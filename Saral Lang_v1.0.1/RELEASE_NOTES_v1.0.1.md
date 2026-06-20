# Saral Lang v1.0.1 — Security & Cleanup Release

**Release date:** 2026-06-19  
**Codename:** Security & Cleanup Release  
**Status:** All 95 tests passed

---

## At a Glance

v1.0.1 is a focused maintenance release. No language features changed — every
existing `.saral` program runs exactly as before. The release fixes six security
vulnerabilities found during an internal audit, removes all legacy transpiler
compatibility shims, rewrites both Linux installer scripts, and adds a 95-test
automated test suite.

| Area | v1.0.0 | v1.0.1 |
|---|---|---|
| Transpiler shims | Still present (dead code) | Fully removed |
| Ollama references | In comments and status UI | Cleaned out |
| Save filename validation | None — path traversal possible | Sanitised with regex |
| API key file permissions | World-readable (`644`) | Owner-only (`600`) |
| `include` path validation | No restriction | Blocks `..` and absolute paths |
| `fetch` URL validation | Any scheme including `file://` | `http://` and `https://` only |
| Temp file execution | Written to disk then re-read | Compiled directly from memory |
| AI setup | Environment variables | `saral --setup-ai` wizard |
| Root `saral.py` | Duplicate of core — stale | Thin launcher → delegates to `core/` |
| `install_linux.sh` | Missing `debugger.py`, `ai_config.py` optional | All core files required; debugger included |
| Uninstaller API key cleanup | Looked for wrong filename — key survived | Correctly removes `saral_ai.conf` |
| Test suite | None | 95 tests across 20 categories |

---

## Security Fixes

### SRL-2026-01 — Path Traversal in Save Operations · HIGH

**Files:** `core/saral.py` — `interactive_mode()`, `ai_generate_mode()`

User-supplied filenames were written to disk without any validation. A name like
`../../etc/cron.d/evil` would create files outside the working directory.

```python
# Fixed: filename sanitised before use
safe_name = re.sub(r'[^\w\-]', '_', os.path.basename(fname)).strip('_')
if not safe_name:
    print("  ❌  Invalid filename.")
else:
    with open(f"{safe_name}.saral", "w", ...) as f: ...
```

---

### SRL-2026-02 — API Key File World-Readable · MEDIUM

**File:** `core/ai_config.py` — `save_config()`

`saral_ai.conf` was created with default umask permissions (`644`), making the API
key readable by any user on the same system.

```python
# Fixed: restrict to owner immediately after write
with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    f.write(content)
os.chmod(CONFIG_FILE, 0o600)
```

---

### SRL-2026-03 — Path Traversal via `include` Statement · MEDIUM

**File:** `core/codegen.py` — STDLIB `_include()`

A Saral program could use `include "../../etc/shadow"` to open files outside the
project directory. The file was opened and read even though it would fail to parse.

```python
# Fixed: absolute paths and '..' rejected before open
if _o.path.isabs(_sp) or '..' in _sp.split('/'):
    print("[Include error: absolute paths and '..' are not allowed]"); return
```

---

### SRL-2026-04 — URL Injection in Gemini API Calls · LOW

**Files:** `core/ai_config.py`, `core/ai_helper.py`

The Gemini API embeds the key and model name in the URL. These were interpolated
as raw strings — special characters (`&`, `#`, `%`) would silently corrupt the URL.

```python
# Fixed: URL-encode both parameters
url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{urllib.parse.quote(model, safe='')}:generateContent"
    f"?key={urllib.parse.quote(api_key, safe='')}"
)
```

---

### SRL-2026-05 — SSRF / Local File Read via `fetch` · LOW

**File:** `core/codegen.py` — STDLIB `_fetch()`

`fetch "file:///etc/passwd"` or `fetch "http://169.254.169.254/..."` were both
accepted with no scheme restriction.

```python
# Fixed: only http:// and https:// permitted
if not (_su.startswith('https://') or _su.startswith('http://')):
    return "[Fetch error: only http:// and https:// URLs are allowed]"
```

