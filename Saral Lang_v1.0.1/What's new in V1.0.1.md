# What's New in Saral Lang v1.0.1

**Release Date:** 2026-06-19
**Type:** Code Quality & Security Release

This release removes all legacy transpiler code, fixes security vulnerabilities
discovered during an internal audit, rewrites the Linux installer scripts, and
consolidates the project entry point. No new language features were added. Existing
`.saral` programs run unchanged.

---

## 1. Transpiler Code Fully Removed

Saral v4.0 replaced the original regex-based `transpiler.py` with a proper
lexer → parser → AST → code-generator pipeline. However, v1.0.0 still shipped
backwards-compatibility shims that silently called the new pipeline under the old
names. These wrappers have now been removed entirely.

### Files Changed

| File | What Was Removed / Changed |
|---|---|
| `pipeline.py` | Removed `transpile()` and `format_runtime_error()` wrapper functions and their section header comment |
| `pipeline.py` | Module docstring updated: removed "backwards compatible with existing saral.py" |
| `saral.py` | Import changed from `transpile, format_runtime_error` to `compile_saral` |
| `saral.py` | All three `transpile(source)` call sites replaced with `compile_saral(source, filepath)` |
| `saral.py` | Error messages "transpiler bug" and "Transpiler error" corrected to "compiler bug" / "Compiler error" |
| `saral.py` | Inline `format_runtime_error(...)` calls replaced with direct f-string messages |
| `codegen.py` | STDLIB `_include()` helper updated: replaced `from pipeline import transpile` + `transpile(src)` with `compile_saral(src, path, show_warnings=False)` |
| `errors.py` | Comment "For transpiler errors (unknown lines)" corrected to "For compiler errors (unknown lines)" |

---

## 2. Offline AI (Ollama) References Cleaned

Saral previously supported a local offline AI via Ollama as "Tier 1". When the
multi-provider cloud AI system was introduced, Ollama was removed from the logic but
its naming lived on in comments. These have been updated to reflect the current design.

### Files Changed

| File | What Was Changed |
|---|---|
| `ai_helper.py` | `query()` docstring: "Fallback chain: DeepSeek → Gemini → Pattern" → "Fallback chain: Configured AI → Pattern matching → Helpful message" |
| `ai_helper.py` | Internal comment `# Tier 1 + 2: AI` → `# Try configured AI first` |

---

## 3. Security Fixes

Six vulnerabilities were identified and fixed across five files.

---

### 3.1 Path Traversal in Save Operations — HIGH

**File:** `saral.py`
**Functions:** `interactive_mode()` save command, `ai_generate_mode()` save action

**Problem:** User-supplied filenames were written to disk without any sanitisation.
A filename like `../../etc/cron.d/evil` would write outside the working directory
to an arbitrary path on the filesystem.

```python
# BEFORE (vulnerable)
fpath = f"{fname}.saral"
with open(fpath, "w", ...) as f:
    f.write(...)

# AFTER (fixed)
safe_name = re.sub(r'[^\w\-]', '_', os.path.basename(fname)).strip('_')
if not safe_name:
    print("  ❌  Invalid filename.")
else:
    fpath = f"{safe_name}.saral"
    with open(fpath, "w", ...) as f:
        f.write(...)
```

