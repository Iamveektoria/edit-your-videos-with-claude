#!/usr/bin/env python3
"""/edit-video background: compositor only. Talking-head only, no AI-generated
backgrounds (no Stable Diffusion / diffusers / LCM).

Takes a single still image as the new background -- it does not care whether
that image is the customer's own uploaded reference photo, or a one-off scene
Claude just drew with bg_toolkit.py for this specific video. There is no
preset library here; whatever background is wanted is decided in conversation
with the customer BEFORE this script ever runs, and the image already exists
on disk by the time this is called.

Adapted from the original handoff's Appendix C lighting/contrast match. Since
MediaPipe gives only an alpha mask (no RVM-style foreground colour estimate,
'fgr'), the edge light-wrap below uses the alpha from matte.py and the
ORIGINAL frame as the colour source. The erode step already baked into that
alpha is what removes the old-wall halo, so the light-wrap band is re-tuned
narrower here rather than reusing the old numbers blindly.

Usage:
  python3 background_core.py <input_video> <out_dir> <background_image.png> <blur> [brand R,G,B] [max_frames]
  blur in {none, light, medium, strong}
"""
import sys, os, subprocess, time
import numpy as np
import cv2
from PIL import Image
from matte import MatteStream, MODEL_DEFAULT, lens_blur

BLUR_RADIUS_BG = {"none": 0, "light": 6, "medium": 12, "strong": 22}


def load_background_image(path, out_w, out_h):
    img = Image.open(path).convert("RGB")
    src_w, src_h = img.size
    scale = max(out_w / src_w, out_h / src_h)
    new_w, new_h = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - out_w) // 2, (new_h - out_h) // 2
    img = img.crop((left, top, left + out_w, top + out_h))
    return np.array(img).astype(np.float32) / 255.0


def luminance(bgr_float):
    # bgr_float: ...,3 (B,G,R) 0..1
    b, g, r = bgr_float[..., 0], bgr_float[..., 1], bgr_float[..., 2]
    return 0.114 * b + 0.587 * g + 0.299 * r


def measure_subject_stats(frame_bgr_f, alpha_f):
    """Measure once (first good frame) and reuse for every frame: no flicker."""
    sel = alpha_f > 0.95
    if sel.sum() < 500:
        sel = alpha_f > 0.7
    lum = luminance(frame_bgr_f)
    fg_vals = lum[sel]
    fg_mean = float(fg_vals.mean()) if fg_vals.size else 0.5
    fg_std = float(fg_vals.std()) if fg_vals.size else 0.15

    mx = frame_bgr_f.max(axis=2)
    mn = frame_bgr_f.min(axis=2)
    sat = (mx - mn) / (mx + 1e-3)
    bright = sel & (lum > np.quantile(lum[sel], 0.6) if fg_vals.size else False) & (sat < 0.25)
    if bright.sum() > 50:
        light_col = frame_bgr_f[bright].mean(axis=0)
    else:
        light_col = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    light_col = light_col / (light_col.mean() + 1e-6)

    h, w = alpha_f.shape
    mid = w // 2
    left_sel = sel[:, :mid]
    right_sel = sel[:, mid:]
    Lm = float(lum[:, :mid][left_sel].mean()) if left_sel.sum() else 0.5
    Rm = float(lum[:, mid:][right_sel].mean()) if right_sel.sum() else 0.5
    side = 1 if Rm > Lm else -1  # +1 = lit from the right

    return {"fg_mean": fg_mean, "fg_std": fg_std, "light_col": light_col, "side": side}


def match_background(bg_bgr_f, stats, brand_bgr=None):
    """Tonal match + colour temperature + light direction + optional brand glow.

    The original handoff's formula was tuned on a still image with one subject;
    on real backgrounds with their own internal contrast (LED cavities, dark
    pots, plants) a full-strength contrast rescale plus a hard target mean
    clipped dark detail straight to black. Clamp the contrast ratio and only
    partly pull the background toward the subject's own mean so dark subjects
    don't crush an otherwise fine background.
    """
    b = bg_bgr_f.copy()
    lum = luminance(b)
    mu, sd = float(lum.mean()), float(lum.std() + 1e-6)
    tgt_mu = 0.5 * mu + 0.5 * (stats["fg_mean"] * 0.88)
    tgt_sd = max(stats["fg_std"] * 0.9, 0.05)
    ratio = np.clip(tgt_sd / sd, 0.7, 1.3)
    b = ((b - mu) * ratio * 0.4 + (b - mu) * 0.6 + tgt_mu)
    b = np.clip(b, 0, 1)

    b = np.clip(b * (1 + 0.6 * (stats["light_col"] - 1.0)), 0, 1)

    h, w = b.shape[:2]
    xs = np.linspace(0, 1, w).reshape(1, w, 1)
    ramp = xs if stats["side"] > 0 else (1 - xs)
    b = np.clip(b * (0.86 + 0.28 * ramp), 0, 1)

    if brand_bgr is not None:
        far = (1 - xs) if stats["side"] > 0 else xs
        yy = np.linspace(0, 1, h).reshape(h, 1, 1)
        glow = np.exp(-(far ** 2) / 0.12 - ((yy - 0.35) ** 2) / 0.35)
        c = np.array(brand_bgr, dtype=np.float32).reshape(1, 1, 3) / 255.0
        b = np.clip(b + c * 0.20 * glow, 0, 1)

    return b


