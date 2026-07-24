# SDD - Hide Restricted Server Settings

## Problem

The custom Android and Windows clients still expose the ID server, relay
server, API server, and key form. Users can view the embedded connection data
and attempt to replace it even though the custom build already supplies the
required server configuration.

## Root cause

`scripts/apply_customizations.py` writes `hide-server-settings=Y` to
`OVERWRITE_SETTINGS`. The Flutter settings pages do not read that map for UI
visibility; they call `mainGetBuildinOption`, which reads `BUILTIN_SETTINGS`.
The existing visibility checks therefore receive an empty value and render the
form.

The QR-code and deep-link import paths can also reach the shared server form or
setter without going through the settings-page visibility checks.

## Goal

Custom Android and Windows builds must not display the restricted server form
or allow server configuration to be changed through Flutter UI entry points.
The embedded server and key must continue to be used by the connection layer.

## Solution

- Generate `hide-server-settings=Y` in `BUILTIN_SETTINGS`, the map consumed by
  the Android and Windows settings pages.
- Keep the embedded ID server and key in `OVERWRITE_SETTINGS`, preserving their
  fixed-value behavior.
- Add a shared Flutter predicate for the built-in visibility policy.
- Stop the shared server dialog before creating controls when the policy is
  active.
- Reject shared server-setting writes when the policy is active, covering
  imports, QR codes, deep links, and future callers.
- Do not print the managed server address in custom-build logs.
- Preserve the current behavior for standard builds where the built-in option
  is absent.

## Non-goals

- Hiding unrelated proxy or WebSocket settings.
- Changing the configured server, key, API derivation, or relay resolution.
- Treating values compiled into a distributed binary as cryptographic secrets.
- Redesigning the existing settings screens.

## Validation

- Compile-check the customization script.
- Verify the generated Rust source places the visibility flag only in
  `BUILTIN_SETTINGS` and the fixed connection values in `OVERWRITE_SETTINGS`.
- Format and analyze the changed Dart files.
- Run the focused Flutter tests and the available project validation commands.
- Review the final diff for Android, Windows, QR-code, and deep-link coverage.
