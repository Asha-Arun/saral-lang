# saral-lang
Saral Lang -A beginner-friendly, English-like programming language. Developed by Asha V S, Kerala, India

# Saral Lang v 1.0.0

### Simple Programming for Everyone

*The world's first beginner-friendly, AI-powered, secure-by-design programming language*

---

**Write code the way you think. No symbols. No jargon. Just plain English.**

```
store 10 in price
store price * 2 in double_price
show "Price: {price}, Double: {double_price}"
```

[Get Started](#quick-start) • [Features](#features) • [Examples](#sample-programs) • [Install](#installation) • [Docs](#documentation)

</div>

---

## What is Saral Lang?

**Saral Lang** (Sanskrit/Hindi: सरल — *simple*) is a general-purpose programming language designed from the ground up for people with no coding background.

It reads like plain English. It runs on minimal hardware. It includes built-in AI assistance. And it transpiles to Python — giving users access to the entire Python ecosystem without ever needing to learn Python syntax.

> "People moved in already established paths. No one moved into a new unexplored path. That is the only difference."  
> — Asha V S, Developer, Saral Lang, Kerala, India, 2026

### Who is it for?

- 🎓 **Students** learning programming for the first time
- 🏪 **Small business owners** who want to automate without hiring a developer
- 🏛️ **Government employees** handling data and reports
- 👩‍🏫 **Teachers** introducing computational thinking
- 🌾 **Anyone** who has an idea but was told "you need to learn to code first"

---

## Quick Start

```bash
# Run a Saral Lang program
saral myprogram.saral

# Interactive mode — type and run line by line
saral --interactive

# AI writes code for you
saral --generate

# Connect your AI (paste any API key)
saral --setup-ai

# Check AI status
saral --status

# Check your program for errors
saral --check myprogram.saral

# Explain what code does
saral --explain myprogram.saral
```

Your first Saral Lang program (`hello.saral`):

```
store "World" in name
show "Hello, {name}!"
show "Today is:"
store today in date
show date
```

Run it:
```bash
saral hello.saral
```

Output:
```
Hello, World!
Today is:
17-06-2026
```

---

## Features

### 🗣️ Natural English Syntax
```
store 10 in apples
store 5 in oranges
store apples + oranges in total
show "Total fruits: {total}"
```

### 🤖 Built-in AI Assistant

Connect any AI provider in seconds using the setup wizard:

```bash
saral --setup-ai
```

Paste your API key — Saral Lang **auto-detects** the provider and tests the connection live. No config files to edit.

**8 supported AI providers:**

| Provider | Key Format | Notes |
|---|---|---|
| xAI Grok | `xai-...` | Get key at console.x.ai |
| OpenAI (GPT-4o) | `sk-proj-...` | Get key at platform.openai.com |
| DeepSeek R1 | `sk-...` (hex) | Free credits at platform.deepseek.com |
| Anthropic Claude | `sk-ant-...` | Get key at console.anthropic.com |
| Google Gemini | `AIza...` | Free tier at aistudio.google.com |
| Groq | `gsk_...` | Fast inference at console.groq.com |
| Mistral | alphanumeric | Get key at console.mistral.ai |
| Cohere | alphanumeric | Get key at dashboard.cohere.com |

**AI fallback chain:**
1. **Configured AI** — whichever provider you set up via `--setup-ai`
2. **Pattern matching** — always available, no internet needed

**Use AI inside your Saral Lang programs:**
```
ask ai "What is the capital of Kerala?" and store in answer
show answer

ask ai "Summarize this report" using report_text and store in summary
show summary
```

**Use AI from the command line:**
```bash
saral --generate          # AI writes Saral Lang code from your description
saral --explain file.saral  # AI explains what your code does
saral --status            # Check which AI is configured
```

### 📊 Math and Science
```
store sin of 90 in s          # Trigonometry (degrees)
store sqrt of 144 in r        # Square root
store round of 3.14159 to 2 places in pi
store square of -5 in sq      # Negative powers: correct sign
store cube of -3 in cu
store log of 1000 in l
```

### 📁 Files, CSV, JSON
```
read csv "sales.csv" and store in data
store column "price" of data in prices
store average of prices in avg
show "Average price: {avg}"
write data to json "output.json"
```

### ✅ Built-in Validation
```
check that email is valid email and store in ok
check that age is between 1 and 120 and store in valid
check that name is not empty and store in filled
```

### 🔴 Colored Output and Progress
```
show "Success!" in green
show "Warning!" in yellow
show "Error!" in red
show progress 45 of 100
```

### 🛡️ Production Error System
Every error has a code (E001–E020), shows the exact line with a pointer, explains in plain English, and suggests a fix:

```
❌  [E002] Variable used before it was stored

   --> myprogram.saral:7:1
    |
  5 | store 10 in price
  6 | show total
    | ^^^^^^^^^^
    | 'total' is used here but has no value yet.

💡  Did you mean:
      • store ... in total  ← add this before line 6

📖  Explanation:
    In Saral Lang, you must store a value in a variable
    before using it.
```

### 📋 Complete Feature List

| Category | Features |
|---|---|
| **Variables** | store, increase, decrease |
| **Math** | + - * / ^ %, sqrt, sin, cos, tan, log, floor, ceiling, absolute, round, square, cube, random |
| **Output** | show, show blank, show in color, show progress |
| **Input** | ask, ask number, ask ai |
| **Conditions** | if, otherwise if, otherwise, done |
| **Loops** | repeat, for each, count from, while, stop, skip |
| **Functions** | define, call, return, default params, multiple return |
| **Lists** | make list, add, remove, sort, reverse, slice, unique, flatten |
| **Dictionaries** | make dictionary, set, get value, deep value |
| **Strings** | uppercase, lowercase, trimmed, reversed, length, split, join, replace, pad |
| **Types** | as number, as text, as decimal, as boolean |
| **Files** | read file, write, append, read lines, delete |
| **CSV** | read csv, write csv, store column |
| **JSON** | read json, write json, parse json, convert to json |
| **HTTP** | fetch, fetch json |
| **Regex** | matches pattern, find pattern, replace pattern |
| **Validation** | valid email, valid phone, is a number, between, not empty |
| **Date/Time** | today, now, current time/year/month/day |
| **Error handling** | try, catch, show error, raise error |
| **AI** | ask ai, generate, explain, fix errors, setup-ai, status |
| **Multiline** | store text block … end block |
| **Import** | use, include |
| **Concurrency** | run in background, wait for all |
| **Utility** | wait, clear screen, exit program |

---

## Sample Programs

### Hello World
```
show "Hello, World!"
```

### Bakery Sales Calculator
```
ask number "Enter today's sales (₹): " and store in sales
store sales * 5 / 100 in gst
store sales + gst in total
store round of total to 2 places in total
show "Sales:  ₹{sales}"
show "GST:    ₹{gst}"
show "Total:  ₹{total}" in bold
```

### Engineering Math
```
ask number "Enter angle in degrees: " and store in angle
store sin of angle in s
store cos of angle in c
store round of s to 6 places in s
store round of c to 6 places in c
show "sin({angle}°) = {s}"
show "cos({angle}°) = {c}"
```

### AI-Powered Q&A
```
store "yes" in running
while running = "yes"
    ask "Your question: " and store in question
    if question = "quit"
        store "no" in running
    otherwise
        ask ai question and store in answer
        show answer
    done
done
```

### Data Validation
```
ask "Enter your email: " and store in email
check that email is valid email and store in ok
if ok
    show "Email accepted!" in green
otherwise
    show "Invalid email!" in red
done
```

---

## Installation

### Linux / Linux Mint / Ubuntu (Recommended)

```bash
# Clone the repository
git clone https://github.com/saral-lang/saral-lang.git
cd saral-lang

# Run the installer
bash install/install_linux.sh
```

The installer automatically:
- Checks Python installation
- Creates the `saral` command globally

After installation:
```bash
saral myprogram.saral
saral --interactive
saral --setup-ai       # connect your preferred AI
```

### Windows 10/11

1. Install Python from [python.org](https://python.org) *(check "Add Python to PATH")*
2. Clone or download this repository
3. Double-click `install/install_windows.bat`

### Manual (Any Platform)

```bash
git clone https://github.com/saral-lang/saral-lang.git
cd saral-lang
python core/saral.py myprogram.saral
```

### Minimum Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.8+ | 3.11+ |
| RAM | 512 MB | 2 GB |
| Storage | 50 MB | 100 MB |
| OS | Windows 10, Ubuntu 20, macOS 11 | Latest |
| Internet | Not required (AI needs it) | For AI features |

---

## What's in v1.0.0

### 🤖 AI Coding Agent — Enforced Saral-Only Generation
`saral --generate` now guarantees the AI never produces Python-style output. Three enforcement layers run on every AI response:

1. **Forbidden-constructs prompt** — the AI is shown an explicit list of Python patterns it must never use (`print()`, `input()`, `x = value`, `for i in range()`, `def`, `import`, etc.) paired with the correct Saral equivalent.
2. **Rule-based sanitizer** — converts any Python slips that still appear: `print(x)` → `show x`, `var = []` → `make list called var`, `int(input(...))` → `ask number ... and store in var`, inline `str(x)` → `x as text`, `elif x == 3:` → `otherwise if x = 3`, and more. A dedicated block-closer pass inserts `done`/`end` wherever Python's indentation-based blocks would leave Saral blocks unclosed.
3. **Compiler validation + AI retry** — the sanitized code is compiled silently through the real Saral parser. If errors remain, they are sent back to the AI for a correction pass. The final result always shows a validation badge:
   ```
   ✅  Validated: uses only valid Saral syntax.
   ```

### 🐛 Step Debugger with AI at Every Step (`saral --debug`)
- AI analysis is now **always available** — falls back to pattern-based hints when no API key is set
- AI **triggers automatically** after every runtime error and on every watchpoint hit
- New `explain` command: understand exactly what the current line does and why it might fail
- Every session auto-saves a `<name>_debugged.saral` file with a comment header listing errors found, watchpoints triggered, and steps run

### 🔧 New Language Feature: List Index Write
```
set item 2 of scores to 99
```
Directly update any position in a list (1-based indexing). Supported in the AST (`SetListStmt`), parser, and code generator.

### 🐞 Bug Fixes — `bakery_one.saral` (9 bugs fixed)
Unclosed string, missing `done`, off-by-one loop index, `len` shadowing Python built-in, type errors in string concatenation, case-sensitive item lookup causing zero sales total.

---

## Architecture

Saral Lang v1.0.0 uses a proper compiler pipeline:

```
Source (.saral)
      ↓
  Lexer (lexer.py)            — tokenizes with exact line+column
      ↓
  Parser (parser.py)          — recursive descent, builds AST
      ↓
  Analyzer (analyzer.py)      — symbol table, type warnings
      ↓
  Code Generator (codegen.py) — AST → Python + source map
      ↓
  Source Map (sourcemap.py)   — exact error line mapping
      ↓
Python execution (via pipeline.py)
      ↓
  AI Layer (ai_helper.py)     — AI features, code generation, explanation
  AI Config (ai_config.py)    — provider detection, key management, setup wizard
```

| File | Role |
|---|---|
| `lexer.py` | Tokenizer |
| `parser.py` | Recursive descent parser |
| `ast_nodes.py` | 60+ typed AST nodes |
| `codegen.py` | Python code generator |
| `analyzer.py` | Semantic analysis |
| `sourcemap.py` | Line number mapping |
| `pipeline.py` | Integration layer |
| `errors.py` | Error reporting system |
| `ai_helper.py` | AI features: generate (with sanitizer + validation), explain, fix, query, debug hints |
| `ai_config.py` | Provider detection, setup wizard, key storage |
| `debugger.py` | Step debugger with AI analysis at every step, auto-save debugged file |

---

## Language Rules

- **Case insensitive** — `STORE`, `Store`, `store` all work
- **Indentation optional** — but recommended for readability
- **Comments** — start with `#`
- **Equality check** — use `=` inside `if` (not `==`)
- **Math** — `+` `-` `*` `/` `^` (power) `%` (modulo)
- **Negative powers** — `(-5)^2 = 25` always correct
- **Degrees** — trigonometry uses degrees, not radians

---

## Documentation

### v1.0.0 release (June 2026)

- 📋 [v1.0.0 Release Summary (PDF)](docs/Saral_v1.0.0_Release_Summary.pdf) — bugs fixed, AI features, test results
- 📑 [v1.0.0 Pre-Release Report (PDF)](docs/Saral_v1.0.0_PreRelease_Report.pdf) — detailed technical documentation
- 📝 [Release Summary (Markdown)](docs/Saral_v1.0.0_Release_Summary.md) · [Full Report (Markdown)](docs/Saral_v1.0.0_PreRelease_Report.md)
- 📝 [Release Notes v1.0.0](RELEASE_NOTES_v1.0.0.md)
- 📜 [Changelog](CHANGELOG.md)
- 🤖 [AI Coding Agent — What's New](../../AI%20coding%20agent.md)

### Language guides

- 📋 [Complete Syntax Reference](#features)
- 💡 [Sample Programs](programs/)

---

## Error Codes

| Code | Meaning |
|---|---|
| E001 | Unknown keyword or command |
| E002 | Variable used before stored |
| E003 | Block not closed |
| E004 | Type mismatch |
| E005 | File not found |
| E009 | Division by zero |
| E011 | List index out of range |
| E012 | Dictionary key not found |
| E013 | Invalid number conversion |
| E014 | Function not defined |
| E015 | Library not installed |
| E020 | General runtime error |

---

## Contributing

Saral Lang is open to contributions. Areas where help is welcome:

- **New language features** — web output, Android target
- **Standard library** — common functions in Saral Lang itself
- **Documentation** — tutorials, videos, translations
- **Bug reports** — programs that fail, edge cases
- **Translations** — error messages in Malayalam, Hindi, Tamil

Please open an issue before submitting a large pull request.

---

## Roadmap

| Phase | Feature | Status |
|---|---|---|
| Phase 1 | Core language + AI + error system | ✅ Complete (v1.0.0) |
| Phase 1.1 | AI coding agent — enforced Saral-only generation, step debugger with AI, auto-save | ✅ Complete (v1.0.0) |
| Phase 2A | Web output — HTML + JavaScript | 🔄 Planned |
| Phase 2B | Web output — React | 🔄 Planned |
| Phase 3 | Android output — Java | 🔄 Planned |
| Phase 4 | Saral Lang Secure — security model | 🔄 Planned |
| Phase 5 | Package manager | 🔄 Planned |
| Phase 6 | Malayalam language keywords | 🔄 Planned |

---

## Trademark

**SARAL LANG** (word mark) and the **Saral Lang green S logo** (device mark) are trademarks of Asha V S,
pending registration as **SARAL LANG** under **Class 42** at the Indian Trade Marks Registry
(ipindia.gov.in).

Trademark applications filed: June 2026 
Word mark: SARAL LANG — Class 42 
Device mark: Saral Lang green S logo — Class 42 
Applicant: Asha V S, Irinjalakuda, Thrissur, Kerala, India 
Class: 42 — Computer programming; software as a service (SaaS);
design and development of computer hardware and software.

**You may:**
- Use the name "Saral Lang" to refer to this programming language (the language name is Saral Lang)
- Say "written in Saral Lang" or "built with Saral Lang"
- Include Saral Lang in your project dependencies

**You may not:**
- Use the Saral Lang name or logo to imply official endorsement
- Create a product called "Saral Lang" or "Saral Lang" in Class 42 (software/technology)
- Register a confusingly similar trademark in the software category

For licensing questions: ashavs@zohomail.in

---

## License

Copyright 2026 Saral Lang Project, Kerala, India

Licensed under the **Apache License, Version 2.0**.
See [LICENSE](LICENSE) for full terms.

---

## Acknowledgements

Saral Lang is developed by **Asha V S**.

> *"I would like to express my deepest gratitude to my husband, Arun Raj R.  
> He has been my biggest support throughout this journey — trusting me, believing in my vision,  
> and investing his time, money, and effort into this project.  
> He designed the complete architecture of Saral Lang with great dedication and care.  
> His constant encouragement and silent strength have made this dream possible.  
> I am truly blessed to have a partner who stands beside me with so much love and belief.  
> Thank you, my dear husband, for everything."*  
> — Asha V S

Built in Irinjalakuda, Thrissur, Kerala, India.  
Named after the Sanskrit word सरल meaning *simple*.  
Designed for the billion people who have ideas but were told they need to learn to code first.

📧 Contact: [ashavs@zohomail.in](mailto:ashavs@zohomail.in)

---

<div align="center">

**🌿 Saral Lang — Simple. Secure. Powerful.**

*Developed with love by Asha V S, Kerala, India.*

*SARAL LANG™ is a trademark of Asha V S, pending registration.*

*Write code the way you think.*

</div>
