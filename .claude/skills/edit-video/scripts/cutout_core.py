#!/usr/bin/env python3
"""MediaPipe selfie-segmenter cutout core. Apache-2.0 model, no GPL, no third-party weights.

Usage: python3 cutout_core.py <input_video> <output_dir> [--model PATH] [max_frames]

Writes:
  <output_dir>/cutout.webm                     transparent VP9 webm (alpha = person, colour = original frame)
  <output_dir>/preview_transparency_check.mp4   cutout composited over a grey checkerboard, labelled as a PREVIEW
  <output_dir>/alpha_report.txt                 verification numbers (does NOT assume alpha worked)
"""
import sys, os, subprocess, time
import numpy as np
import cv2
from matte import MatteStream, MODEL_DEFAULT


def make_checkerboard(w, h, tile=40):
    board = np.zeros((h, w, 3), dtype=np.uint8)
    light, dark = 200, 140
    for y in range(0, h, tile):
        for x in range(0, w, tile):
            c = light if ((x // tile) + (y // tile)) % 2 == 0 else dark
            board[y:y + tile, x:x + tile] = c
    return board


def run(input_path, out_dir, model_path=MODEL_DEFAULT, max_frames=None):
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise SystemExit(f"could not open {input_path}")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    n_total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"input {W}x{H} @ {fps:.2f}fps, {n_total} frames", flush=True)

    stream = MatteStream(model_path)
    checker = make_checkerboard(W, H)

    rgba_path = os.path.join(out_dir, "_rgba_raw.rgba")
    fout = open(rgba_path, "wb")

    flicker_deltas = []
    alpha_mins, alpha_maxs, transparent_fracs = [], [], []
    prev_raw = None

    n = 0
    t0 = time.time()
    while True:
        ok, frame_bgr = cap.read()
        if not ok:
            break
        if max_frames is not None and n >= max_frames:
            break
        alpha_u8, raw_mask, rgb = stream.next(frame_bgr)

        if prev_raw is not None:
            flicker_deltas.append(float(np.mean(np.abs(raw_mask - prev_raw))))
        prev_raw = raw_mask

        alpha_mins.append(int(alpha_u8.min()))
        alpha_maxs.append(int(alpha_u8.max()))
        transparent_fracs.append(float(np.mean(alpha_u8 < 10)))

        rgba = np.dstack([rgb, alpha_u8])  # colour = ORIGINAL frame (MediaPipe gives no fgr estimate)
        fout.write(rgba.tobytes())

        n += 1
        if n % 30 == 0:
            print(n, f"{time.time()-t0:.0f}s", flush=True)

    fout.close()
    cap.release()
    stream.close()

    print("frames", n, "seconds", round(time.time() - t0, 1))

    cutout_path = os.path.join(out_dir, "cutout.webm")
    has_audio = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
         "-of", "csv=p=0", input_path], capture_output=True, text=True
    ).stdout.strip() != ""

    cmd = ["ffmpeg", "-v", "error", "-y",
           "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", rgba_path]
    if has_audio:
        cmd += ["-i", input_path]
    cmd += ["-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", "24", "-auto-alt-ref", "0"]
    if has_audio:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:a", "libopus", "-shortest"]
    cmd += [cutout_path]
    subprocess.run(cmd, check=True)
    os.remove(rgba_path)

    checker_path = os.path.join(out_dir, "_checkerboard.png")
    cv2.imwrite(checker_path, checker)
    preview_path = os.path.join(out_dir, "preview_transparency_check.mp4")
    subprocess.run([
        "ffmpeg", "-v", "error", "-y",
        "-loop", "1", "-i", checker_path,
        "-c:v", "libvpx-vp9", "-i", cutout_path,  # must force libvpx-vp9 decode or alpha is silently dropped
        "-filter_complex", "[0:v][1:v]overlay=shortest=1[v]",
        "-map", "[v]"] + (["-map", "1:a"] if has_audio else []) + [
        "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        preview_path
    ], check=True)
    os.remove(checker_path)

    report_path = os.path.join(out_dir, "alpha_report.txt")
    with open(report_path, "w") as rf:
        rf.write(f"frames checked: {n}\n")
        rf.write(f"alpha min (overall): {min(alpha_mins)}\n")
        rf.write(f"alpha max (overall): {max(alpha_maxs)}\n")
        rf.write(f"mean transparent-pixel fraction (<10): {np.mean(transparent_fracs):.3f}\n")
        if flicker_deltas:
            rf.write(f"raw mask-to-mask mean abs delta (flicker metric): {np.mean(flicker_deltas):.4f}\n")
    print(open(report_path).read())

    return {
        "cutout": cutout_path,
        "preview": preview_path,
        "alpha_min": min(alpha_mins),
        "alpha_max": max(alpha_maxs),
        "transparent_frac": float(np.mean(transparent_fracs)),
        "flicker_metric": float(np.mean(flicker_deltas)) if flicker_deltas else None,
    }


if __name__ == "__main__":
    inp = sys.argv[1]
    out = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else MODEL_DEFAULT
    max_frames = int(sys.argv[4]) if len(sys.argv) > 4 else None
    run(inp, out, model, max_frames)
