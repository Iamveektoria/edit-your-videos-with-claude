"""Drawing primitives for a ONE-OFF hand-drawn background, composed fresh for
each customer's video. This is NOT a picklist of preset scenes — there is no
"purple_shelf" or "bright_loft" to choose from. When a customer asks Claude to
draw a background, Claude writes a short script (using these helpers directly)
that composes a scene matching what that specific video is about, renders it
to a PNG, and only then runs the lighting-match/depth-blur compositor
(background_core.py) on that PNG like it would on any uploaded reference photo.

Honest limits (carried over from the original handoff's own test verdict):
code-drawn scenes read as soft illustrations, not photos. Keep them simple,
warm and uncluttered rather than busy.
"""
import random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops


def canvas(w, h, top, bot):
    """Vertical gradient base, e.g. canvas(1080, 1920, (205,195,222), (150,125,175))."""
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top)[None, None, :] * (1 - t) + np.array(bot)[None, None, :] * t
    return Image.fromarray(np.repeat(a, w, 1).astype('uint8'), 'RGB')


def glow(img, layer, sigma, strength=1.0):
    """Screen-blend a blurred light layer onto img. layer is an RGB Image, same size as img,
    black everywhere except where you've drawn a light shape."""
    g = layer.filter(ImageFilter.GaussianBlur(sigma))
    return ImageChops.screen(img, Image.eval(g, lambda v: int(v * strength)))


def leaf_cluster(img, cx, cy, n, size, col, seed=1, spread=1.0, up=True):
    """Paste a loose cluster of leaf-shaped blobs onto img (in place), for a plant."""
    r = random.Random(seed)
    for _ in range(n):
        a = r.uniform(-math.pi, 0) if up else r.uniform(0, math.pi * 2)
        dist = r.uniform(0.2, 1.0) * size * spread
        x, y = cx + math.cos(a) * dist, cy + math.sin(a) * dist
        w, h = r.uniform(.35, .6) * size, r.uniform(.18, .3) * size
        sh = r.uniform(-25, 25)
        c = tuple(int(max(0, min(255, v + sh))) for v in col)
        im = Image.new('RGBA', (int(w * 2.2), int(w * 2.2)), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse((w * .1, w - h, w * 2.1, w + h), fill=c + (255,))
        im = im.rotate(-math.degrees(a) + r.uniform(-30, 30), expand=True)
        img.paste(im, (int(x - im.width / 2), int(y - im.height / 2)), im)


def bokeh_dots(w, h, n, colours, seed=7, y_range=None):
    """A soft-focus dots layer (podcast/city-light look). Screen-blend this onto
    the base with ImageChops.screen(base, bokeh_dots(...).filter(GaussianBlur(2)))."""
    y_range = y_range or (0, h)
    img = Image.new('RGB', (w, h), 0)
    d = ImageDraw.Draw(img)
    r = random.Random(seed)
    for _ in range(n):
        x, y, rad = r.randint(0, w), r.randint(*y_range), r.randint(int(h * 0.015), int(h * 0.05))
        c = r.choice(colours)
        c = tuple(int(v * r.uniform(.35, .7)) for v in c)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), fill=c)
        d.ellipse((x - rad, y - rad, x + rad, y + rad), outline=tuple(min(255, int(v * 1.4)) for v in c), width=max(1, rad // 6))
    return img


def shelf_grid(w, h, box, rows, cols, line_colour, line_width=5):
    """Draw an empty shelf/cubby grid inside `box`=(x0,y0,x1,y1). Fill cells afterward if you like."""
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    for r in range(rows + 1):
        d.line((x0, y0 + r * ch, x1, y0 + r * ch), fill=line_colour, width=line_width)
    for c in range(cols + 1):
        d.line((x0 + c * cw, y0, x0 + c * cw, y1), fill=line_colour, width=line_width)
    return img


def window_light(w, h, polygon, colour=(255, 245, 220), sigma=60, strength=0.8):
    """A soft directional light wash, e.g. from a window just out of frame."""
    layer = Image.new('RGB', (w, h), 0)
    ImageDraw.Draw(layer).polygon(polygon, fill=colour)
    return layer, sigma, strength  # pass to glow(img, *this)


def cover_fit(pil_img, out_w, out_h):
    """Resize+crop a PIL image to exactly out_w x out_h, cover-style, then return
    it as an RGB float32 numpy array in 0..1 (what background_core.py expects)."""
    src_w, src_h = pil_img.size
    scale = max(out_w / src_w, out_h / src_h)
    new_w, new_h = int(src_w * scale + 0.5), int(src_h * scale + 0.5)
    img = pil_img.resize((new_w, new_h), Image.LANCZOS)
    left, top = (new_w - out_w) // 2, (new_h - out_h) // 2
    img = img.crop((left, top, left + out_w, top + out_h))
    return np.array(img.convert('RGB')).astype(np.float32) / 255.0