---

### SRL-2026-06 — TOCTOU Race Condition and Temp File Leaks · LOW

**Files:** `core/pipeline.py`, `core/saral.py`

Compiled Python was written to a temp file and immediately re-read — an unnecessary
roundtrip that created a TOCTOU window. Additionally, `os.unlink()` cleanup was not
inside `finally` blocks, so `sys.exit()` left orphaned files on disk.

```python
# Fixed A: compile directly from memory — no disk roundtrip
code_obj = compile(python_code, filename, "exec")
exec(code_obj, {"__name__": "__main__"})

# Fixed B: guaranteed cleanup
try:
    run_file(tmp_path)
finally:
    try: os.unlink(tmp_path)
    except Exception: pass
```

---

### Uninstaller: API Key Survived Uninstallation · HIGH

**File:** `uninstall_linux.sh`

The uninstaller searched for `saral_ai_config.json` (a legacy name from an earlier
design). The actual config file is `saral_ai.conf`. The API key was silently left on
disk after every uninstall.

```bash
# Fixed: correct filename + legacy cleanup
rm -f "$SARAL_DIR/saral_ai.conf"
rm -f "$SARAL_DIR/saral_ai_config.json"   # remove legacy file if present
```

---

## Code Cleanup

### Transpiler Shims Removed

`pipeline.py` previously shipped two backwards-compatibility wrappers —
`transpile()` and `format_runtime_error()` — that silently called the real compiler
under old names. These have been deleted. All call sites in `saral.py` now call
`compile_saral()` directly.

Files changed: `core/pipeline.py`, `core/saral.py`, `core/codegen.py`,
`core/errors.py`

### Ollama References Cleaned

Ollama was removed from the AI logic in a prior release but its naming survived
in two comments in `core/ai_helper.py`. Updated to reflect the current design
(configured provider → pattern matching).

### AI Setup: Environment Variables Replaced by Wizard

v1.0.0 required manual `export XAI_API_KEY=...` / `export SARAL_GEMINI_KEY=...`
shell commands. v1.0.1 replaces this with a guided setup wizard:

```bash
saral --setup-ai
# Paste any API key — Saral detects the provider automatically
# and tests the connection before saving.
```

Keys are saved to `~/.saral/saral_ai.conf` (permissions `600`). Supported
providers: OpenAI, DeepSeek, Anthropic, Gemini, Groq, Mistral, Cohere, xAI Grok.

---

## Root Launcher Rewritten

The project-root `saral.py` was a full copy of `core/saral.py` that had never been
kept in sync. It contained all six security vulnerabilities above plus two crash
conditions (`transpile` import, Ollama keys in `--status`).

It is now a 30-line thin launcher:

```python
_core_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core")
sys.path.insert(0, _core_dir)
from saral import main   # delegates to core/saral.py
if __name__ == "__main__": main()
```

There is now one source of truth. All fixes apply in `core/saral.py` only.

---

## Installer Fixes

### `install_linux.sh`

| # | Issue | Fix |
|---|---|---|
| 1 | Version `1.0.0` in 3 places | Bumped to `1.0.1` |
| 2 | `debugger.py` not installed | Added to required `CORE_FILES` |
| 3 | `ai_config.py` optional — AI wizard would fail silently | Moved to required |
| 4 | `mkdir -p "$SARAL_DIR/stdlib"` — directory does not exist | Removed |
| 5 | `SARAL_DIR` written to `.bashrc` unquoted | Fixed to `\"$SARAL_DIR\"` |
| 6 | No check for `apt-get` before calling it | Graceful fallback with manual install message added |

Also added: post-install verification step, `test_saral.py` copied when present,
xAI Grok added to the supported providers list.

### `uninstall_linux.sh`

