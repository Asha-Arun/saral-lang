#!/bin/bash
# ═══════════════════════════════════════════════════════
# Saral Language Installer — Linux Mint / Ubuntu / Debian
# Version 1.1.0 "AI Auto-Debugger Release"
# Run with: bash install_linux.sh
# Developer: Asha V S, Kerala, India
# ═══════════════════════════════════════════════════════

SARAL_VERSION="1.1.0"
SARAL_DIR="$HOME/.saral"
SARAL_BIN="/usr/local/bin/saral"

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
echo "║   🌿  SARAL LANG v$SARAL_VERSION Installer        ║"
echo "║   Simple programming for everyone            ║"
echo "║   Developed by Asha V S, Kerala, India       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check Python ──────────────────────────────
print_step "Checking Python..."
if command -v python3 &>/dev/null; then
    PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
    print_ok "Python $PY_VER found"
    PYTHON=python3
    # Verify minimum version 3.8
    if ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)" 2>/dev/null; then
        print_error "Saral requires Python 3.8 or higher. Found: Python $PY_VER"
        print_error "Please upgrade Python from https://python.org and re-run."
        exit 1
    fi
else
    print_warn "Python 3 not found. Installing..."
    if command -v apt-get &>/dev/null; then
        sudo apt-get update -qq
        sudo apt-get install -y python3
    else
        print_error "Could not install Python 3 automatically."
        print_error "Please install Python 3.8+ from https://python.org and re-run."
        exit 1
    fi
    PYTHON=python3
    print_ok "Python 3 installed"
fi

# ── Step 2: Locate Saral core files ──────────────────
#
# Use the script's own directory as the anchor — never rely on CWD.
# A valid source directory must contain BOTH saral.py AND pipeline.py.
# Search order: Core/ (uppercase, latest) → core/ (lowercase) → script dir itself.
#
print_step "Locating Saral core files..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR=""

_has_core() {
    [ -f "$1/saral.py" ] && [ -f "$1/pipeline.py" ]
}

# Search candidates in priority order.
# Each must have BOTH saral.py AND pipeline.py to be accepted —
# this prevents picking the project root which has saral.py but not pipeline.py.
for _candidate in \
    "$SCRIPT_DIR/Core" \
    "$SCRIPT_DIR/core" \
    "$SCRIPT_DIR" \
    "$SCRIPT_DIR/Saral_Programme_file/Core" \
    "$SCRIPT_DIR/Saral_Programme_file/core" \
    "$SCRIPT_DIR/../Core" \
    "$SCRIPT_DIR/../core" \
    "$SCRIPT_DIR/../Saral_Programme_file/Core" \
    "$SCRIPT_DIR/../Saral_Programme_file/core"
do
    if _has_core "$_candidate"; then
        SRC_DIR="$(cd "$_candidate" && pwd)"
        print_ok "Found core files in $SRC_DIR"
        break
    fi
done

if [ -z "$SRC_DIR" ]; then
    print_error "Cannot find Saral core files (saral.py + pipeline.py)."
    print_error "Ensure the Core/ folder exists beside or near this installer."
    print_error "Script location: $SCRIPT_DIR"
    exit 1
fi

# ── Step 3: Create Saral directory ───────────────────
print_step "Setting up Saral directory at $SARAL_DIR..."
mkdir -p "$SARAL_DIR"
mkdir -p "$SARAL_DIR/examples"
print_ok "Directory ready"

# ── Step 4: Copy Saral core files ────────────────────
print_step "Installing Saral core files..."

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
    debugger.py
    __init__.py
)

MISSING=0
for f in "${CORE_FILES[@]}"; do
    if [ -f "$SRC_DIR/$f" ]; then
        cp "$SRC_DIR/$f" "$SARAL_DIR/"
        print_ok "Copied $f"
    else
        print_error "Missing: $f — not found in $SRC_DIR"
        MISSING=$((MISSING + 1))
    fi
done

if [ "$MISSING" -gt 0 ]; then
    print_error "$MISSING file(s) could not be copied. Installation incomplete."
    exit 1
fi

