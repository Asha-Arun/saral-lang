# Saral Lang v1.0.0 — Release Summary

**Version:** 1.0.0 · **Codename:** Complete Compiler Release  
**Date:** 15 June 2026 · **Status:** Pre-release tests passed (29/29)

---

## At a Glance

Saral v1.0.0 fixes critical AI and compiler bugs, makes **Grok (xAI)** the default AI provider, and unifies the runtime on the full compiler pipeline. All six shipped example and test programs pass validation.

| Before (v1.0.0)(Pre release) | After (v1.0.0)(Public Release)|
|-----------------|----------------|
| `--status` crashed | Works; shows all AI tiers |
| 4/6 programs passed `--check` | **6/6 pass** |
| Regex transpiler only | Full pipeline (lexer → codegen) |
| Ollama as only AI path | Grok → Ollama → Gemini → patterns |
| Installer copied 3 files | Installer copies 14 modules |

---

## Bugs Fixed

### Critical

**1. `saral --status` crash**  
- **Error:** `KeyError: 'model'`  
- **Cause:** Status UI expected a key that `check_ai_status()` did not return  
- **Fix:** Added `model`, `grok`, `grok_model` to status dict; updated status display  

**2. Example programs failed validation**  
- **Files:** `bakery.saral`, `engineering_math_solver.saral`  
- **Cause:** Legacy transpiler could not parse `ask ai <variable>`  
- **Fix:** `saral.py` now uses `pipeline.py` (full compiler)  

### High

**3. `show ... as text` parse failures**  
- **File:** `calculator.saral` (26 errors)
- **Cause:** `as text` only worked on plain variable names, not keywords like `result`  
- **Fix:** Postfix `as <type>` now applies to any expression in the parser  

### Medium

**4. `store trimmed greeting in greeting`** — `of` is now optional (matches transpiler)
**5. Module paths** — Fixed import resolution in `core/saral.py` and `debugger.py`  
**6. Installer** — Now deploys all 14 compiler modules, not just 3  
**7. Doc drift** — README/installers aligned to `deepseek-r1:1.5b` (was Llama 3.2)  

---

## AI Features Introduced

### Grok as default (Tier 1)

```bash
export XAI_API_KEY="xai-your-key-here"    # get key: console.x.ai
export SARAL_GROK_MODEL="grok-3-mini"     # optional
```

### Four-tier fallback

1. **Grok** (xAI cloud) — default  
2. **Ollama** + DeepSeek R1 1.5b — local, offline  
3. **Gemini** 2.0 Flash — cloud fallback (`SARAL_GEMINI_KEY`)  
4. **Pattern matching** — always available  

### AI capabilities

| Command / syntax | Purpose |
|------------------|----------|
| `saral --generate` | English → Saral code |
| `saral --explain file.saral` | Code → plain English |
| `saral --status` | Check AI tier availability |
| `ask ai "..." and store in x` | AI inside programs |
| `ask ai prompt and store in x` | Dynamic prompt (new) |
| Debugger `fix` | AI session analysis |

---

## Pre-Release Test Results

**Environment:** Linux · Python 3.12.3 · Ollama + deepseek-r1:1.5b

| Test | Result |
|------|--------|
| Python syntax compile (15 modules) | ✅ Pass |
| Pipeline self-test | ✅ Pass |
| `programs/bakery.saral` | ✅ Pass (834 lines) |
| `programs/calculator.saral` | ✅ Pass (312 lines) |
| `programs/engineering_math_solver.saral` | ✅ Pass (587 lines) |
| `programs/example.saral` | ✅ Pass (46 lines) |
| `tests/test_v2.saral` | ✅ Pass (135 lines) |
| `tests/test_v3.saral` | ✅ Pass (245 lines) |
| Parser regression (4 bug-fix cases) | ✅ Pass |
| `saral --status` | ✅ Pass |
| AI query (Ollama fallback) | ✅ Pass |
| `saral --version` → v1.0.0 | ✅ Pass |

**Total: 29/29 passed (100%)**

---

## Release Verdict

✅ **Approved for GitHub release as v1.0.0** — no blocking issues.

### Quick setup after install

```bash
python3 saral.py --version
python3 saral.py --status
python3 saral.py --check programs/example.saral
export XAI_API_KEY="xai-your-key-here"   # enable Grok
```

### Export this document to PDF

```bash
# Option A: pandoc (if installed)
pandoc docs/Saral_v1.0.0_Release_Summary.md -o docs/Saral_v1.0.0_Release_Summary.pdf

# Option B: open in any Markdown viewer → Print → Save as PDF
```

---

**Full report:** [Saral_v1.0.0_PreRelease_Report.md](Saral_v1.0.0_PreRelease_Report.md)  
**Changelog:** [CHANGELOG.md](../CHANGELOG.md) · **Release notes:** [RELEASE_NOTES_v1.0.0.md](../RELEASE_NOTES_v1.0.0.md)