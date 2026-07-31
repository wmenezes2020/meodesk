#!/usr/bin/env python3
"""Generate MeuDesk branding assets (app icons and in-app logos).

Source of truth is ``images/meudesk - fondo transparente.png`` -- the only
artwork that ships with a real alpha channel, so no background keying (and no
color fringing) is needed.

Run from the repository root:

    python scripts/generate_brand_assets.py
"""

import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, 'images', 'meudesk - fondo transparente.png')

# Tight bounding boxes measured on the source artwork (alpha > 40).
MARK_BOX = (297, 376, 505, 535)   # 208x159 -- the framed-cursor symbol
LOGO_BOX = (297, 376, 1228, 535)  # 931x159 -- symbol + "meuDesk" wordmark

# White plate used behind the symbol on desktop / legacy launcher icons.
PLATE_COLOR = (255, 255, 255, 255)
PLATE_RADIUS_RATIO = 0.20
# Symbol width as a fraction of the icon side.
MARK_RATIO_PLATE = 0.70
MARK_RATIO_BARE = 0.86
# Android adaptive icons only guarantee the inner 66% of the canvas.
MARK_RATIO_ADAPTIVE = 0.55
# macOS icons keep a transparent margin around the squircle.
MAC_CONTENT_RATIO = 0.805
MAC_RADIUS_RATIO = 0.225

SSAA = 8


def resize_rgba(image, width, height):
    """LANCZOS resize on premultiplied alpha (avoids halos on transparency)."""
    data = np.asarray(image, dtype=np.float32)
    alpha = data[..., 3:4] / 255.0
    premultiplied = np.concatenate([data[..., :3] * alpha, data[..., 3:4]], axis=2)
    resized = np.asarray(
        Image.fromarray(np.round(premultiplied).astype(np.uint8), 'RGBA')
        .resize((width, height), Image.LANCZOS),
        dtype=np.float32,
    )
    alpha = resized[..., 3:4] / 255.0
    rgb = np.divide(resized[..., :3], alpha, out=np.zeros_like(resized[..., :3]),
                    where=alpha > 0)
    out = np.concatenate([np.clip(rgb, 0, 255), resized[..., 3:4]], axis=2)
    return Image.fromarray(np.round(out).astype(np.uint8), 'RGBA')


def fit_width(image, width):
    height = max(1, round(width * image.size[1] / image.size[0]))
    return resize_rgba(image, width, height)


def rounded_mask(size, radius, circle=False):
    big = size * SSAA
    mask = Image.new('L', (big, big), 0)
    draw = ImageDraw.Draw(mask)
    if circle:
        draw.ellipse((0, 0, big - 1, big - 1), fill=255)
    else:
        draw.rounded_rectangle((0, 0, big - 1, big - 1), radius=radius * SSAA, fill=255)
    return mask.resize((size, size), Image.LANCZOS)


def make_plate(size, radius_ratio=PLATE_RADIUS_RATIO, circle=False, content_ratio=1.0):
    """White rounded plate, optionally inset inside a transparent canvas."""
    side = max(1, round(size * content_ratio))
    layer = Image.new('RGBA', (side, side), PLATE_COLOR)
    layer.putalpha(rounded_mask(side, max(1, round(side * radius_ratio)), circle))
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    offset = (size - side) // 2
    canvas.alpha_composite(layer, (offset, offset))
    return canvas


def center(canvas, sprite, y_shift=0):
    x = (canvas.size[0] - sprite.size[0]) // 2
    y = (canvas.size[1] - sprite.size[1]) // 2 + y_shift
    canvas.alpha_composite(sprite, (x, y))
    return canvas


def icon_on_plate(mark, size, circle=False, mark_ratio=MARK_RATIO_PLATE,
                  radius_ratio=PLATE_RADIUS_RATIO, content_ratio=1.0):
    canvas = make_plate(size, radius_ratio, circle, content_ratio)
    return center(canvas, fit_width(mark, max(1, round(size * mark_ratio * content_ratio))))


def bare_icon(mark, size, mark_ratio=MARK_RATIO_BARE):
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    return center(canvas, fit_width(mark, max(1, round(size * mark_ratio))))