Only alphanumeric characters, underscores, and hyphens are now accepted. Path
separators (`/`, `\`) and directory traversal sequences (`..`) are stripped.

---

### 3.2 API Key File World-Readable — MEDIUM

**File:** `ai_config.py`
**Function:** `save_config()`

**Problem:** The API key file `saral_ai.conf` was created with the system's default
umask, which on Linux produces permissions `644` (owner read/write, group and world
read). Any other user on the same machine could read the API key.

```python
# BEFORE (vulnerable)
with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# AFTER (fixed)
with open(CONFIG_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
os.chmod(CONFIG_FILE, 0o600)  # owner read/write only
```

The file is now immediately restricted to owner-only access (`600`) after writing.

---

### 3.3 Path Traversal in `include` Statement — MEDIUM

**File:** `codegen.py` (inside the STDLIB template)
**Function:** `_include()`

**Problem:** A Saral program could use `include "/etc/shadow"` or
`include "../../config/secrets"` to attempt reading files outside the project
directory. The file would be compiled as Saral code (so non-Saral content would
fail to parse), but the file was still opened and read.

```python
# BEFORE (vulnerable)
def _include(path):
    if not _o.path.exists(path):
        print(f"[Include error: '{path}' not found]"); return
    with open(path, "r", ...) as f: src = f.read()
    ...

# AFTER (fixed)
def _include(path):
    _sp = str(path).replace('\\', '/')
    if _o.path.isabs(_sp) or '..' in _sp.split('/'):
        print(f"[Include error: absolute paths and '..' are not allowed]"); return
    if not _o.path.exists(path):
        print(f"[Include error: '{path}' not found]"); return
    with open(path, "r", ...) as f: src = f.read()
    ...
```

Absolute paths and any path containing `..` are now rejected before the file is opened.

---

### 3.4 URL Injection in Gemini API Calls — LOW

**Files:** `ai_config.py` (`_test_gemini()`), `ai_helper.py` (`_call_gemini()`)

**Problem:** The Gemini API uses a key-in-URL pattern. The API key and model name
were embedded directly in the URL string via f-string interpolation without URL
encoding. Special characters such as `&`, `#`, `?`, or `%` in the key or model
name would silently corrupt the URL and cause request failures.

```python
# BEFORE (vulnerable)
url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{model}:generateContent?key={api_key}"
)

# AFTER (fixed) — applied in both ai_config.py and ai_helper.py
import urllib.parse
url = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{urllib.parse.quote(model, safe='')}:generateContent"
    f"?key={urllib.parse.quote(api_key, safe='')}"
)
```

`urllib.parse` was added to the imports of both files.

---

### 3.5 SSRF / Local File Read via `fetch` — LOW

**File:** `codegen.py` (inside the STDLIB template)
**Function:** `_fetch()`

**Problem:** The `fetch "url"` Saral statement called `urllib.request.urlopen()`
with no URL scheme validation. A Saral program could use `fetch "file:///etc/passwd"`
to read local files, or fetch internal network addresses for server-side request
forgery.

```python
# BEFORE (vulnerable)
def _fetch(url):
    try:
        with _ur.urlopen(_ur.Request(url), timeout=15) as r:
            return r.read().decode()
    except Exception as e: return f"[Fetch error:{e}]"

# AFTER (fixed)
def _fetch(url):
    try:
        _su = str(url).strip()
        if not (_su.startswith('https://') or _su.startswith('http://')):
            return "[Fetch error: only http:// and https:// URLs are allowed]"
        with _ur.urlopen(_ur.Request(_su), timeout=15) as r:
            return r.read().decode()
    except Exception as e: return f"[Fetch error:{e}]"
```

Only `http://` and `https://` scheme URLs are now accepted.

---

### 3.6 TOCTOU Race Condition and Temp File Leaks — LOW

**Files:** `pipeline.py` (`run_saral()`), `saral.py` (`run_file()`, `interactive_mode()`)

**Problem:** Compiled Python code was written to a temporary file, that file was then
re-opened and read back, then compiled. This created an unnecessary time-of-check /
time-of-use (TOCTOU) window during which the temp file could be replaced. Additionally,
in `interactive_mode()`, the `os.unlink()` cleanup call was not inside a `finally` block,
so a `sys.exit()` from inside `run_file()` would leave orphaned temp files on disk.

**Fix A — Remove the needless disk roundtrip:**

```python
# BEFORE (vulnerable to TOCTOU)
with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, ...) as tmp:
    tmp.write(python_code)
    tmp_path = tmp.name
try:
    with open(tmp_path, ...) as f:
        code_obj = compile(f.read(), tmp_path, "exec")
    exec(code_obj, {"__name__": "__main__"})
finally:
    os.unlink(tmp_path)

# AFTER (fixed — compile directly from memory)
code_obj = compile(python_code, filename, "exec")
exec(code_obj, {"__name__": "__main__"})
```

Applied in both `saral.py`'s `run_file()` and `pipeline.py`'s `run_saral()`.
The `import tempfile` was also removed from `pipeline.py` as it is no longer needed there.

**Fix B — Wrap temp file cleanup in `finally`:**

The `.saral` temp files created inside `interactive_mode()` (for the `run` and
`check` commands) and `ai_generate_mode()` (for the `run` action) now use
`try/finally` to guarantee cleanup even when `sys.exit()` is raised:

```python
# BEFORE (temp file leaked on sys.exit)
run_file(tmp_path)
os.unlink(tmp_path)

# AFTER (always cleaned up)
try:
    run_file(tmp_path)
finally:
    try: os.unlink(tmp_path)
    except Exception: pass
```

---

---

## 4. Root Launcher (`saral.py`) Rewritten

The project-root `saral.py` was a full duplicate of `core/saral.py` that had never
been updated to match the session's fixes. It contained every bug and vulnerability
that was already patched in `core/saral.py`.

### Problems in the old root `saral.py`

| # | Issue | Severity |
|---|---|---|
| 1 | `from pipeline import transpile, format_runtime_error` — both functions removed this release | **Crash on import** |
| 2 | `show_status()` read `status["ollama"]`, `status["ollama_model"]` — keys removed with Ollama | **Crash on `--status`** |
| 3 | No `--setup-ai` handler — running `saral --setup-ai` silently fell through | Missing feature |
| 4 | `--debug` mapped to verbose flag, not the step-through debugger | Bug |
| 5 | User-supplied save filenames written to disk without sanitisation | Path traversal |
| 6 | Temp file `os.unlink()` not inside `try/finally` | Temp file leak |
| 7 | Version `"2026-06-15"` / `"Complete Compiler Release"` — wrong date and name | Wrong metadata |

### Fix

The root `saral.py` was replaced with a **30-line thin launcher**. It has one job:
add `core/` to `sys.path` and call `core/saral.py`'s `main()`.

```python
import sys, os

_core_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "core")
if not os.path.isdir(_core_dir):
    print(f"\n❌  Cannot find core/ directory at: {_core_dir}\n")
    sys.exit(1)
sys.path.insert(0, _core_dir)

from saral import main   # resolves to core/saral.py

if __name__ == "__main__":
    main()
```

There is now one source of truth — `core/saral.py`. All future fixes apply there
automatically; the root launcher requires no maintenance.

---

## 5. Linux Installer (`install_linux.sh`) Fixed

### Bugs Fixed

| # | Bug | Fix |
|---|---|---|
| 1 | Version `1.0.0` in script header, `SARAL_VERSION`, and `.bashrc` comment | Bumped all three to `1.0.1` |
| 2 | `debugger.py` missing from `CORE_FILES` — debugger not installed | Added to required files list |
| 3 | `ai_config.py` listed as "optional" — AI setup wizard would fail without it | Moved to required `CORE_FILES` |
| 4 | `mkdir -p "$SARAL_DIR/stdlib"` created a directory that does not exist in the project | Removed; STDLIB is embedded in `codegen.py` |
| 5 | `SARAL_DIR` written to `.bashrc` without surrounding quotes | Fixed to `\"$SARAL_DIR\"` — safe for home paths containing spaces |

### Improvements

- Added `test_saral.py` as an optional copy (copied if present)
- Added `apt-get` availability check before attempting auto-install of Python 3
- Added non-Debian fallback message with manual install instructions
- Added Step 7: post-install verification (`saral --version`)
- Added `xAI Grok` to the supported providers list in the completion banner
- Removed the separate "optional" block for `ai_config.py`

---

## 6. Linux Uninstaller (`uninstall_linux.sh`) Fixed

### Security Fix

| # | Issue | Severity | Fix |
|---|---|---|---|
| 1 | Cleaned up `saral_ai_config.json` (old name) instead of `saral_ai.conf` (current name) — API key survived uninstallation | **HIGH** | Fixed to remove `saral_ai.conf`; also removes legacy `saral_ai_config.json` if present |
| 2 | `sed -i` modified `.bashrc` with no backup — file damage on failure left shell broken | Medium | Added timestamped backup before any `sed` edit |

### Bugs Fixed

| # | Bug | Fix |
|---|---|---|
| 1 | `debugger.py` missing from removal list — orphaned file left on disk | Added |
| 2 | `test_saral.py` missing from removal list | Added |
| 3 | `find "$HOME" -name "*.saral.py" -delete` searched entire home directory for temp `.py` files that are no longer created (TOCTOU fix in section 3.6 eliminated them) | Removed entirely |
| 4 | Version `1.0.0` in header and `SARAL_VERSION` variable | Bumped to `1.0.1` |

---

## Summary of All Files Modified

| File | Changes |
|---|---|
| `core/pipeline.py` | Removed `transpile()` + `format_runtime_error()` shims; removed `import tempfile`; `run_saral()` compiles from memory |
| `core/saral.py` | Updated all `transpile()` call sites; fixed error messages; sanitised save filenames; fixed temp file cleanup; compiles from memory; added `--setup-ai` and `--debug` handlers |
| `core/codegen.py` | `_include()` blocks absolute/traversal paths; `_fetch()` validates URL scheme |
| `core/ai_config.py` | Added `urllib.parse`; Gemini URL parameters encoded; API key file restricted to `0o600` |
| `core/ai_helper.py` | Added `urllib.parse`; Gemini URL parameters encoded; updated Ollama-era comments |
| `core/errors.py` | "transpiler errors" comment corrected to "compiler errors" |
| `core/test_saral.py` | **New file** — 95-test suite across 20 categories |
| `saral.py` (root) | Rewritten as 30-line thin launcher; delegates entirely to `core/saral.py` |
| `install_linux.sh` | Version bumped; `debugger.py` added; `ai_config.py` made required; obsolete `stdlib` mkdir removed; `.bashrc` export quoted; verification step added |
| `uninstall_linux.sh` | Version bumped; API config filename corrected (`saral_ai.conf`); `.bashrc` backup added; `debugger.py` + `test_saral.py` added to removal list; obsolete `find` sweep removed |

---

## Compatibility

All changes are internal. The Saral language syntax, available commands, and AI
provider setup procedure (`python saral.py --setup-ai`) are identical to v1.0.0.
Existing `.saral` programs do not require any modification.
