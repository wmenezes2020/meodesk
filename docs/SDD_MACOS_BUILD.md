# SDD — macOS custom client workflow

## Problem

Only Android and Windows had a custom build workflow. macOS had no pipeline,
and the pieces that make a build "branded" on the other two platforms had no
macOS equivalent: the bundle still declared `PRODUCT_NAME = RustDesk`, the
`.app` icon was upstream artwork, and the deep-link scheme was `rustdesk://`
while the Rust core emits `meudesk://`.

## Solution

### Branding parity

macOS carries its identity in different files than Windows, so three gaps had
to be closed before a build could be branded:

| Concern | Windows | macOS |
| --- | --- | --- |
| Product name | `Runner.rc` | `Configs/AppInfo.xcconfig` -> `PRODUCT_NAME` |
| Icon | `resources/app_icon.ico` | `Runner/AppIcon.icns` |
| Deep-link scheme | registry, from `APP_NAME` | `Info.plist` -> `CFBundleURLSchemes` |

- `scripts/generate_brand_assets.py` now also emits
  `flutter/macos/Runner/AppIcon.icns` from the same 1024 px macOS plate that
  feeds `res/mac-icon.png`, so the squircle and margins match. Pillow writes
  every standard entry from 16 px up to 512@2x.
- `scripts/apply_customizations.py` rewrites `PRODUCT_NAME`,
  `PRODUCT_BUNDLE_IDENTIFIER` and the `Info.plist` URL scheme and URL name.
  `PRODUCT_COPYRIGHT` is left alone, same reasoning as `LegalCopyright` on
  Windows.
- `PRODUCT_NAME` also decides the `.app` directory name, and `build.py` copied
  the `service` binary into a hardcoded `RustDesk.app`. It now reads
  `PRODUCT_NAME` back from the xcconfig, so renaming the product cannot break
  the build.

### Workflow

`.github/workflows/build-custom-cliente-macos.yml`, same `push` trigger on
`build-custom` as the other two. Differences from the Windows workflow, all
forced by the platform:

- **Rust 1.81**, not 1.75 — `cidre`, pulled in by the macOS build, requires it.
- **Two architectures** via matrix, `fail-fast: false`. Unlike Windows and
  Android, macOS has two live architectures; `macos-14` builds `aarch64` with
  `--screencapturekit`, `macos-15-intel` builds `x86_64`. A failure on one arch
  still ships the other.
- **NASM pinned to 2.16.03** from the official release. `brew install nasm`
  now installs 3.x, whose CLI is incompatible with what `aom` expects.
- **Minimum macOS version** is patched per arch before building (12.3 for
  Apple Silicon, 10.14 for Intel) across `build.py`, the Podfile, `Cargo.toml`
  and the Xcode project.
- **No custom Flutter engine.** Only the Windows build replaces it; macOS uses
  the stock engine, matching upstream.
- The dead `RENDEZVOUS_SERVER` / `RS_PUB_KEY` env export from the Windows
  workflow was not carried over. Those values reach the binary through
  `apply_customizations.py` patching `config.rs`, not through the environment.

## Signing

The artifact is an **unsigned** `.dmg`. There are no Apple Developer secrets in
this repository, so notarization is not possible. The build applies an ad-hoc
signature (`codesign --sign -`), which is required for arm64 bundles to launch
at all but is not a Developer ID signature: Gatekeeper will still warn, and
users must right-click > Open on first launch.

To ship properly signed builds, add `MACOS_P12_BASE64`, `MACOS_P12_PASSWORD`
and `MACOS_NOTARIZE_JSON` as repository secrets and mirror the codesign and
notarize steps from `.github/workflows/flutter-build.yml`.

## Validation

- All three custom workflows parse as YAML and expose one job each.
- `scripts/apply_customizations.py` ran against the real tree; the resulting
  `AppInfo.xcconfig` (`PRODUCT_NAME = MeuDesk`) and `Info.plist` (scheme
  `meudesk`) were inspected, then reverted along with the other build-time
  outputs and the `hbb_common` submodule.
- `build.py`'s `get_macos_product_name()` was executed against the customized
  xcconfig and returned `MeuDesk`.
- `AppIcon.icns` was re-opened and its size table checked.
- The build itself is verified by the workflow; no macOS machine is available
  locally.
