"""
saral.py — Saral Language Launcher v1.1.0

Usage:
  python saral.py myfile.saral              Run a Saral program
  python saral.py --interactive             Interactive mode (REPL)
  python saral.py --generate               AI writes code for you
  python saral.py --explain myfile.saral   AI explains your code
  python saral.py --check myfile.saral     Validate without running
  python saral.py --show myfile.saral      Show generated Python
  python saral.py --debug myfile.saral     Step through code with debugger
  python saral.py --debugger myfile.saral  AI auto-debugger (cloud AI analyses fully)
  python saral.py --status                 Check AI availability
  python saral.py --version                Show version info
  python saral.py --help                   Show this help
"""

import sys
import os

# Add the directory containing this file to sys.path so all compiler modules are found
_core_dir = os.path.dirname(os.path.abspath(__file__))
if _core_dir not in sys.path:
    sys.path.insert(0, _core_dir)
import tempfile
import re

from pipeline import compile_saral
try:
    from errors import classify_runtime_error, compile_error, display_error
    _RICH_ERRORS = True
except ImportError:
    _RICH_ERRORS = False

# ─────────────────────────────────────────────
# VERSION
# ─────────────────────────────────────────────

VERSION       = "1.1.0"
VERSION_DATE  = "2026-06-19"
VERSION_NAME  = "AI Auto-Debugger Release"   # release name

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

BANNER = f"""
╔══════════════════════════════════════════════╗
║   🌿  SARAL  v{VERSION}  "{VERSION_NAME}"    ║
║   Simple programming for everyone            ║
║   Write code the way you think               ║
╚══════════════════════════════════════════════╝
"""

HELP_TEXT = """
USAGE:
  python saral.py <file.saral>              Run a program
  python saral.py --interactive             Type code line by line
  python saral.py --generate               Let AI write code for you
  python saral.py --explain <file.saral>   Explain what code does
  python saral.py --check <file.saral>     Check for errors without running
  python saral.py --show <file.saral>      See the Python code Saral generates
  python saral.py --debug <file.saral>     Step through code with debugger
  python saral.py --debugger <file.saral>  AI auto-debugger (cloud AI analyses everything)
  python saral.py --setup-ai               Connect your AI (paste any API key)
  python saral.py --status                 Check AI availability
  python saral.py --version                Show version info
  python saral.py --help                   Show this help

QUICK EXAMPLES:

  # Hello World
  show "Hello, World!"

  # Variables and math
  store 10 in apples
  store 5 in oranges
  store apples + oranges in total
  show total

  # Conditions
  if total > 12
      show "That is a lot!"
  otherwise
      show "That is fine."
  done

  # Loop
  repeat 5 times
      show "hello"
  done

  # Function
  define greet using name
      show "Hello " + name
  end
  call greet with "Arun"

  # Ask AI
  ask ai "What is the capital of Kerala?" and store in answer
  show answer

RULES:
  - Case insensitive: SHOW = show = Show
  - Use # for comments
  - Use + - * / ^ % for math
  - Use = for equality check inside if

LEARN MORE:
  Read example.saral for a complete working example.
  Run --interactive to try Saral live.
"""


# ─────────────────────────────────────────────
# RUN A .SARAL FILE
# ─────────────────────────────────────────────

