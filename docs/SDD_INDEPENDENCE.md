# SDD — Independence from the upstream project

## Problem

The project should stand on its own. Three kinds of coupling existed: build
metadata that still named the upstream author, internal artifact names
(`rustdesk` crate, `librustdesk` library, `rustdesk.exe`), and — the deepest
one — a build that cannot run at all without the upstream GitHub org.

## What was found

The build depends on upstream infrastructure in three structural places:

1. `libs/hbb_common` is a submodule of `github.com/rustdesk/hbb_common`.
2. 26 distinct `github.com/rustdesk-org/*` git dependencies across
   `Cargo.toml`, `libs/enigo`, `libs/scrap` and `libs/hbb_common`.
3. The Windows workflow downloads a custom Flutter engine from
   `github.com/rustdesk/engine/releases`.

None of these are fixable by editing strings; they require mirroring the
repositories. That work is tracked separately and is not part of this change.

## Legal boundary

The project is licensed **AGPL-3.0** and is a derived work. The licence text,
the upstream copyright notices and the obligation to offer source to network
users must be preserved. Independence here means technical and brand
independence; it does not and cannot mean removing the licence or attribution.
`CompanyName` and `LegalCopyright` in `Runner.rc` are left untouched for the
same reason.

The GitHub fork relationship (`wmenezes2020/meodesk` -> `rustdesk/rustdesk`)
can only be severed by GitHub Support or by recreating the repository.

## Solution

### Metadata

`Cargo.toml` authors, description and `[package.metadata.bundle]`, plus the
Debian control block in `build.py`. The `Homepage` field was dropped rather
than blanked, since an empty value is invalid in a Debian control file. The
macOS bundle identifier was set to `com.meudesk.app` — **assumption**: no real
reverse-domain was specified, and macOS is not built by the current workflows.

The `upstream` git remote pointing at `rustdesk/rustdesk` was removed. No
history, branch or tag was deleted.

### Renaming the crate, library and binary

| From | To |
| --- | --- |
| package `rustdesk` | `meudesk` |
| `[lib] name = "librustdesk"` | `libmeudesk` |
| `default-run` and the sciter binary | `meudesk` |
| Windows `BINARY_NAME` / `.exe` | `meudesk` (applied by `apply_customizations.py`) |

The library name is load-bearing on three chains that must stay in sync:

- **Android**: cargo emits `liblibmeudesk.so`; the workflow copies it to
  `jniLibs/.../libmeudesk.so`; `ffi.kt` calls
  `System.loadLibrary("meudesk")`; `native_model.dart` opens `libmeudesk.so`.
- **Windows**: cargo emits `libmeudesk.dll`; `CMakeLists.txt` installs and
  renames it; `main.cpp` calls `LoadLibraryA`; `native_model.dart` opens it.
- **Rust**: `src/main.rs`, `src/service.rs` and `examples/ipc.rs` import the
  library crate by name.

`Cargo.lock` had to be renamed too — both workflows build with `--locked`, so a
lock that disagrees with the manifest fails the build outright.

Exported C symbols (`rustdesk_core_main_args`, `get_rustdesk_app_name`) keep
their names. They are private to the runner/library boundary and renaming them
would add risk for no visible gain.

The Linux, macOS, iOS and F-Droid build files were updated in the same pass.
They are not built by the custom workflows, but leaving them pointing at a
library name that no longer exists would be a latent break.

## Validation

- `git grep librustdesk` returns nothing outside documentation.
- The load chains above were traced end to end and checked for consistency.
- Compilation is verified by the two custom workflows on push to
  `build-custom`; no Rust or Flutter toolchain exists locally.
- The riskiest item is the `Cargo.lock` rename. If CI fails on `--locked`,
  regenerate the lock with `cargo generate-lockfile` and commit it.
