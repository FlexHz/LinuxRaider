#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

mkdir -p "$BIN_DIR" "$APP_DIR" "$ICON_DIR"

chmod +x "$REPO_DIR/main.py"
ln -sf "$REPO_DIR/main.py" "$BIN_DIR/linuxraider"

cp "$REPO_DIR/resources/linuxraider.png" "$ICON_DIR/linuxraider.png"

cat > "$APP_DIR/linuxraider.desktop" <<EOF
[Desktop Entry]
Name=LinuxRaider
GenericName=Game Visual Enhancer
Comment=Control de brillo, gamma y ecualización de sombras para juegos
Exec=$REPO_DIR/main.py
Icon=$REPO_DIR/resources/linuxraider.png
Terminal=false
Type=Application
Categories=Game;Utility;Settings;
Keywords=gamma;brightness;contrast;shadow;gaming;raider;
StartupNotify=true
StartupWMClass=linuxraider
EOF
chmod +x "$APP_DIR/linuxraider.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi

echo "✓ LinuxRaider instalado:"
echo "  - CLI / GUI: $BIN_DIR/linuxraider"
echo "  - Lanzador:  $APP_DIR/linuxraider.desktop"