# Optional: test suite
if [ -f "$SRC_DIR/test_saral.py" ]; then
    cp "$SRC_DIR/test_saral.py" "$SARAL_DIR/"
    print_ok "Copied test_saral.py"
fi

# Copy example programs if present
for EXAMPLES_DIR in "$SRC_DIR/../examples" "$SRC_DIR/examples" "examples"; do
    if [ -d "$EXAMPLES_DIR" ]; then
        cp "$EXAMPLES_DIR"/*.saral "$SARAL_DIR/examples/" 2>/dev/null && \
            print_ok "Copied example programs" || true
        break
    fi
done

print_ok "All Saral files installed to $SARAL_DIR"

# ── Step 5: Create saral command ─────────────────────
print_step "Creating 'saral' command at $SARAL_BIN..."
sudo tee "$SARAL_BIN" > /dev/null << CMDEOF
#!/bin/bash
$PYTHON "$SARAL_DIR/saral.py" "\$@"
CMDEOF
sudo chmod +x "$SARAL_BIN"
print_ok "'saral' command created"
print_ok "You can now type: saral myfile.saral"

# ── Step 6: Create desktop shortcut ──────────────────
print_step "Creating desktop shortcut..."
DESKTOP_FILE="$HOME/Desktop/Saral.desktop"
if [ -d "$HOME/Desktop" ]; then
    cat > "$DESKTOP_FILE" << DESKEOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Saral Interactive
Comment=Saral Lang — Simple Programming for Everyone
Exec=bash -c '$PYTHON "$SARAL_DIR/saral.py" --interactive; read'
Icon=utilities-terminal
Terminal=true
Categories=Development;
DESKEOF
    chmod +x "$DESKTOP_FILE"
    print_ok "Desktop shortcut created"
else
    print_warn "Desktop folder not found — skipping shortcut"
fi

# ── Step 7: Update PATH in .bashrc ───────────────────
print_step "Updating .bashrc..."
if ! grep -q "SARAL_DIR" "$HOME/.bashrc" 2>/dev/null; then
    {
        echo ""
        echo "# Saral Lang v$SARAL_VERSION"
        echo "export SARAL_DIR=\"$SARAL_DIR\""
    } >> "$HOME/.bashrc"
    print_ok "Added SARAL_DIR to .bashrc"
else
    print_ok ".bashrc already configured"
fi

# ── Step 8: Verify installation ──────────────────────
print_step "Verifying installation..."
if $PYTHON "$SARAL_DIR/saral.py" --version 2>/dev/null; then
    print_ok "Saral Lang is working correctly"
else
    print_warn "Could not auto-verify — try: saral --version"
fi

# ── Done ─────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅  Saral Lang v$SARAL_VERSION installed!       ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "   How to use Saral Lang:"
echo ""
echo "    1. Run a program:       saral myfile.saral"
echo "    2. Interactive mode:    saral --interactive"
echo "    3. AI writes code:      saral --generate"
echo "    4. Check your code:     saral --check myfile.saral"
echo "    5. Explain code:        saral --explain myfile.saral"
echo "    6. Show Python output:  saral --show myfile.saral"
echo "    7. Step debugger:       saral --debug myfile.saral"
echo "    8. AI auto-debugger:    saral --debugger myfile.saral"
echo "    9. Setup AI provider:   saral --setup-ai"
echo "   10. Check AI status:     saral --status"
echo "   11. See version:         saral --version"
echo ""
echo "   Example files are in:  $SARAL_DIR/examples/"
echo ""
echo "   AI Setup:"
echo "   Run 'saral --setup-ai' and paste your API key."
echo "   Supports: OpenAI, DeepSeek, Gemini, Groq,"
echo "             Anthropic, Mistral, Cohere, xAI Grok"
echo ""
echo "   Free AI keys available at:"
echo "   https://aistudio.google.com        (Gemini — free)"
echo "   https://platform.deepseek.com      (DeepSeek — free)"
echo "   https://console.groq.com           (Groq — free)"
echo ""
echo "   Restart your terminal or run: source ~/.bashrc"
echo ""
echo "   SARAL LANG™ — Trademark Pending Class 42"
echo ""
