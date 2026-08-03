# MeuDesk Product Requirements

## Vision

MeuDesk is a branded remote-support client derived from RustDesk. It provides
remote access on Android, Windows and macOS while routing custom distributions
the organization's preconfigured infrastructure.

## Users And Platforms

- End users install the Android, Windows or macOS client and receive remote
  support.
- Support operators initiate and manage remote sessions using the capabilities
  inherited from RustDesk.
- Release maintainers produce branded Android, Windows and macOS artifacts
  through the custom GitHub Actions workflows.

## Current Product Scope

### Remote Support

The client retains RustDesk's core remote-desktop capabilities, including
session establishment, screen interaction, clipboard support, file transfer,
and the platform-specific permission flows available in this source tree.

### Branded Builds

The custom build pipeline reads the product name and connection configuration
from `config.json`. `scripts/apply_customizations.py` applies those values to
the Rust core and platform metadata before each platform build runs.
Product values must not be copied into documentation or build output beyond
what is operationally required.

### Visual Identity

Custom builds ship the MeuDesk mark on every icon and logo surface. Assets are
generated from the delivered artwork in `images/` by
`scripts/generate_brand_assets.py` and committed, so no build step depends on
regenerating them.

- Android: launcher, round launcher, adaptive foreground and notification icons
  for every density.
- Windows: the Flutter runner icon, the executable icon used by `build.rs`, the
  MSI shortcut icon and the tray icon.
- macOS: the `.app` bundle icon, plus the shared desktop icon sizes and tray
  silhouettes, all from the same source.
- In-app logo assets cover the light and dark themes on the desktop home page
  and the mobile settings page.

### Product Naming

The client is presented as MeuDesk everywhere a user can see it: window and tab
titles, Android launcher and notification entries, the accessibility service,
Windows file metadata, the executable file name, the deep-link scheme and the
two-factor issuer shown in authenticator apps.

The upstream RustDesk name is substituted at runtime in every translated string
by the shared language layer, driven by the configured `app_name`. Internal
identifiers, package names, the AGPL copyright notice and links to upstream
documentation are out of scope and keep their original values.

### Account And Login

Custom builds set the `disable-account` hard option. The organization does not
operate the account service, so the client hides every entry point that depends
on being signed in: the desktop Account settings tab, the Android Account
section, the Address Book and Group peer tabs, and the connection-note option.

### Managed Server Configuration

Custom builds use an embedded ID server and public server key. These options are
fixed by `OVERWRITE_SETTINGS`, so ordinary option writes cannot replace them.

When `hide-server-settings=Y` is present in `BUILTIN_SETTINGS`:

- Settings on every platform must not display the ID/relay server entry or
  its ID server, relay server, API server, and key fields.
- The shared server dialog must not open from alternate routes such as a
  configuration QR code.
- Flutter configuration imports and deep links must not change server options.
- Connection logic must continue using the embedded values and existing API
  and relay fallback behavior.

Standard RustDesk builds without this built-in option retain the existing
editable server-settings experience.

## Primary Flows

### Custom Build

1. A maintainer updates the custom product configuration.
2. The Android, Windows or macOS workflow checks out the repository and
   submodules.
3. The customization script embeds branding and managed connection options.
4. The platform build produces a MeuDesk artifact with restricted server
   settings hidden.

### End-User Settings

1. The user opens Settings on Android, Windows or macOS.
2. General settings remain available according to existing platform policies.
3. Managed server fields are absent and cannot be opened or submitted through
   an alternate Flutter route.

## Configuration Contract

- `app_name`: branded application name.
- `server_ip`: managed rendezvous server address.
- `server_key`: public key used to validate the managed server.
- `hide-server-settings`: built-in UI and write policy for managed builds.
- `hide-powered-by-me`: built-in option that removes the upstream credit.
- `disable-account`: hard option that removes the account/login feature.

Branding artwork lives in `images/`; the generated icon and logo files are the
committed output of `scripts/generate_brand_assets.py`.

Actual configuration values are intentionally omitted from this document.

## Non-goals

- Operating or provisioning the rendezvous/relay server infrastructure.
- Replacing RustDesk's transport protocol or cryptography.
- Hiding every network-related preference from users.
- Guaranteeing that data compiled into a distributed executable cannot be
  recovered through binary analysis.

## Decisions And Trade-offs

- Visibility policy belongs in `BUILTIN_SETTINGS`; fixed connection values
  belong in `OVERWRITE_SETTINGS`.
- Enforcement is shared instead of duplicated in Android and Windows widgets,
  reducing the chance that an alternate entry point bypasses the restriction.
- The upstream editable behavior remains available when the custom policy is
  not enabled.

## Changelog

- 2026-07-24: Specified managed server-setting visibility and write protection
  for custom Android and Windows clients.
- 2026-07-30: Added the MeuDesk visual identity across Android and Windows icons
  and the in-app light/dark logo assets.
- 2026-07-30: Renamed the product from MeoDesk to MeuDesk, removed the upstream
  name from every user-facing surface, and disabled the account/login feature.
- 2026-07-31: Renamed the crate, native library and binary to MeuDesk, cleaned
  the build metadata and dropped the upstream git remote. Mirroring the
  upstream build dependencies remains open.
- 2026-07-31: Added the macOS custom client workflow and the macOS branding
  surfaces (bundle name, icon, deep-link scheme).