def run_file(filepath: str, verbose: bool = False):
    if not os.path.exists(filepath):
        print(f"\n❌  File not found: '{filepath}'")
        print(f"💡  Make sure the file name is correct and ends in .saral\n")
        sys.exit(1)

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            saral_source = f.read()
    except UnicodeDecodeError:
        print(f"\n❌  '{filepath}' contains characters Saral cannot read.")
        print(f"💡  Save the file as UTF-8 and try again.\n")
        sys.exit(1)

    if not saral_source.strip():
        print(f"\n⚠️   '{filepath}' is empty. Nothing to run.\n")
        return

    saral_lines = saral_source.splitlines()

    # compile — keep source_map for accurate runtime error line numbers
    try:
        python_code, source_map, parse_errors = compile_saral(saral_source, filepath)
    except SystemExit:
        # Compile errors were already printed by the pipeline.
        # Give AI a chance to suggest fixes before exiting.
        print("\n🤖  Asking AI to help fix these compile errors...\n")
        try:
            from ai_helper import fix_error
            fix = fix_error(saral_source, "Compile/parse errors — program could not be compiled")
            if fix.get("explanation"):
                print(f"📖  What went wrong:\n    {fix['explanation']}\n")
            if fix.get("fix_summary"):
                print(f"🔧  Suggested fix: {fix['fix_summary']}\n")
            if fix.get("fixed_code") and fix["fixed_code"] != saral_source:
                print("── Suggested fixed code ──────────────────")
                print(fix["fixed_code"])
                print("──────────────────────────────────────────")
                try:
                    save = input("\nSave fixed code to file? (yes/no): ").strip().lower()
                    if save in ("yes", "y"):
                        fixed_path = filepath.replace(".saral", "_fixed.saral")
                        with open(fixed_path, "w", encoding="utf-8") as f:
                            f.write(fix["fixed_code"])
                        print(f"✅  Saved as {fixed_path}\n")
                except (KeyboardInterrupt, EOFError):
                    pass
        except Exception:
            pass
        sys.exit(1)

    # If there were parse errors, don't run partial code — invoke AI help instead
    if parse_errors:
        print("\n🤖  Asking AI to help fix these errors...\n")
        try:
            from ai_helper import fix_error
            error_summary = "; ".join(str(e) for e in parse_errors[:5])
            fix = fix_error(saral_source, f"Parse errors: {error_summary}")
            if fix.get("explanation"):
                print(f"📖  What went wrong:\n    {fix['explanation']}\n")
            if fix.get("fix_summary"):
                print(f"🔧  Suggested fix: {fix['fix_summary']}\n")
            if fix.get("fixed_code") and fix["fixed_code"] != saral_source:
                print("── Suggested fixed code ──────────────────")
                print(fix["fixed_code"])
                print("──────────────────────────────────────────")
                try:
                    save = input("\nSave fixed code to file? (yes/no): ").strip().lower()
                    if save in ("yes", "y"):
                        fixed_path = filepath.replace(".saral", "_fixed.saral")
                        with open(fixed_path, "w", encoding="utf-8") as f:
                            f.write(fix["fixed_code"])
                        print(f"✅  Saved as {fixed_path}\n")
                except (KeyboardInterrupt, EOFError):
                    pass
        except Exception:
            pass
        sys.exit(1)

    if verbose:
        print("\n── Generated Python ──────────────────────")
        print(python_code)
        print("──────────────────────────────────────────\n")

    # execute — compile directly from memory, no temp file needed
    try:
        code_obj = compile(python_code, filepath, "exec")
        exec(code_obj, {"__name__": "__main__"})

    except SyntaxError as e:
        print(f"\n❌  Saral generated invalid code (this is a compiler bug).")
        print(f"    Please report this with your .saral file.\n")
        if verbose:
            print(f"    Python error: {e}\n")

    except Exception as e:
        # Use source map for accurate Saral line number
        saral_line = 0
        try:
            if source_map and hasattr(source_map, "extract_from_exception"):
                saral_line = source_map.extract_from_exception(e) or 0
        except Exception:
            pass

        # Use rich error system if available
        if _RICH_ERRORS:
            try:
                report = classify_runtime_error(
                    e, saral_lines, filename=filepath, line_num=saral_line
                )
                display_error(report)
            except Exception:
                print(f"\n❌  Something went wrong:\n    {type(e).__name__}: {e}\n")
        else:
            print(f"\n❌  Something went wrong:\n    {type(e).__name__}: {e}\n")

        # ask AI to help fix
        try:
            from ai_helper import fix_error
            print("\n🤖  Asking AI to help fix this...\n")
            fix = fix_error(saral_source, str(e))
            if fix.get("explanation"):
                print(f"📖  What went wrong:\n    {fix['explanation']}\n")
            if fix.get("fix_summary"):
                print(f"🔧  Fix applied: {fix['fix_summary']}\n")
            if fix.get("fixed_code") and fix["fixed_code"] != saral_source:
                print("── Suggested fixed code ──────────────────")
                print(fix["fixed_code"])
                print("──────────────────────────────────────────")
                save = input("\nSave fixed code to file? (yes/no): ").strip().lower()
                if save in ("yes", "y"):
                    fixed_path = filepath.replace(".saral", "_fixed.saral")
                    with open(fixed_path, "w", encoding="utf-8") as f:
                        f.write(fix["fixed_code"])
                    print(f"✅  Saved as {fixed_path}\n")
        except Exception:
            pass

        # Auto-launch AI debugger for deep analysis
        print("\n🐛  Auto-launching AI Debugger for full analysis...\n")
        print("    (Note: your program will be re-run inside the debugger)")
        try:
            from debugger import run_debugger_ai
            run_debugger_ai(filepath)
        except ImportError:
            print("  (debugger.py not found — reinstall Saral to enable auto-debugging)\n")
        except Exception as _de:
            print(f"  (Auto-debugger could not start: {_de})\n")


