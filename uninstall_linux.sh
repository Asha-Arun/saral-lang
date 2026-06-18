#!/bin/bash
# ═══════════════════════════════════════════════════════
# Saral Lang Uninstaller — Linux Mint / Ubuntu / Debian
# Version 1.0.0 "First Public Release"
# Run with: bash uninstall_linux.sh
# Developer: Asha V S, Kerala, India
# ═══════════════════════════════════════════════════════

set -e

SARAL_VERSION="1.0.0"
SARAL_DIR="$HOME/.saral"
SARAL_BIN="/usr/local/bin/saral"
DESKTOP_FILE="$HOME/Desktop/Saral.desktop"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step()  { echo -e "\n${BLUE}▶  $1${NC}"; }
print_ok()    { echo -e "   ${GREEN}✅  $1${NC}"; }
print_warn()  { echo -e "   ${YELLOW}⚠️   $1${NC}"; }
print_error() { echo -e "   ${RED}❌  $1${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   🌿  SARAL LANG v$SARAL_VERSION Uninstaller ║"
echo "║   Simple programming for everyone            ║"
echo "║   Developed by Asha V S, Kerala, India       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Confirm uninstall ────────────────────────────────
echo "   This will remove:"
echo "   • Saral Lang files from $SARAL_DIR"
echo "   • 'saral' command from $SARAL_BIN"
echo "   • Desktop shortcut"
echo "   • Saral entries from .bashrc"
echo ""
echo "   Your .saral programs will NOT be deleted."
echo ""
read -p "   Are you sure you want to uninstall? (yes/no): " CONFIRM

if [[ ! "$CONFIRM" =~ ^[Yy] ]]; then
    echo ""
    echo "   Uninstall cancelled. Saral Lang is still installed."
    echo ""
    exit 0
fi

echo ""

# ── Step 1: Remove saral command ─────────────────────
print_step "Removing 'saral' command..."
if [ -f "$SARAL_BIN" ]; then
    sudo rm -f "$SARAL_BIN"
    print_ok "Removed $SARAL_BIN"
else
    print_warn "'saral' command not found — skipping"
fi

# ── Step 2: Remove Saral core files ──────────────────
print_step "Removing Saral core files..."

CORE_FILES=(
    saral.py
    pipeline.py
    lexer.py
    parser.py
    ast_nodes.py
    codegen.py
    analyzer.py
    sourcemap.py
    errors.py
    ai_helper.py
    ai_config.py
    __init__.py
)

for f in "${CORE_FILES[@]}"; do
    if [ -f "$SARAL_DIR/$f" ]; then
        rm -f "$SARAL_DIR/$f"
        print_ok "Removed $f"
    fi
done

# ── Step 3: Remove examples folder ───────────────────
print_step "Removing example programs..."
if [ -d "$SARAL_DIR/examples" ]; then
    rm -rf "$SARAL_DIR/examples"
    print_ok "Removed examples folder"
else
    print_warn "Examples folder not found — skipping"
fi

# ── Step 4: Remove stdlib folder ─────────────────────
print_step "Removing stdlib folder..."
if [ -d "$SARAL_DIR/stdlib" ]; then
    rm -rf "$SARAL_DIR/stdlib"
    print_ok "Removed stdlib folder"
else
    print_warn "stdlib folder not found — skipping"
fi

# ── Step 5: Remove AI config ─────────────────────────
print_step "Removing AI configuration..."
if [ -f "$SARAL_DIR/saral_ai_config.json" ]; then
    rm -f "$SARAL_DIR/saral_ai_config.json"
    print_ok "Removed AI config"
else
    print_warn "AI config not found — skipping"
fi

# ── Step 6: Remove Saral directory ───────────────────
print_step "Removing Saral directory..."
if [ -d "$SARAL_DIR" ]; then
    # Check if anything remains (user files)
    REMAINING=$(ls -A "$SARAL_DIR" 2>/dev/null | wc -l)
    if [ "$REMAINING" -eq 0 ]; then
        rm -rf "$SARAL_DIR"
        print_ok "Removed $SARAL_DIR"
    else
        print_warn "$SARAL_DIR has remaining files — not deleting"
        print_warn "Review and delete manually: ls $SARAL_DIR"
    fi
else
    print_warn "Saral directory not found — skipping"
fi

# ── Step 7: Remove desktop shortcut ──────────────────
print_step "Removing desktop shortcut..."
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    print_ok "Removed desktop shortcut"
else
    print_warn "Desktop shortcut not found — skipping"
fi

# ── Step 8: Clean .bashrc entries ────────────────────
print_step "Cleaning .bashrc..."
if grep -q "SARAL_DIR" "$HOME/.bashrc" 2>/dev/null; then
    # Remove Saral Lang entries from .bashrc
    sed -i '/# Saral Lang/d' "$HOME/.bashrc"
    sed -i '/SARAL_DIR/d' "$HOME/.bashrc"
    sed -i '/SARAL_AI_KEY/d' "$HOME/.bashrc"
    print_ok "Cleaned .bashrc"
else
    print_warn "No Saral entries found in .bashrc — skipping"
fi

# ── Step 9: Remove __pycache__ ───────────────────────
print_step "Cleaning Python cache..."
if [ -d "$SARAL_DIR/__pycache__" ]; then
    rm -rf "$SARAL_DIR/__pycache__"
    print_ok "Removed __pycache__"
fi
find "$HOME" -name "*.saral.py" -delete 2>/dev/null || true
print_ok "Cache cleaned"

# ── Done ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅  Saral Lang uninstalled successfully!   ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "   Saral Lang has been removed from your system."
echo ""
echo "   Your .saral program files are safe."
echo "   They were not deleted."
echo ""
echo "   To reinstall anytime:"
echo "   bash install_linux.sh"
echo ""
echo "   Restart your terminal or run: source ~/.bashrc"
echo ""
echo "   Thank you for using Saral Lang!"
echo "   github.com/Asha-Arun/saral-lang"
echo "   SARAL LANG™ — Trademark Pending Class 42"
echo ""
