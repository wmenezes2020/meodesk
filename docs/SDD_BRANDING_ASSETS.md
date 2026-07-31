# SDD — MeuDesk branding assets (icons and logos)

## Problem

Custom Android and Windows builds already carried the MeuDesk product name, but
every visual asset was still upstream RustDesk artwork: launcher icons, tray
icons, the Windows `.ico` files and the desktop/mobile in-app logo area. The
`_Logo` widget in `flutter/lib/common.dart` looks for `assets/logo*.png`, and
none of those files existed, so the home page and the mobile settings page
rendered an empty logo slot.

## Root cause

Branding was applied only to text metadata by `scripts/apply_customizations.py`.
No image pipeline existed, and the artwork delivered in `images/` had never been
converted into the sizes each platform requires.

## Goal

Every icon and logo surface of the Android and Windows clients shows the
MeuDesk mark, generated deterministically from the delivered artwork.

## Solution

`scripts/generate_brand_assets.py` derives every asset from
`images/meudesk - fondo transparente.png`, the only source with a real alpha
channel (keying the white/black variants would have produced color fringing on
the antialiased edges).

Two crops drive everything:

- symbol: `(297, 376, 505, 535)` — the framed-cursor mark
- full logo: `(297, 376, 1228, 535)` — symbol plus the `meuDesk` wordmark

Rendering rules:

- Resizes run on premultiplied alpha, so transparent edges do not pick up halos.
- Plates (rounded square, circle, macOS squircle) are drawn at 8x and
  downsampled, so small sizes stay crisp.
- Every `.ico` entry is rendered at its native size instead of being downscaled
  from a single master.
- The dark-theme logo is the source artwork pulled 20% toward white, which keeps
  `#006EFF` legible on dark surfaces while preserving the alpha channel.

Generated surfaces:

| Target | Files |
| --- | --- |
| In-app logo | `flutter/assets/logo.png`, `logo_light.png`, `logo_dark.png` |
| In-app icon | `flutter/assets/icon.png` |
| Android launcher | `mipmap-{m,h,xh,xxh,xxxh}dpi/ic_launcher.png`, `ic_launcher_round.png` |
| Android adaptive | `mipmap-*/ic_launcher_foreground.png` (mark inside the 66% safe zone) |
| Android notification | `mipmap-*/ic_stat_logo.png` (white silhouette) |
| Windows runner | `flutter/windows/runner/resources/app_icon.ico` |
| Windows executable / MSI | `res/icon.ico` (used by `build.rs` and `res/msi/preprocess.py`) |
| Desktop tray | `res/tray-icon.ico`, `res/mac-tray-{dark,light}-x2.png` |
| Shared desktop | `res/icon.png`, `res/mac-icon.png`, `res/{32x32,64x64,128x128,128x128@2x}.png` |

`.gitignore` ignores `*png` repository-wide, so the four new `flutter/assets`
files are explicitly re-included.

## Non-goals

- Vectorizing the mark into SVG (`res/logo.svg`, `res/scalable.svg`,
  `flutter/assets/icon.svg` still hold upstream artwork).
- Changing any Dart or Rust code: `_Logo` and `loadIcon` already resolve the
  asset names that are now provided.
- Rebranding README banners or Linux packaging metadata.

## Validation

- `python scripts/generate_brand_assets.py` regenerates all 35 assets.
- Every written file was re-opened and inspected: sizes, modes and the
  per-size `.ico` frames (16/24/32/48/64/128/256 for the app icon,
  16/20/24/32/48/64 for the tray icon).
- Visual review at 16 px confirmed the mark stays readable at the smallest
  Windows tray and Android notification sizes.
- Android and Windows artifacts are produced by
  `.github/workflows/build-custom-cliente-*.yml`, which consume these files
  directly; no build step regenerates them.