def silhouette(mark, size, color, mark_ratio=MARK_RATIO_BARE):
    sprite = fit_width(mark, max(1, round(size * mark_ratio)))
    flat = Image.new('RGBA', sprite.size, color + (0,))
    flat.putalpha(sprite.getchannel('A'))
    canvas = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    return center(canvas, flat)


def lighten(image, factor):
    """Pull colors toward white for dark backgrounds; alpha is preserved."""
    data = np.asarray(image, dtype=np.float32)
    rgb = 255.0 - (255.0 - data[..., :3]) * factor
    out = np.concatenate([np.clip(rgb, 0, 255), data[..., 3:4]], axis=2)
    return Image.fromarray(np.round(out).astype(np.uint8), 'RGBA')


def write_png(image, *parts):
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path, format='PNG', optimize=True)
    print('wrote', os.path.relpath(path, ROOT))


def write_ico(frames, *parts):
    """Write an .ico where every entry is rendered at its native size."""
    path = os.path.join(ROOT, *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    frames = sorted(frames, key=lambda im: im.size[0], reverse=True)
    frames[0].save(
        path,
        format='ICO',
        sizes=[im.size for im in frames],
        append_images=frames[1:],
    )
    print('wrote', os.path.relpath(path, ROOT))


ANDROID_DPI = {
    'mdpi': 1,
    'hdpi': 1.5,
    'xhdpi': 2,
    'xxhdpi': 3,
    'xxxhdpi': 4,
}


def main():
    source = Image.open(SOURCE).convert('RGBA')
    mark = source.crop(MARK_BOX)
    logo = source.crop(LOGO_BOX)

    # ---------------------------------------------------------------- logos
    logo_dark = lighten(logo, 0.80)
    write_png(logo, 'flutter', 'assets', 'logo.png')
    write_png(logo, 'flutter', 'assets', 'logo_light.png')
    write_png(logo_dark, 'flutter', 'assets', 'logo_dark.png')
    write_png(bare_icon(mark, 512), 'flutter', 'assets', 'icon.png')

    # ------------------------------------------------------- shared desktop
    write_png(icon_on_plate(mark, 1024), 'res', 'icon.png')
    write_png(
        icon_on_plate(mark, 1024, radius_ratio=MAC_RADIUS_RATIO,
                      content_ratio=MAC_CONTENT_RATIO),
        'res', 'mac-icon.png',
    )
    for size, name in ((32, '32x32.png'), (64, '64x64.png'),
                       (128, '128x128.png'), (256, '128x128@2x.png')):
        write_png(icon_on_plate(mark, size), 'res', name)

    write_png(silhouette(mark, 128, (0, 0, 0)), 'res', 'mac-tray-dark-x2.png')
    write_png(silhouette(mark, 128, (255, 255, 255)), 'res', 'mac-tray-light-x2.png')

    ico_sizes = (16, 24, 32, 48, 64, 128, 256)
    write_ico([icon_on_plate(mark, s) for s in ico_sizes], 'res', 'icon.ico')
    write_ico(
        [icon_on_plate(mark, s) for s in ico_sizes],
        'flutter', 'windows', 'runner', 'resources', 'app_icon.ico',
    )
    write_ico([bare_icon(mark, s) for s in (16, 20, 24, 32, 48, 64)],
              'res', 'tray-icon.ico')

    # -------------------------------------------------------------- android
    res = os.path.join('flutter', 'android', 'app', 'src', 'main', 'res')
    for dpi, scale in ANDROID_DPI.items():
        folder = f'mipmap-{dpi}'
        launcher = round(48 * scale)
        foreground = round(108 * scale)
        stat = round(24 * scale)
        write_png(icon_on_plate(mark, launcher), res, folder, 'ic_launcher.png')
        write_png(icon_on_plate(mark, launcher, circle=True),
                  res, folder, 'ic_launcher_round.png')
        write_png(bare_icon(mark, foreground, MARK_RATIO_ADAPTIVE),
                  res, folder, 'ic_launcher_foreground.png')
        write_png(silhouette(mark, stat, (255, 255, 255)),
                  res, folder, 'ic_stat_logo.png')


if __name__ == '__main__':
    main()
