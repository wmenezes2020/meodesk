# SDD — MeuDesk white-label (name, upstream branding, account feature)

## Problem

Three gaps in the branded client:

1. The product was named `MeoDesk`, which does not match the `meuDesk` artwork.
2. The upstream `RustDesk` name still surfaced in the UI, in Android system
   screens, in Windows file metadata and in the shipped executable name.
3. The account/login feature was visible on both platforms even though the
   organization does not operate that service, so every entry point led to a
   dead end.

## Root cause

`scripts/apply_customizations.py` only rewrote the product name in four places.
Everything else either hardcoded `RustDesk` or was never wired to the app name.

## Solution

### 1. MeoDesk -> MeuDesk

`config.json` carries the single source of truth (`app_name`). The rename also
covers the script default, the two workflow names, the artifact names and the
documentation.

### 2. Removing the upstream name

The key finding is that upstream already substitutes at runtime: `src/lang.rs`
replaces `RustDesk` with `APP_NAME` in **every** translated string when
`APP_NAME != "RustDesk"`. All 51 language files were therefore already covered
and were left untouched. Two hardcoded exemptions were removed so nothing leaks:
`powered_by_me` and `upgrade_rustdesk_server_pro*`.

What was not going through that path:

| Surface | Fix |
| --- | --- |
| "Powered by RustDesk" credit + its external link | `hide-powered-by-me=Y` in `BUILTIN_SETTINGS` (upstream option, removes the whole widget) |
| Desktop tab-bar title | `tabbar_widget.dart` reads `bind.mainGetAppNameSync()` instead of a literal |
| TOTP issuer in the user's authenticator app | `auth_2fa.rs` uses `crate::get_app_name()` |
| Windows `MessageBox` caption | `platform/windows.rs` uses `crate::get_app_name()` |
| Android notification title, channel name and description | `MainService.kt` reads `R.string.app_name` |
| Android boot toast | `BootReceiver.kt` reads `R.string.app_name` |
| Accessibility service label and description | script rewrites `AndroidManifest.xml` and `strings.xml` |
| Deep-link scheme | script rewrites `android:scheme`, which must match Rust's `get_uri_prefix()` (lowercased app name) — previously `rustdesk://` while the core emitted `meudesk://` |
| Windows executable name and `OriginalFilename` | script rewrites `BINARY_NAME` in `flutter/windows/CMakeLists.txt` and the matching `Runner.rc` field |

Source files use dynamic lookups wherever the app name is available at runtime;
the script is used only where the value must be baked into build metadata.

### 3. Hiding the account feature

`disable-account` is an upstream `HARD_SETTINGS` flag already honored across the
codebase. `apply_customizations.py` now injects it, which removes in one step:

- the desktop Settings > Account tab
- the Android Settings > Account section
- the Address Book and Group peer tabs
- the toolbar account entry and the connection-note option that requires login

`HARD_SETTINGS` is only inserted into (never replaced) when a custom client
config is loaded, so the compiled-in value survives.

## Non-goals

- Renaming crates, the Rust `librustdesk.dll`, Kotlin packages, the Android
  `applicationId`, code identifiers or tests. These are internal and renaming
  them risks the build without changing anything a user sees.
- Rewriting `https://rustdesk.com` and `github.com/rustdesk` URLs. They must
  keep resolving; the visible link text is already translated.
- Touching `CompanyName` / `LegalCopyright` in `Runner.rc`. Those name the
  upstream copyright holder and the project is AGPL-3.0.
- Upstream community documents under `docs/` and the README translations, which
  are not shipped to end users.

## Validation

- `python scripts/apply_customizations.py` ran against the real tree; the
  resulting `config.rs`, `AndroidManifest.xml`, `strings.xml`, `Runner.rc` and
  `CMakeLists.txt` were inspected, then reverted (they are build-time output and
  must stay upstream-clean in the repository).
- `replace_required` now guards `BINARY_NAME`, `OVERWRITE_SETTINGS`,
  `BUILTIN_SETTINGS` and `HARD_SETTINGS`, so a silent no-op fails the build.
- The Windows workflow runs `build.py --portable --skip-portable-pack`, which
  returns before the packaging step that still references the upstream file
  name, so renaming the binary is safe for this pipeline.
- Rust and Flutter compilation is verified by the two custom workflows; no
  toolchain is available locally.
