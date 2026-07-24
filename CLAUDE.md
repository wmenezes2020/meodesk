Read and follow `AGENTS.md`.

Apply `.claude/skills/fable-method/SKILL.md` as a mandatory engineering rule
for every development task, together with the other repository skills.

## MeoDesk custom builds

- Android and Windows custom artifacts are built by
  `.github/workflows/build-custom-cliente-*.yml`.
- `scripts/apply_customizations.py` embeds branding and managed connection
  values before compilation.
- Keep `hide-server-settings` in `BUILTIN_SETTINGS`; Flutter reads that map to
  hide and block the restricted server form.
- Keep fixed ID server and public key values in `OVERWRITE_SETTINGS`; do not
  expose their concrete values in documentation or logs.
