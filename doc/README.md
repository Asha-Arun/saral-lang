# Saral Lang v1.0.0 Documentation

This folder contains release documentation for Saral Lang v1.0.0 (Complete Compiler Release).

## Contents

### 1. **Saral_v1.0.0_Release_Summary.md**
A quick 2-page summary covering:
- At-a-glance improvements
- Critical bugs fixed  
- AI features introduced (Grok, 4-tier fallback)
- Pre-release test results (29/29 passed)
- Quick setup instructions

**Best for:** Getting up to speed quickly, PR announcements, release blog posts.

### 2. **Saral_v1.0.0_PreRelease_Report.md**
Full technical report (10 sections) covering:
- Executive summary with metrics
- Release scope and version details
- Detailed bug fix descriptions (7 bugs)
- AI features and integration details
- Compiler pipeline architecture
- Complete pre-release test results and CI/CD setup
- Known limitations and release verdict
- Environment configuration reference

**Best for:** Code reviews, release audits, historical record, troubleshooting.

---

## Key Highlights

### v1.0.0 Status

✅ **All 7 critical and high-priority bugs fixed**  
✅ **All 6 example programs validate (bakery, calculator, engineering math, example, test_v2, test_v3)**  
✅ **Grok (xAI) integrated as Tier 1 AI provider**  
✅ **4-tier AI fallback chain working (Grok → Ollama → Gemini → patterns)**  
✅ **Full compiler pipeline (lexer → parser → analyzer → codegen)**  
✅ **29/29 pre-release tests passed (100%)**  
✅ **Approved for GitHub public release**  

### Bugs Fixed

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | Critical | `saral --status` crashed with `KeyError` | Added Grok/Ollama/Gemini status dict keys |
| 2 | Critical | 2 example programs failed `--check` | Unified compiler to use `pipeline.py` |
| 3 | High | `as text` type conversion failed on keywords | Moved postfix conversion to `parse_unary()` |
| 4 | Medium | `store trimmed` required `of` keyword | Made `of` optional in `parse_store_stringop()` |
| 5 | Medium | Module path resolution broken | Fixed `sys.path` in `core/saral.py` |
| 6 | Medium | Installer deployed only 3 files | Installer now copies all 14 modules |
| 7 | Low | Documentation had model name mismatches | Aligned all refs to `deepseek-r1:1.5b` |

### AI Features

**Grok (xAI) as default:**
```bash
export XAI_API_KEY="xai-your-key-here"  # Get from console.x.ai
python3 saral.py --generate              # English → Saral code (uses Grok first)
```

**4-tier fallback chain:**
1. Grok cloud API (xAI)
2. Ollama local (deepseek-r1:1.5b)
3. Gemini cloud (fallback)
4. Pattern matching (always on)

**New syntax support:**
```saral
ask ai prompt and store in ai_result                        # Dynamic prompt
ask ai user_question using ai_context and store in ai_reply # Dynamic + context
```

---

## Quick Links

- **Main README:** [../README.md](../README.md)
- **Changelog:** [../CHANGELOG.md](../CHANGELOG.md)
- **Getting started:** [../GETTING_STARTED.md](../GETTING_STARTED.md)

---

## Environment Setup

### For Grok (Tier 1 — cloud)
```bash
export XAI_API_KEY="xai-your-key-here"
# Get key: https://console.x.ai
```

### For Ollama (Tier 2 — local, optional)
```bash
ollama pull deepseek-r1:1.5b
ollama serve
# Runs on localhost:11434
```

### For Gemini (Tier 3 — cloud fallback, optional)
```bash
export SARAL_GEMINI_KEY="your-gemini-key"
# Get key: https://aistudio.google.com
```

### Verify installation
```bash
python3 saral.py --version           # Should show v1.0.0
python3 saral.py --status            # Shows all 4 AI tiers
python3 saral.py --check programs/example.saral  # Should pass
```

---

## Test Results Summary

| Category | Result |
|----------|--------|
| Python syntax (15 modules) | ✅ 15/15 pass |
| Pipeline self-test | ✅ Pass |
| Program validation (6 files) | ✅ 6/6 pass |
| Parser regression (4 cases) | ✅ 4/4 pass |
| AI status command | ✅ Pass |
| AI query (Ollama) | ✅ Pass |
| Version info | ✅ v1.0.0 |
| **Total** | **✅ 29/29 (100%)** |

**Environment:** Linux · Python 3.12.3 · Ollama + deepseek-r1:1.5b  
**Date:** 15 June 2026

---

## Release Verdict

✅ **Approved for public release**

**No blocking issues. All critical bugs fixed. All tests passing.**

See detailed reports above for:
- Root causes and fixes
- Test methodology and results
- Known limitations and workarounds
- Configuration examples

---

*Generated: 17 June 2026 · Saral Lang v1.0.0*