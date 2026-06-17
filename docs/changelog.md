# Changelog — Saral Programming Language

All notable changes to Saral are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com).

---

## [1.0.0] — 2026-06-17 — "Complete Compiler Release"

### Fixed
- **Critical** — `saral.py --status` KeyError crash (`status['model']` missing)
- **Critical** — `saral.py` now uses the full compiler pipeline (`pipeline.py`) instead of the legacy regex transpiler
- Parser postfix `as text` / `as number` on any expression (`show "Hi " + name as text`)
- Parser `store trimmed greeting in greeting` (optional `of` keyword, same as transpiler)
- Parser `ask ai variable` with dynamic prompts and data variables
- Debugger and installer module path resolution
- Installer now copies the complete compiler module set (not just 3 files)

### Added
- **Grok (xAI)** as default AI provider — Grok → Ollama → Gemini → pattern matching
- Real CI workflow: syntax check, pipeline self-test, `--check` on all programs
- `XAI_API_KEY` / `SARAL_GROK_MODEL` environment variable support

### Changed
- Default Ollama model aligned to `deepseek-r1:1.5b` (matches `ai_helper.py`)
- Version bumped to 1.0.0

---

## [1.0.0] — 2026-06-17 — "First Public Release"

### Major — Proper Compiler Pipeline
Complete rewrite of the language engine from regex-based transpiler
to a proper compiler with lexer, parser, AST, analyzer, and code generator.

### Added
- `lexer.py` — Full tokenizer with exact line and column tracking (747 lines)
- `parser.py` — Recursive descent parser, zero regex (1,400+ lines)
- `ast_nodes.py` — 60+ typed AST node definitions (585 lines)
- `codegen.py` — AST to Python code generator with source map (916 lines)
- `analyzer.py` — Semantic analysis and symbol table (864 lines)
- `sourcemap.py` — Exact Python↔Saral line number mapping (244 lines)
- `pipeline.py` — Complete integration layer (355 lines)
- `square` keyword — `store square of -5 in result` → `25` (correct sign)
- `cube` keyword — `store cube of -3 in result` → `-27` (correct sign)
- Formal BNF grammar document (`saral_grammar.py`)
- Block validation — detects unclosed if/repeat/for/define blocks
- Symbol table — tracks variables and functions, warns before use
- Warning codes W001–W007 for semantic issues
- Dot notation support — `math.pi`, `os.path` usable after `use`

### Fixed
- **Critical** — Negative base power bug: `-5 ^ 2` now correctly gives `25` not `-25`
- Pattern priority conflicts eliminated (regex transpiler limitation)
- Exact error line numbers via source map (previously approximate)
- `sin of (x + y)` complex expressions now work at any depth
- `store item idx of list` now works with variable index, not just literal
- `count from 1 to n as i` no longer consumes `as` keyword in expression
- `ask "..." and store in lines` now accepts keyword as variable name
- Parser no longer hangs on large programs (infinite loop fixed)
- All `expect(NAME)` calls replaced with `expect_name()` for keyword variables

### Grammar Verification
- 111 grammar tests — 111 passing (100%)
- All syntax rules verified end-to-end

---

## [1.0.0] — 2026-06-05 — "First Public Release"

### Added — Production Error System
- `errors.py` — Complete error reporting module (494 lines)
- Error codes E001–E020 with code snippets, line pointers, suggestions
- Plain English explanations for every error type
- Suggestion engine — finds similar variable names for E002
- Runtime error classification — maps Python exceptions to Saral codes

### Fixed (from Grok audit)
- Multiline strings — `store text block in var ... end block` now works
- Regex SyntaxWarning — patterns auto-prefixed with `r` in generated code
- Dead duplicate code removed from replace pattern handler
- Block validator — properly skips `end block` content
- readline history in interactive mode (`~/.saral_history`)
- Test artifacts (CSV/JSON) now cleaned up after tests

---

## [1.0.0] — 2026-06-04

