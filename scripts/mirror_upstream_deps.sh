#!/usr/bin/env bash
#
# Mirror every upstream build dependency into your own GitHub account and
# repoint the repository at the mirrors.
#
# Why: the build currently cannot run without github.com/rustdesk and
# github.com/rustdesk-org. Forks are server-side copies, so they survive if an
# upstream repository is renamed, made private or deleted.
#
# Run once, from the repository root:
#
#     bash scripts/mirror_upstream_deps.sh
#
# The script is idempotent: repositories that already exist are skipped.
# It does not push anything to this repository — review and commit yourself.

set -euo pipefail

OWNER="${MIRROR_OWNER:-wmenezes2020}"

REPOS=(
  rustdesk/hbb_common
  rustdesk-org/The-Fat-Controller
  rustdesk-org/android-wakelock
  rustdesk-org/arboard
  rustdesk-org/clipboard-master
  rustdesk-org/confy
  rustdesk-org/cpal
  rustdesk-org/default_net
  rustdesk-org/evdev
  rustdesk-org/hwcodec
  rustdesk-org/impersonate-system
  rustdesk-org/kcp-sys
  rustdesk-org/keepawake-rs
  rustdesk-org/machine-uid
  rustdesk-org/magnum-opus
  rustdesk-org/nokhwa
  rustdesk-org/pam
  rustdesk-org/parity-tokio-ipc
  rustdesk-org/pulsectl
  rustdesk-org/rdev
  rustdesk-org/rust-sciter
  rustdesk-org/rust-webm
  rustdesk-org/sysinfo
  rustdesk-org/tao
  rustdesk-org/tokio-socks
  rustdesk-org/wallpaper.rs
  rustdesk-org/wezterm
)

echo "==> 1/3  Forking ${#REPOS[@]} repositories into $OWNER"
for repo in "${REPOS[@]}"; do
  name="${repo##*/}"
  if gh repo view "$OWNER/$name" >/dev/null 2>&1; then
    echo "    skip   $name (already exists)"
  else
    echo "    fork   $repo"
    gh repo fork "$repo" --clone=false
    sleep 2   # stay under the secondary rate limit
  fi
done

echo "==> 2/3  Repointing dependency URLs in this repository"
for f in Cargo.toml libs/enigo/Cargo.toml libs/scrap/Cargo.toml; do
  if grep -q "github.com/rustdesk-org/" "$f"; then
    sed -i "s|github.com/rustdesk-org/|github.com/$OWNER/|g" "$f"
    echo "    updated $f"
  fi
done

if grep -q "rustdesk/hbb_common" .gitmodules; then
  sed -i "s|github.com/rustdesk/hbb_common|github.com/$OWNER/hbb_common|" .gitmodules
  git submodule sync libs/hbb_common
  echo "    updated .gitmodules"
fi

echo "==> 3/3  Repointing dependency URLs inside the hbb_common submodule"
# hbb_common has its own rustdesk-org dependencies, so the fork needs its own
# commit. The parent repository then pins that commit.
pushd libs/hbb_common >/dev/null
git remote set-url origin "https://github.com/$OWNER/hbb_common"
if grep -q "github.com/rustdesk-org/" Cargo.toml; then
  sed -i "s|github.com/rustdesk-org/|github.com/$OWNER/|g" Cargo.toml
  git checkout -B meudesk
  git commit -am "Point dependencies at the $OWNER mirrors"
  git push -u origin meudesk
  echo "    pushed $OWNER/hbb_common@meudesk"
fi
popd >/dev/null

cat <<EOF

Done. Review and commit:

    git add .gitmodules Cargo.toml libs/enigo/Cargo.toml libs/scrap/Cargo.toml libs/hbb_common
    git commit -m "Chore: apontar dependencias para os mirrors proprios"
    git push origin build-custom

Still manual — the custom Flutter engine. Release assets are not copied by a
fork, so it has to be downloaded and re-uploaded once:

    curl -LO https://github.com/rustdesk/engine/releases/download/main/windows-x64-release.zip
    gh release create engine-main -R $OWNER/meodesk -t "Flutter engine" -n "Mirror" windows-x64-release.zip

then change the URL in .github/workflows/build-custom-cliente-windows.yml.
EOF
