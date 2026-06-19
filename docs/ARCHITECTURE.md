# Saral Lang v1.0.0 — Complete Architecture

## File Organization

### Core Compiler Modules

All files must be in the **`core/`** directory for the program to run correctly:

```
core/
├── saral.py              ← Main entry point (imports all modules)
├── pipeline.py           ← Full compiler pipeline (lexer → codegen)
├── lexer.py              ← Tokenization with line/column tracking
├── parser.py             ← Recursive descent parser → AST
├── ast_nodes.py          ← AST node definitions
├── codegen.py            ← AST → Python code generator
├── analyzer.py           ← Semantic analysis & symbol table
├── sourcemap.py          ← Python ↔ Saral line mapping
├── errors.py             ← Rich error reporting with ANSI colors
├── debugger.py           ← Interactive step-through debugger
├── ai_helper.py          ← AI integration (Grok, Ollama, Gemini, patterns)
├── ai_config.py          ← AI provider detection & key management
├── transpiler.py         ← Legacy regex transpiler (backward compat)
├── memory.py             ← Memory management helpers (optional)
└── __init__.py           ← Package marker
```

### Key Integration Files

```
root/
├── saral.py              ← Wrapper that imports from core/
├── install_linux.sh      ← Copies core/ modules to /opt/saral
├── install/
│   ├── install_linux.sh
│   └── install_windows.bat
└── .github/workflows/
    └── ci.yml            ← GitHub Actions test suite
```

---

## Compilation Pipeline

```
Source Code (.saral)
        ↓
   lexer.py
  Tokenize with accurate line/col tracking
        ↓
  parser.py
  Recursive descent → Abstract Syntax Tree (AST)
        ↓
 analyzer.py
  Symbol table, semantic warnings, type inference
        ↓
  codegen.py
  AST → Python source code + source map
        ↓
 sourcemap.py
  Maintain Saral ↔ Python line mapping
        ↓
  errors.py
  Rich error reporting (when needed)
        ↓
 Execute or debug
```

---

## AI Fallback Chain

**All AI operations route through `ai_helper._call_ai()`**, which implements a four-tier fallback:

```
User requests AI (ask ai, --generate, --explain, etc.)
    ↓
  Tier 1: Grok (xAI cloud)
    · API key: XAI_API_KEY
    · Model: grok-3-mini
    · Speed: ~2-3 seconds
    ↓ [fails / no key]
  Tier 2: Ollama (local)
    · Model: deepseek-r1:1.5b
    · Speed: ~20-40 seconds
    · Requires: ollama serve running
    ↓ [fails / not running]
  Tier 3: Gemini / DeepSeek (cloud fallback)
    · Keys: SARAL_GEMINI_KEY, etc.
    ↓ [fails / no key]
  Tier 4: Pattern matching
    · Always available
    · No network or key required
```

**Configuration:**
```bash
# Tier 1 (Grok)
export XAI_API_KEY="xai-..."

# Tier 2 (Ollama)
ollama pull deepseek-r1:1.5b
ollama serve

# Tier 3 (Gemini)
export SARAL_GEMINI_KEY="AIza..."
```

---

## Module Responsibilities

| Module | Responsibility |
|--------|-----------------|
| **saral.py** | CLI entry point, command dispatcher (--generate, --status, etc.) |
| **pipeline.py** | Coordinates lexer → parser → analyzer → codegen; handles compilation errors |
| **lexer.py** | Converts raw source → token stream with line/col tracking |
| **parser.py** | Tokens → AST using recursive descent parsing |
| **ast_nodes.py** | AST node classes (Program, StoreStmt, IfStmt, etc.) |
| **codegen.py** | AST → Python code; maintains source map |
| **analyzer.py** | Symbol table, variable usage, type checking, semantic warnings |
| **sourcemap.py** | Maps Python line numbers ↔ Saral line numbers for error reporting |
| **errors.py** | Rich error formatting with ANSI colors, suggestions, explanations |
| **debugger.py** | Interactive debugger: step, breakpoints, watchpoints, AI fix |
| **ai_helper.py** | AI calls, code generation, error fixing, explanation (4-tier fallback) |
| **ai_config.py** | Detect provider from API key, test connectivity, save config |

---

## Error Reporting

**When a Saral program fails:**

```
1. Extract Python traceback
2. Map Python line → Saral line (via sourcemap)
3. Classify error (E001-E020) via errors.py
4. Display rich error with:
   - Error code + description
   - Source line with column pointer (^)
   - Plain English explanation
   - Suggestions for fixing
   - Optional: AI-powered fix explanation (via ai_helper)
```

Example:
```
❌  [E009] You tried to divide by zero
     Division by zero is not possible in mathematics.
     
     13 | store 10 / result in answer
                 ^
     
  💡  Did you mean:
       • if divisor != 0
            store numerator / divisor in result
        done
```

---

## Testing

**All tests run in GitHub Actions (`.github/workflows/ci.yml`):**

1. **Python syntax check** — All 15 modules compile
2. **Pipeline self-test** — `python3 core/pipeline.py` passes
3. **Program validation** — All `programs/*.saral` and `tests/*.saral` pass `--check`
4. **AI status** — `saral --status` runs without error
5. **Version** — `saral --version` reports v1.0.0

---

## Critical: All Files Must Be in core/

If files are missing or in wrong locations, you'll get:

```
❌  ModuleNotFoundError: No module named 'pipeline'
❌  ImportError: cannot import name 'parse' from 'parser'
❌  KeyError: 'model' in saral.py --status
```

**Solution:**
```bash
# Ensure all 14 modules are in core/
ls core/*.py | wc -l    # should show 14

# Test import
python3 -c "from core import pipeline; print('OK')"
```

---

## Environment Variables

```bash
# AI Configuration
export XAI_API_KEY="xai-..."                    # Grok (Tier 1)
export SARAL_OLLAMA_MODEL="deepseek-r1:1.5b"  # Ollama (Tier 2)
export SARAL_GEMINI_KEY="AIza..."              # Gemini (Tier 3)

# Development
export SARAL_DEBUG=1                            # Verbose output
```

---

## Verification Checklist

Before pushing to GitHub:

- [ ] All 14 core modules present in `core/` directory
- [ ] `python3 -m py_compile core/*.py` passes (syntax check)
- [ ] `python3 saral.py --version` shows v1.0.0
- [ ] `python3 saral.py --status` runs without error
- [ ] `python3 saral.py --check programs/example.saral` passes
- [ ] Installer copies all 14 modules to destination
- [ ] Git repository initialized: `git init && git add . && git commit -m "v1.0.0"`

---

**End of Architecture Guide**
