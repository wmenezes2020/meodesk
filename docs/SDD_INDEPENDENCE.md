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

None of these are fixable by editing strings. They are resolved by
`.github/workflows/vendor-upstream-deps.yml`, described below.

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

## Removing the upstream dependency, inside this repository

Everything stays in this repository: no forks, no second account, no extra
secret. The default `GITHUB_TOKEN` can write here, which is all that is needed.

### `libs/hbb_common`

Converted from a git submodule into a normal directory. The 32 files are now
tracked here, `.gitmodules` is gone, and the build no longer clones from
`github.com/rustdesk/hbb_common`. `submodules: recursive` in the workflows
became a harmless no-op.

### The 26 crate dependencies

`.github/workflows/vendor-upstream-deps.yml` runs `cargo vendor`, which copies
only the crates the lock actually uses — a large repository like `wezterm`
contributes just `portable-pty`. It then:

1. Keeps only the git-sourced crates. Vendored crates.io packages carry a
   checksum in `.cargo-checksum.json`; git ones have `"package": null`. The
   registry copies are deleted, so crates.io keeps serving them and the
   committed tree stays small.
2. Writes `.cargo/config.toml` from cargo's own emitted config, minus the
   `[source.crates-io]` block, so only the upstream git sources are redirected.
3. Fails the run if any `git+` source in `Cargo.lock` has no vendored
   directory, rather than letting the build quietly reach the network again.
4. Commits with `git add -f`. The repository-wide `*png` / `*svg` rules would
   otherwise drop fixtures shipped inside some crates, and cargo verifies every
   vendored file against its checksum — a missing file breaks the build.

**`Cargo.toml` and `Cargo.lock` are deliberately untouched.** Source
replacement swaps where cargo reads from without changing what is resolved, so
`--locked` keeps working and every revision stays pinned exactly where it was.
Rewriting URLs would have forced a lockfile rewrite as well.

### The Flutter engine

Republished as a release (`engine-mirror`) on this repository. The Windows
workflow tries `gh release download` first and falls back upstream until the
mirror exists, so it needed no edit when the mirror appeared and works on a
private repository too.

### Timing

The vendor job runs alongside the build jobs on the same push. The first run
still builds against upstream while vendoring happens; from the next push on,
the builds read from `third_party/vendor`. The vendor commit is pushed with
`GITHUB_TOKEN`, which by design does not re-trigger workflows, so there is no
loop.

## Validation

- `git grep librustdesk` returns nothing outside documentation.
- The load chains above were traced end to end and checked for consistency.
- Compilation is verified by the two custom workflows on push to
  `build-custom`; no Rust or Flutter toolchain exists locally.
- The riskiest item is the `Cargo.lock` rename. If CI fails on `--locked`,
  regenerate the lock with `cargo generate-lockfile` and commit it.