### Added
- Multiline string blocks — `store text block in var ... end block`
- Block validation — warns on unclosed blocks with line numbers
- Compound conditions — `if x > 5 and x < 10` now works correctly
- readline support in interactive mode (arrow key history)
- Test artifact cleanup in test suite
- `otherwise if` (elif) working in all nesting levels

### Fixed
- `store item * 2 in doubled` — `item` no longer blocked as keyword
- `replace pattern` now correctly placed before string replace
- `show error` priority fixed (was being caught by general `show`)
- `catch` block indentation corrected

---

## [1.0.0] — 2026-06-03 — "Complete Language"

### Added — 20 new features
- String formatting — `show "Hello {name}!"` (f-string style)
- Module system — `include "myfile.saral"`
- CSV support — `read csv`, `write csv`, `store column`
- Global variables — `global price` inside functions
- Default parameters — `define greet using name, title = "Mr"`
- Multiple return values — `return a, b, c`
- List slicing — `store items 2 to 5 of list in result`
- Colored output — `show "text" in red/green/yellow/blue`
- Progress bar — `show progress 45 of 100`
- String padding — `store x padded right to 20 in fmt`
- JSON support — `read json`, `write json`, `parse json`
- HTTP requests — `fetch "url" and store in result`
- Regular expressions — `matches pattern`, `find pattern`, `replace pattern`
- Data validation — `check that email is valid email`
- Concurrency — `run in background`, `wait for all`
- Nested dictionary access — `store deep value of k1 then k2 in dict`
- `make unique list` and `flatten list`
- Trig functions — `sin`, `cos`, `tan` (in degrees)
- Log function — `store log of 1000 in result`
- `wait N seconds`, `clear screen`, `exit program`

### Fixed
- Chained functions `round of sqrt of X` now works
- `store length of "string literal"` now works
- Type conversion in expressions — `show price as text`

---

## [2.0.0] — 2026-06-02 — "Language Completeness"

### Added
- Math functions — sqrt, round, floor, ceiling, absolute, random
- String operations — uppercase, lowercase, trimmed, reversed, split, join, replace
- Type conversion — `as number`, `as text`, `as decimal`, `as boolean`
- File I/O — read file, write, append, read lines, delete file, file exists check
- Date and time — today, now, current time/year/month/day
- Dictionaries — make dictionary, set key, get value
- List operations — sort, reverse, sum, average, max, min, item N of
- Error handling — try, catch, show error, raise error
- `count from N to M as var` loop
- `otherwise if` (elif chain)
- `increase by`, `decrease by`
- `stop` (break) and `skip` (continue)
- `store result of function with args in var`
- Plain English runtime errors with suggestions

### Fixed
- `round of X to N places` now correctly ranked before simple `round`
- `catch` block indentation matching `otherwise`

---

## [1.0.0] — 2026-06-01 — "First Working Language"

### Added — Core Language
- Variables — `store`, `in`
- Math — `+`, `-`, `*`, `/`, `^`, `%`
- Output — `show`
- Input — `ask ... and store in`
- Conditions — `if`, `otherwise`, `done`
- Loops — `repeat N times`, `for each`, `while`
- Functions — `define`, `call`, `return`, `end`
- Lists — `make list`, `add`, `remove`
- Comments — `#`
- Case insensitive keywords
- Transpiles to Python
- AI integration (3-tier: Ollama → Gemini → pattern)
- Interactive REPL (`--interactive`)
- AI code generator (`--generate`)
- Linux and Windows installers
- Plain English error messages

---

## Origin

Saral Lang was conceived and developed by **Asha V S**
in Irinjalakuda, Thrissur, Kerala, India.

Asha V S leads this women-led initiative with a vision to make programming
accessible to everyone.

The project was built using AI as a collaborative tool — itself a demonstration
of Saral Lang's core philosophy. The name comes from the Sanskrit/Hindi word सरल
meaning *simple*.

The core insight: every programming language ever built was designed by engineers
for engineers. Saral Lang is built the other way around — starting from how humans
naturally express instructions, not from how computers receive them.

📧 Contact: ashavs@zohomail.in