# ─────────────────────────────────────────────
# CHECK (validate without running)
# ─────────────────────────────────────────────

def check_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"\n❌  File not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        saral_source = f.read()

    lines     = saral_source.splitlines()
    errors    = []
    warnings  = []

    print(f"\n🔍  Checking '{filepath}'...\n")

    # check 1: try to compile
    try:
        python_code, _, _ = compile_saral(saral_source, filepath)
    except SystemExit:
        print("❌  Compiler error — see message above.\n")
        return

    # check 2: compile the generated Python
    try:
        compile(python_code, "<saral>", "exec")
    except SyntaxError as e:
        errors.append(f"Syntax error in generated code: {e}")

    # check 3: lint Saral source for common mistakes
    for i, line in enumerate(lines, 1):
        stripped = line.strip().lower()

        # warn about common Python habits
        if re.match(r'^print\s*\(', stripped):
            warnings.append(f"Line {i}: Use 'show' instead of 'print()'")
        if re.match(r'^\w+\s*=\s*\S', stripped) and not stripped.startswith(("store", "if", "set", "#")):
            warnings.append(f"Line {i}: Use 'store value in variable' instead of 'variable = value'")
        if stripped.startswith("input("):
            warnings.append(f"Line {i}: Use 'ask \"...\" and store in variable' instead of 'input()'")

        # warn about unclosed blocks
        if stripped in ("if", "repeat", "for", "while", "define", "try"):
            warnings.append(f"Line {i}: Block opened — make sure it has a matching 'done' or 'end'")

    # report
    if errors:
        print(f"❌  {len(errors)} error(s) found:\n")
        for e in errors:
            print(f"    • {e}")
    else:
        print(f"✅  No errors found.")

    if warnings:
        print(f"\n⚠️   {len(warnings)} warning(s):\n")
        for w in warnings:
            print(f"    • {w}")

    # line count
    non_blank = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
    print(f"\n📊  {len(lines)} total lines, {non_blank} code lines.")
    print()


# ─────────────────────────────────────────────
# SHOW GENERATED PYTHON
# ─────────────────────────────────────────────

