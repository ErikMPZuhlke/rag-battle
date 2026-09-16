#!/usr/bin/env bash
set -euo pipefail

# oh-my-posh binary is installed at image build time (see Dockerfile); this only wires up the pwsh profile.
PROFILE_DIR="$HOME/.config/powershell"
PROFILE_FILE="$PROFILE_DIR/Microsoft.PowerShell_profile.ps1"
INIT_LINE='oh-my-posh init pwsh | Invoke-Expression'

mkdir -p "$PROFILE_DIR"
touch "$PROFILE_FILE"
grep -qxF "$INIT_LINE" "$PROFILE_FILE" || echo "$INIT_LINE" >> "$PROFILE_FILE"
