"""Shared MediaPipe selfie-segmentation matte pipeline (Apache-2.0 model).

Used by cutout_core.py, blur_core.py and background_core.py so the flicker-fix /
edge-cleanup recipe lives in exactly one place.
"""
import os
import urllib.request
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

MODEL_DEFAULT = os.path.join(os.path.dirname(__file__), "selfie_segmenter.tflite")
MODEL_URL = "https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/latest/selfie_segmenter.tflite"


def ensure_model(model_path=MODEL_DEFAULT):
    """Download the official Google model file on first use (~250KB, Apache-2.0).
    Never committed to git, never fetched from any third-party mirror."""
    if os.path.exists(model_path) and os.path.getsize(model_path) > 0:
        return model_path
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    tmp = model_path + ".part"
    urllib.request.urlretrieve(MODEL_URL, tmp)
    os.replace(tmp, model_path)
    return model_path


class MatteStream:
    """Call .next(frame_bgr) for each frame in order; returns (alpha_u8, raw_mask)."""

    def __init__(self, model_path=MODEL_DEFAULT):
        model_path = ensure_model(model_path)
        base_opts = mp_python.BaseOptions(model_asset_path=model_path)
        options = mp_vision.ImageSegmenterOptions(
            base_options=base_opts,
            running_mode=mp_vision.RunningMode.VIDEO,
            output_confidence_masks=True,
        )
        self.segmenter = mp_vision.ImageSegmenter.create_from_options(options)
        self.mask_hist = []
        self.prev_final = None
        self.frame_idx = 0
        self.kernel5 = np.ones((5, 5), np.uint8)

    def next(self, frame_bgr):
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        timestamp_ms = int(self.frame_idx * 33.3)
        result = self.segmenter.segment_for_video(mp_image, timestamp_ms)
        raw_mask = result.confidence_masks[0].numpy_view().squeeze().astype(np.float32)

        self.mask_hist.append(raw_mask)
        if len(self.mask_hist) > 3:
            self.mask_hist.pop(0)
        med = np.median(np.stack(self.mask_hist, axis=0), axis=0) if len(self.mask_hist) > 1 else raw_mask
        m = med if self.prev_final is None else (0.6 * med + 0.4 * self.prev_final)
        self.prev_final = m

        eroded = cv2.erode(m, self.kernel5)
        blurred = cv2.GaussianBlur(eroded, (0, 0), sigmaX=1.6)
        alpha_f = np.clip((blurred - 0.15) / 0.7, 0, 1)
        alpha_u8 = (alpha_f * 255).astype(np.uint8)

        self.frame_idx += 1
        return alpha_u8, raw_mask, rgb

    def close(self):
        self.segmenter.close()


def disc_kernel(radius):
    """Bokeh-style disc kernel for highlight-aware background blur."""
    size = radius * 2 + 1
    y, x = np.ogrid[-radius:radius + 1, -radius:radius + 1]
    mask = (x * x + y * y) <= radius * radius
    k = mask.astype(np.float32)
    k /= k.sum()
    return k


def lens_blur(bgr_float, radius_at_full_res, downscale=0.5):
    """Disc-kernel blur with highlight boost, matching the original handoff's
    'lens'/bokeh look. bgr_float is float32 0..1, full resolution."""
    h, w = bgr_float.shape[:2]
    small = cv2.resize(bgr_float, (max(1, int(w * downscale)), max(1, int(h * downscale))), interpolation=cv2.INTER_AREA)
    # highlight boost only kicks in on genuine bright spots (lamps, window glare);
    # a plain lit wall sits around 0.8-0.9 and must not get blown out to white.
    boosted = small + 1.0 * np.clip(small - 0.92, 0, None)
    r = max(1, int(radius_at_full_res * downscale))
    k = disc_kernel(r)
    blurred = cv2.filter2D(boosted, -1, k, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(blurred, (w, h), interpolation=cv2.INTER_LINEAR)


BLUR_RADIUS = {"light": 8, "medium": 15, "strong": 26}


def stray_fraction(alpha_u8, visible_thresh=80):
    """Fraction of frame pixels that are part-visible (alpha>thresh) but NOT
    in the single largest connected blob - i.e. isolated patches of the
    background bleeding through away from the person, not a clean edge."""
    binary = (alpha_u8 > visible_thresh).astype(np.uint8)
    n_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if n_labels <= 1:
        return 0.0
    areas = stats[1:, cv2.CC_STAT_AREA]
    largest = areas.max()
    total_visible = areas.sum()
    strays = total_visible - largest
    return float(strays) / float(alpha_u8.size)


def assess_quality(alpha_mins, alpha_maxs, transparent_fracs, flicker_deltas, stray_fracs=None):
    """Turn a short run of per-frame cutout numbers into a plain verdict.

    Thresholds are heuristics tuned on real test clips (plain wall, busy
    bookshelf, bright window, dark-on-dark), not a guarantee - always show
    the actual preview frame too, don't rely on numbers alone."""
    reasons = []
    mean_transparent = float(np.mean(transparent_fracs)) if transparent_fracs else 0.0
    mean_flicker = float(np.mean(flicker_deltas)) if flicker_deltas else 0.0
    min_a = min(alpha_mins) if alpha_mins else 0
    max_a = max(alpha_maxs) if alpha_maxs else 0
    mean_stray = float(np.mean(stray_fracs)) if stray_fracs else 0.0

    if max_a < 200:
        reasons.append("the person never reaches full opacity - likely a half-cut edge or very soft outline")
    if min_a > 60:
        reasons.append("the background never goes fully transparent - likely bleed-through from a busy background")
    if mean_flicker > 0.06:
        reasons.append("the outline is moving a lot between frames - likely a rough, flickery edge")
    if mean_transparent < 0.15:
        reasons.append("almost nothing was cut away - the mask may have failed or the person fills the whole frame")
    if mean_stray > 0.004:
        reasons.append("isolated patches of the background are showing through as semi-visible blobs away from the person")

    return {"ok": len(reasons) == 0, "reasons": reasons}