def show_python(filepath: str):
    if not os.path.exists(filepath):
        print(f"\n❌  File not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        saral_source = f.read()

    python_code, _, _ = compile_saral(saral_source, filepath)

    print("\n── Saral Source ──────────────────────────")
    for i, line in enumerate(saral_source.splitlines(), 1):
        print(f"  {i:3}  {line}")
    print("\n── Generated Python ──────────────────────")
    for i, line in enumerate(python_code.splitlines(), 1):
        print(f"  {i:4}  {line}")
    print("──────────────────────────────────────────\n")


# ─────────────────────────────────────────────
# EXPLAIN CODE (AI)
# ─────────────────────────────────────────────

def explain_file(filepath: str):
    if not os.path.exists(filepath):
        print(f"\n❌  File not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        saral_source = f.read()

    print(f"\n📖  Explaining '{filepath}'...\n")

    try:
        from ai_helper import explain_code
        explanation = explain_code(saral_source)
        print(explanation)
        print()
    except ImportError:
        print("❌  ai_helper.py not found.\n")


# ─────────────────────────────────────────────
# AI STATUS
# ─────────────────────────────────────────────

def show_status():
    print(BANNER)
    print("🔍  Checking AI availability...\n")

    try:
        from ai_helper import check_ai_status
        status = check_ai_status()

        if status["configured"]:
            print(f"  ✅  AI configured:    {status['provider_name']}")
            print(f"      Model:            {status['model']}")
            print(f"  ✅  Pattern matching: Always available")
            print()
            print("  To change your AI:  python saral.py --setup-ai")
        else:
            print("  ❌  No AI configured yet.")
            print(f"  ✅  Pattern matching: Always available")
            print()
            print("  To set up AI:       python saral.py --setup-ai")
            print("  Supports:           OpenAI, DeepSeek, Gemini, Groq,")
            print("                      Anthropic, Mistral, Cohere, xAI Grok")
            print()
            print("  Just paste your API key — Saral detects the provider")
            print("  automatically and tests the connection for you.")

    except ImportError:
        print("❌  ai_helper.py not found.\n")

    print()


# ─────────────────────────────────────────────
# VERSION
# ─────────────────────────────────────────────

def show_version():
    print(f"\n🌿  Saral v{VERSION} \"{VERSION_NAME}\"")
    print(f"    Released: {VERSION_DATE}")
    print(f"    Python:   {sys.version.split()[0]}")
    print(f"    Platform: {sys.platform}")
    print()


# ─────────────────────────────────────────────
# AI GENERATE MODE
# ─────────────────────────────────────────────

def ai_generate_mode():
    print(BANNER)
    print("🤖  AI Code Generator")
    print("    Describe what you want in plain English.")
    print("    Type 'quit' to exit.\n")

    try:
        from ai_helper import generate_code, validate_generated_code
    except ImportError:
        print("❌  ai_helper.py not found.\n")
        sys.exit(1)

    while True:
        try:
            description = input("What should your program do?\n> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if description.lower() in ("quit", "exit", "bye"):
            print("Goodbye!")
            break

        if not description:
            continue

        print("\n⏳  Generating Saral code...\n")
        code = generate_code(description)

        print("── Generated Saral Code ──────────────────")
        print(code)
        print("──────────────────────────────────────────")

        # ── Validate the generated code against the Saral compiler ──
        is_valid, val_errors = validate_generated_code(code)
        if is_valid:
            print("✅  Validated: uses only valid Saral syntax.\n")
        else:
            print("⚠️   Some lines may not be valid Saral syntax:")
            for ve in val_errors[:5]:
                print(f"    • {ve}")
            print("    Edit the code or type 'new' to try a different description.\n")

        action = input("What next? (run / save / explain / new / quit): ").strip().lower()

        if action in ("run", "r"):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".saral", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(code)
                tmp_path = tmp.name
            print()
            try:
                run_file(tmp_path)
            finally:
                try: os.unlink(tmp_path)
                except Exception: pass

        elif action in ("save", "s"):
            fname = input("File name (without .saral): ").strip()
            if fname:
                safe_name = re.sub(r'[^\w\-]', '_', os.path.basename(fname)).strip('_')
                if not safe_name:
                    print("  ❌  Invalid filename.\n")
                else:
                    fpath = f"{safe_name}.saral"
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(code)
                    print(f"✅  Saved as {fpath}\n")

        elif action in ("explain", "e"):
            try:
                from ai_helper import explain_code
                print("\n📖  Explanation:\n")
                print(explain_code(code))
                print()
            except ImportError:
                pass

        print()


# ─────────────────────────────────────────────
# INTERACTIVE / REPL MODE
# ─────────────────────────────────────────────

def interactive_mode():
    # Enable arrow key history if readline is available
    try:
        import readline
        import atexit, os
        hist_file = os.path.join(os.path.expanduser("~"), ".saral_history")
        try:
            readline.read_history_file(hist_file)
        except FileNotFoundError:
            pass
        atexit.register(readline.write_history_file, hist_file)
        readline.set_history_length(500)
    except ImportError:
        pass  # readline not available on Windows — graceful fallback

    print(BANNER)
    print("📝  Interactive Mode")
    print("    Type Saral code line by line.")
    print()
    print("    Commands:")
    print("      run      — Execute your code")
    print("      show     — See your code so far")
    print("      clear    — Start over")
    print("      explain  — AI explains your code")
    print("      check    — Validate without running")
    print("      save     — Save code to a file")
    print("      hint     — Get AI suggestion for next line")
    print("      quit     — Exit")
    print()

    buffer = []

    while True:
        try:
            # show line number prompt
            line_num = len(buffer) + 1
            line = input(f"saral {line_num:3}> ").rstrip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        cmd = line.strip().lower()

        # ── Commands ──────────────────────────

        if cmd == "quit":
            print("Goodbye!")
            break

        elif cmd == "clear":
            buffer = []
            print("✅  Cleared.\n")

        elif cmd == "show":
            if buffer:
                print("\n── Your code ─────────────────────────────")
                for i, l in enumerate(buffer, 1):
                    print(f"  {i:3}  {l}")
                print("──────────────────────────────────────────\n")
            else:
                print("  (nothing written yet)\n")

        elif cmd == "run":
            if not buffer:
                print("  Nothing to run yet.\n")
                continue
            source = "\n".join(buffer)
            print("\n── Running ────────────────────────────────")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".saral", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(source)
                tmp_path = tmp.name
            try:
                run_file(tmp_path)
                print("───────────────────────────────────────────\n")
            finally:
                try: os.unlink(tmp_path)
                except Exception: pass

        elif cmd == "check":
            if not buffer:
                print("  Nothing to check yet.\n")
                continue
            source = "\n".join(buffer)
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".saral", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(source)
                tmp_path = tmp.name
            try:
                check_file(tmp_path)
            finally:
                try: os.unlink(tmp_path)
                except Exception: pass

        elif cmd == "explain":
            if not buffer:
                print("  Nothing to explain yet.\n")
                continue
            try:
                from ai_helper import explain_code
                source = "\n".join(buffer)
                print("\n📖  AI Explanation:\n")
                print(explain_code(source))
                print()
            except ImportError:
                print("❌  ai_helper.py not found.\n")

        elif cmd == "hint":
            try:
                from ai_helper import autocomplete
                context  = "\n".join(buffer)
                hints    = autocomplete(context, "")
                if hints:
                    print("\n💡  Suggestions for next line:")
                    for i, h in enumerate(hints, 1):
                        print(f"    {i}. {h}")
                    print()
                else:
                    print("  No suggestions available.\n")
            except ImportError:
                print("❌  ai_helper.py not found.\n")

        elif cmd == "save":
            if not buffer:
                print("  Nothing to save yet.\n")
                continue
            fname = input("File name (without .saral): ").strip()
            if fname:
                safe_name = re.sub(r'[^\w\-]', '_', os.path.basename(fname)).strip('_')
                if not safe_name:
                    print("  ❌  Invalid filename.\n")
                else:
                    fpath = f"{safe_name}.saral"
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write("\n".join(buffer))
                    print(f"✅  Saved as {fpath}\n")

        elif cmd == "":
            buffer.append("")

        else:
            # regular code line
            buffer.append(line)

            # inline hints for common mistakes
            stripped = line.strip().lower()
            if re.match(r'^print\s*[\(\"]', stripped):
                print('  💡  Hint: use  show "message"  instead of print()')
            elif re.match(r'^\w+\s*=\s*\S', stripped) and not stripped.startswith(("store", "if", "set", "#")):
                parts = stripped.split("=", 1)
                print(f'  💡  Hint: use  store {parts[1].strip()} in {parts[0].strip()}')
            elif stripped.startswith("input("):
                print('  💡  Hint: use  ask "your question" and store in variable_name')

            # autocomplete hint (pattern-based only, instant)
            try:
                from ai_helper import _pattern_autocomplete
                context   = "\n".join(buffer[:-1])
                hints     = _pattern_autocomplete(stripped[:3], context)
                if hints and len(stripped) <= 3:
                    print(f"  💡  Completing: {hints[0]}")
            except ImportError:
                pass


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(BANNER)
        print(HELP_TEXT)
        return

    if "--version" in args or "-v" in args:
        show_version()
        return

    if "--status" in args:
        show_status()
        return

    if "--setup-ai" in args:
        try:
            from ai_config import run_setup_wizard
            run_setup_wizard()
        except ImportError:
            print("❌  ai_config.py not found. Please reinstall Saral.\n")
        return

    if "--generate" in args or "--gen" in args:
        ai_generate_mode()
        return

    if "--interactive" in args or "--repl" in args or "-i" in args:
        interactive_mode()
        return

    if "--show" in args:
        idx = args.index("--show")
        if idx + 1 < len(args):
            show_python(args[idx + 1])
        else:
            print("❌  Provide a file: python saral.py --show myfile.saral")
        return

    if "--check" in args:
        idx = args.index("--check")
        if idx + 1 < len(args):
            check_file(args[idx + 1])
        else:
            print("❌  Provide a file: python saral.py --check myfile.saral")
        return

    if "--explain" in args:
        idx = args.index("--explain")
        if idx + 1 < len(args):
            explain_file(args[idx + 1])
        else:
            print("❌  Provide a file: python saral.py --explain myfile.saral")
        return

    if "--debugger" in args:
        remaining = [a for a in args if not a.startswith("--")]
        if remaining:
            try:
                from debugger import run_debugger_ai
                run_debugger_ai(remaining[0])
            except ImportError:
                print("❌  debugger.py not found. Please reinstall Saral.\n")
        else:
            print("❌  Provide a file: python saral.py --debugger myfile.saral")
        return

    if "--debug" in args:
        remaining = [a for a in args if not a.startswith("--")]
        if remaining:
            try:
                from debugger import run_debugger
                run_debugger(remaining[0])
            except ImportError:
                print("❌  debugger.py not found. Please reinstall Saral.\n")
        else:
            print("❌  Provide a file: python saral.py --debug myfile.saral")
        return

    # default: run the file
    verbose = "--verbose" in args
    positional = [a for a in args if not a.startswith("--")]
    if not positional:
        print("❌  No file specified. Usage: python saral.py myfile.saral\n")
        return
    filepath = positional[0]

    if not filepath.endswith(".saral"):
        print(f"\n⚠️   '{filepath}' doesn't end in .saral")
        print("    Saral programs should be named like: myprogram.saral\n")

    run_file(filepath, verbose=verbose)


if __name__ == "__main__":
    main()
