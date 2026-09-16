#!/usr/bin/env bash
set -euo pipefail

# Use VS Code's 3-way Merge Editor for `git mergetool`/`git difftool`.
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
git config --global merge.conflictStyle zdiff3
git config --global mergetool.keepBackup false
