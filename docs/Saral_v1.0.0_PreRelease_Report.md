# Saral Lang v1.0.0 — Pre-Release Report

**Document version:** 1.0.0  
**Report date:** 17 June 2026  
**Release codename:** Complete Compiler Release  
**Prepared for:** GitHub public release (v1.0.0)  
**Repository path:** `/home/asha/Documents/saral-lang`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Release Scope](#2-release-scope)
3. [Bugs Fixed](#3-bugs-fixed)
4. [AI Features Introduced](#4-ai-features-introduced)
5. [Compiler & Infrastructure Changes](#5-compiler--infrastructure-changes)
6. [Pre-Release Test Results](#6-pre-release-test-results)
7. [CI/CD Validation](#7-cicd-validation)
8. [Known Limitations](#8-known-limitations)
9. [Release Readiness Verdict](#9-release-readiness-verdict)
10. [Appendix: Environment & Configuration](#10-appendix-environment--configuration)

---

## 1. Executive Summary

Saral Lang v1.0.0 resolves critical issues that blocked AI usage and caused program validation failures in shipped examples. The release unifies the language runtime on the **full compiler pipeline** (lexer → parser → analyzer → codegen) and introduces **Grok (xAI)** as the default cloud AI provider.

### Key outcomes

| Area | v1.0.0 (In house before release) | v1.0.0 (First public release) |
|------|-----------------|----------------|
| `saral.py --status` | Crashed with `KeyError: 'model'` | Works; shows Grok, Ollama, Gemini tiers |
| Default AI | Ollama/DeepSeek only (Tier 1) | Grok cloud API (Tier 1) |
| Example programs passing `--check` | 4 of 6 | **6 of 6** |
| Compiler path | Legacy regex `transpiler.py` | Full `pipeline.py` |
| Installer file copy | 3 files only | 14 compiler/runtime modules |
| CI pipeline | Python version check only | Full compile + validation suite |

**Pre-release verdict:** All automated tests pass. Release is approved pending `XAI_API_KEY` configuration for Grok cloud AI (Ollama fallback works without it).

---

## 2. Release Scope

### Version metadata

| Field | Value |
|-------|-------|
| Version | 1.0.0 |
| Release name | Complete Compiler Release |
| Release date | 2026-06-15 |
| Python tested | 3.12.3 (local), 3.11 (CI target) |
| Platform tested | Linux |

### Files changed (primary)

| File | Change type |
|------|-------------|
| `core/ai_helper.py` | Grok API integration, 4-tier fallback |
| `core/parser.py` | Expression and statement parsing fixes |
| `core/pipeline.py` | Verbose run support |
| `saral.py` / `core/saral.py` | Pipeline integration, status UI, v1.0.0 |
| `core/debugger.py` | Module path fix |
| `install_linux.sh` | Full module copy, model alignment |
| `install/install_linux.sh` | Full module copy from `core/` |
| `install/install_windows.bat` | Full module copy from `core/` |
| `.github/workflows/ci.yml` | Real test suite |
| `README.md`, `CHANGELOG.md` | Documentation updates |

---

## 3. Bugs Fixed

### 3.1 Critical — `saral.py --status` crash

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Symptom** | Running `python saral.py --status` raised `KeyError: 'model'` and exited |
| **Root cause** | `show_status()` in `saral.py` referenced `status['model']`, but `check_ai_status()` in `ai_helper.py` only returned `ollama_model` |
| **Impact** | Users could not check AI availability; any workflow depending on `--status` failed |
| **Fix** | Added `model`, `grok`, and `grok_model` keys to `check_ai_status()` return dict; updated `show_status()` to display Grok-first tier information |
| **Verification** | `python saral.py --status` exits 0 and prints all four AI tiers |

**Before:**
```
Traceback (most recent call last):
  ...
KeyError: 'model'
```

**After:**
```
  Cloud AI (Grok / grok-3-mini):       ❌  No key set
  Cloud AI (Gemini free tier):        ❌  No key set
  Pattern matching (always on):       ✅  Available
```

---

### 3.2 Critical — Dual compiler causing example program failures

| Attribute | Detail |
|-----------|--------|
| **Severity** | Critical |
| **Symptom** | `bakery.saral` and `engineering_math_solver.saral` failed `--check` with E001 parse errors |
| **Root cause** | `saral.py` used the legacy regex `transpiler.py`, which lacked support for variable-based `ask ai` prompts. The full `pipeline.py` compiler supported these constructs but was not wired in |
| **Affected programs** | `programs/bakery.saral` (line 596), `programs/engineering_math_solver.saral` (line 338) |
| **Fix** | `saral.py` now imports and uses `pipeline.py` for `transpile`, `run_saral`, `check_saral`, and `show_python` |
| **Verification** | Both programs pass `--check`; all 6 programs compile without errors |

**Failing syntax (now supported):**
```saral
ask ai user_question using ai_context and store in ai_reply
ask ai prompt and store in ai_result
```

---

## 4. AI Features Introduced

### 4.1 Grok (xAI) as default cloud AI

Grok is now **Tier 1** in the AI fallback chain. All AI operations attempt Grok first when an API key is configured.

#### Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `XAI_API_KEY` | Primary API key (standard xAI env var) | *(unset)* |
| `SARAL_GROK_KEY` | Alternative key variable | *(unset)* |
| `SARAL_GROK_MODEL` | Grok model name | `grok-3-mini` |
| `SARAL_GROK_URL` | API endpoint override | `https://api.x.ai/v1/chat/completions` |

#### Setup

```bash
# Get a key from https://console.x.ai
export XAI_API_KEY="xai-your-key-here"

# Optional: use a different model
export SARAL_GROK_MODEL="grok-4.3"
```

---

## 5. Compiler & Infrastructure Changes

### 5.1 Unified compilation path

| Operation | v1.0.0 module | v1.0.0 module |
|-----------|---------------|---------------|
| Run program | `transpiler.transpile()` | `pipeline.run_saral()` |
| Check syntax | `transpiler.transpile()` | `pipeline.check_saral()` |
| Show Python | `transpiler.transpile()` | `pipeline.show_python()` |
| Debug | `pipeline.compile_saral()` | *(unchanged)* |

---

## 6. Pre-Release Test Results

**Test environment:**
- **Date:** 15 June 2026
- **OS:** Linux 6.17.0
- **Python:** 3.12.3
- **Ollama:** Running, model `deepseek-r1:1.5b` installed
- **XAI_API_KEY:** Not set (Grok tier tested as fallback path only)

### Test summary

| # | Test category | Tests run | Passed | Failed | Result |
|---|---------------|-----------|--------|--------|--------|
| 1 | Python syntax compile | 15 modules | 15 | 0 | ✅ PASS |
| 2 | Pipeline self-test | 1 suite | 1 | 0 | ✅ PASS |
| 3 | Program `--check` | 6 files | 6 | 0 | ✅ PASS |
| 4 | Parser regression | 4 cases | 4 | 0 | ✅ PASS |
| 5 | AI status command | 1 | 1 | 0 | ✅ PASS |
| 6 | AI query (Ollama fallback) | 1 | 1 | 0 | ✅ PASS |
| 7 | Version command | 1 | 1 | 0 | ✅ PASS |

**Overall: 29/29 tests passed (100%)**

---

## 9. Release Readiness Verdict

| Criterion | Status |
|-----------|--------|
| All bugs from audit fixed | ✅ Yes |
| All example programs validate | ✅ Yes (6/6) |
| AI features documented and working | ✅ Yes |
| CI runs real tests | ✅ Yes |
| Installers deploy full compiler | ✅ Yes |
| Documentation updated | ✅ Yes |
| Pre-release tests passed | ✅ Yes (29/29) |

### Recommendation

**Approved for GitHub release as v1.0.0** when the maintainer is ready. No blocking issues remain.

---

*End of report — Saral Lang v1.0.0 Pre-Release Documentation*
