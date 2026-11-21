#!/usr/bin/env bash
set -euo pipefail
REPO_URL="https://github.com/Lithium023/luthor-mv.git"
git init
git checkout -B main
git add .
git commit -m "Final Director's Cut: Native 1080p & 720p engines, Act IV mythic 6-scene waves, grand finale montage, all 14 marble assets"
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
git push -u origin main --force