| # | Issue | Fix |
|---|---|---|
| 1 | Wrong API config filename (see SRL-2026-07 above) | Fixed |
| 2 | `sed -i` on `.bashrc` with no backup | Timestamped backup created before edit |
| 3 | `debugger.py` and `test_saral.py` not in removal list | Added |
| 4 | `find "$HOME" -name "*.saral.py" -delete` searched entire home directory for temp files that are no longer created | Removed |
| 5 | Version `1.0.0` in header and variable | Bumped to `1.0.1` |

---

## Test Suite Added

A new automated test suite `core/test_saral.py` ships with v1.0.1.

```bash
python3 core/test_saral.py        # run all tests
python3 core/test_saral.py -v     # verbose output
```

**95 tests across 20 categories:**
Variables, Strings, Conditionals, Loops, Lists, Dictionaries, Functions,
Error Handling, Math, DateTime, File Operations, Validation, Show Variants,
Text Blocks, Security (`_include`), Security (`_fetch`), Filename Sanitisation,
API Key Permissions, Gemini URL Encoding, Version Check.

---

## Test Results

**Environment:** Linux · Python 3.12.3

| Test Group | Tests | Result |
|---|---|---|
| Variables | 12 | ✅ |
| Strings | 9 | ✅ |
| Conditionals | 8 | ✅ |
| Loops | 6 | ✅ |
| Lists | 9 | ✅ |
| Dictionaries | 3 | ✅ |
| Functions | 6 | ✅ |
| Error handling | 3 | ✅ |
| Math functions | 6 | ✅ |
| DateTime | 3 | ✅ |
| File operations | 4 | ✅ |
| Validation | 3 | ✅ |
| Show variants | 3 | ✅ |
| Text blocks | 1 | ✅ |
| Security — `_include` | 3 | ✅ |
| Security — `_fetch` | 3 | ✅ |
| Security — filename sanitisation | 5 | ✅ |
| API key permissions | 1 | ✅ |
| Gemini URL encoding | 2 | ✅ |
| Version check | 4 | ✅ |
| **Total** | **95** | **✅ 95/95** |

---

## Files Changed

| File | Type of Change |
|---|---|
| `core/pipeline.py` | Removed `transpile()` + `format_runtime_error()` shims; `run_saral()` compiles from memory; removed `import tempfile` |
| `core/saral.py` | `compile_saral()` replaces all `transpile()` call sites; save filenames sanitised; temp file cleanup in `finally`; `--setup-ai` and `--debug` handlers added; `run_file()` compiles from memory |
| `core/codegen.py` | `_include()` blocks `..` and absolute paths; `_fetch()` restricts to `http(s)://` |
| `core/ai_config.py` | `save_config()` applies `chmod 600`; Gemini URL parameters encoded with `urllib.parse` |
| `core/ai_helper.py` | Gemini URL parameters encoded; Ollama-era comments updated |
| `core/errors.py` | "transpiler errors" → "compiler errors" in one comment |
| `core/test_saral.py` | **New file** — 95-test automated suite |
| `saral.py` (root) | Rewritten as 30-line thin launcher; all logic in `core/saral.py` |
| `install_linux.sh` | 5 bugs fixed; `debugger.py` added; verification step added |
| `uninstall_linux.sh` | HIGH security fix (API key cleanup); `.bashrc` backup; 4 bugs fixed |

---

## Upgrade

```bash
# Re-run installer (recommended)
bash install_linux.sh

# Or copy updated files manually
cp core/*.py ~/.saral/
```

No `.saral` program changes needed — the language is fully backwards-compatible.

---

## Quick Setup After Install

```bash
saral --version           # should print: Saral v1.0.1 "Security & Cleanup Release"
saral --setup-ai          # paste any AI provider key (optional)
saral --status            # confirm AI is configured
saral --check myfile.saral
```

---

## Documentation

- [What's New in V1.0.1](../../What's%20new%20in%20V1.0.1.md) — full technical changelog
- [Release Summary v1.0.0](docs/Saral_v1.0.0_Release_Summary.md)
- [Release Notes v1.0.0](RELEASE_NOTES_v1.0.0.md)