def composite_frame(frame_bgr_f, alpha_f, matched_bg, blur_radius, rng):
    bg_blurred = lens_blur(matched_bg, blur_radius) if blur_radius > 0 else matched_bg

    a3 = alpha_f[..., None]
    kernel7 = np.ones((7, 7), np.uint8)
    eroded = cv2.erode(alpha_f, kernel7)
    eroded_blur = cv2.GaussianBlur(eroded, (0, 0), sigmaX=3)
    band = np.clip(alpha_f - eroded_blur, 0, 1)[..., None]  # thin band just inside the outline
    wrap = 0.35 * band * bg_blurred  # colour source = ORIGINAL frame's own blurred background estimate...
    # actually wrap should pick up blurred-background colour, which bg_blurred already is.
    person = frame_bgr_f * (1 - 0.35 * band) + wrap

    grain = rng.normal(0, 0.012, size=bg_blurred.shape).astype(np.float32)
    bg_final = np.clip(bg_blurred + grain, 0, 1)

    comp = person * a3 + bg_final * (1 - a3)
    return np.clip(comp, 0, 1)


def run(input_path, out_dir, bg_image_path, blur_strength="medium", brand_bgr=None, model_path=MODEL_DEFAULT, max_frames=None):
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise SystemExit(f"could not open {input_path}")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

    bg_rgb = load_background_image(bg_image_path, W, H)
    bg_bgr = bg_rgb[..., ::-1].copy()

    stream = MatteStream(model_path)
    blur_radius = BLUR_RADIUS_BG[blur_strength]
    rng = np.random.default_rng(42)

    stats = None
    raw_path = os.path.join(out_dir, "_raw.bgr")
    fout = open(raw_path, "wb")

    n = 0
    t0 = time.time()
    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        if max_frames is not None and n >= max_frames:
            break
        alpha_u8, _, rgb = stream.next(frame_bgr)
        alpha_f = alpha_u8.astype(np.float32) / 255.0
        frame_f = frame_bgr.astype(np.float32) / 255.0

        if stats is None and alpha_f.max() > 0.9:
            stats = measure_subject_stats(frame_f, alpha_f)
        if stats is None:
            stats = {"fg_mean": 0.5, "fg_std": 0.15, "light_col": np.array([1., 1., 1.]), "side": 1}

        matched_bg = match_background(bg_bgr, stats, brand_bgr)
        comp = composite_frame(frame_f, alpha_f, matched_bg, blur_radius, rng)
        comp_u8 = (comp * 255).astype(np.uint8)
        fout.write(comp_u8.tobytes())

        n += 1
        if n % 30 == 0:
            print(n, f"{time.time()-t0:.0f}s", flush=True)

    fout.close()
    cap.release()
    stream.close()
    print("frames", n, "seconds", round(time.time() - t0, 1))

    has_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", input_path], capture_output=True, text=True
    ).stdout.strip() != ""

    out_path = os.path.join(out_dir, "background.mp4")
    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", str(fps), "-i", raw_path]
    if has_audio:
        cmd += ["-i", input_path]
    cmd += ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p"]
    if has_audio:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += [out_path]
    subprocess.run(cmd, check=True)
    os.remove(raw_path)
    return out_path


if __name__ == "__main__":
    inp, out, bg_image_path, blur = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    brand = None
    max_frames = None
    rest = sys.argv[5:]
    for a in rest:
        if "," in a:
            brand = tuple(int(x) for x in a.split(","))[::-1]  # input as R,G,B -> store B,G,R
        else:
            max_frames = int(a)
    run(inp, out, bg_image_path, blur, brand, max_frames=max_frames)
