#!/usr/bin/env python3
"""/edit-video blur: same matte as cutout, disc-kernel bokeh blur on the real
background, sharp person composited back on top. No style, no background swap.

Usage: python3 blur_core.py <input_video> <output_dir> <light|medium|strong>
"""
import sys, os, subprocess, time
import numpy as np
import cv2
from matte import MatteStream, MODEL_DEFAULT, lens_blur, BLUR_RADIUS


def run(input_path, out_dir, strength="medium", model_path=MODEL_DEFAULT, max_frames=None):
    assert strength in BLUR_RADIUS, f"strength must be one of {list(BLUR_RADIUS)}"
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise SystemExit(f"could not open {input_path}")
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    radius = BLUR_RADIUS[strength]

    stream = MatteStream(model_path)
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
        alpha_f = (alpha_u8.astype(np.float32) / 255.0)[..., None]

        frame_f = frame_bgr.astype(np.float32) / 255.0
        bg_blurred = lens_blur(frame_f, radius)
        comp = frame_f * alpha_f + bg_blurred * (1 - alpha_f)
        comp_u8 = np.clip(comp * 255, 0, 255).astype(np.uint8)
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

    out_path = os.path.join(out_dir, "blur.mp4")
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
    inp, out, strength = sys.argv[1], sys.argv[2], sys.argv[3]
    max_frames = int(sys.argv[4]) if len(sys.argv) > 4 else None
    run(inp, out, strength, max_frames=max_frames)
