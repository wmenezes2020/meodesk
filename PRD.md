# MeoDesk Product Requirements

## Vision

MeoDesk is a branded remote-support client derived from RustDesk. It provides
remote access on Android and Windows while routing custom distributions through
the organization's preconfigured infrastructure.

## Users And Platforms

- End users install the Android or Windows client and receive remote support.
- Support operators initiate and manage remote sessions using the capabilities
  inherited from RustDesk.
- Release maintainers produce branded Android and Windows artifacts through the
  custom GitHub Actions workflows.

## Current Product Scope

### Remote Support

The client retains RustDesk's core remote-desktop capabilities, including
session establishment, screen interaction, clipboard support, file transfer,
and the platform-specific permission flows available in this source tree.

### Branded Builds

The custom build pipeline reads the product name and connection configuration
from `config.json`. `scripts/apply_customizations.py` applies those values to
the Rust core and platform metadata before the Android and Windows builds run.
Product values must not be copied into documentation or build output beyond
what is operationally required.

### Managed Server Configuration

Custom builds use an embedded ID server and public server key. These options are
fixed by `OVERWRITE_SETTINGS`, so ordinary option writes cannot replace them.

When `hide-server-settings=Y` is present in `BUILTIN_SETTINGS`:

- Android and Windows settings must not display the ID/relay server entry or
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
2. The Android or Windows workflow checks out the repository and submodules.
3. The customization script embeds branding and managed connection options.
4. The platform build produces a MeoDesk artifact with restricted server
   settings hidden.

### End-User Settings

1. The user opens Settings on Android or Windows.
2. General settings remain available according to existing platform policies.
3. Managed server fields are absent and cannot be opened or submitted through
   an alternate Flutter route.

## Configuration Contract

- `app_name`: branded application name.
- `server_ip`: managed rendezvous server address.
- `server_key`: public key used to validate the managed server.
- `hide-server-settings`: built-in UI and write policy for managed builds.

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
