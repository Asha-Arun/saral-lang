"""
pipeline.py — Saral v4.0 Complete Pipeline
Replaces transpiler.py with proper parser-based compilation.
Interface is backwards compatible with existing saral.py.
"""

import re
import sys
import tempfile
import os
from typing import List, Tuple, Dict, Optional

from lexer     import tokenize
from parser    import parse  as _parse
from codegen   import generate, STDLIB
from analyzer  import analyze, format_warnings
from sourcemap import SourceMap, locate_error

try:
    from errors import (
        compile_error, classify_runtime_error,
        display_error, display_warning, SaralErrorReport
    )
    _RICH_ERRORS = True
except ImportError:
    _RICH_ERRORS = False


# ─────────────────────────────────────────────
# MAIN COMPILE FUNCTION
# Source → Python + SourceMap + Warnings
# ─────────────────────────────────────────────

def compile_saral(source: str,
                  filename: str = "<program>",
                  show_warnings: bool = True) -> Tuple[str, SourceMap, list]:
    """
    Full v4.0 pipeline:
      source → tokens → AST → analyzed AST → Python + SourceMap

    Returns:
      (python_code, source_map, parse_errors)

    Raises SystemExit on fatal parse errors.
    """
    source_lines = source.splitlines()

    # ── 1. Parse ──────────────────────────────
    ast, parse_errors = _parse(source, filename)

    if parse_errors:
        # Show each parse error with rich formatting if available
        for err_msg in parse_errors:
            # extract line number from "Line N: message"
            m = re.match(r"Line (\d+): (.+)", err_msg)
            if m and _RICH_ERRORS:
                ln  = int(m.group(1))
                msg = m.group(2)
                try:
                    report = compile_error(ln, msg, source_lines, filename)
                    display_error(report)
                except Exception:
                    print(f"\n❌  {err_msg}\n")
            else:
                print(f"\n❌  {err_msg}\n")

        if not ast.body:
            sys.exit(1)

    # ── 2. Analyze ────────────────────────────
    table, warnings = analyze(ast, source_lines, filename)

    if show_warnings and warnings:
        # Only show actual warnings (not info-level)
        real_warnings = [w for w in warnings if w.severity == "warning"]
        if real_warnings:
            print(format_warnings(real_warnings, source_lines))

    # ── 3. Generate ───────────────────────────
    python_code, py_to_saral = generate(ast, source_lines, filename)

    # ── 4. Build source map ───────────────────
    smap = SourceMap(py_to_saral, source_lines, filename)

    return python_code, smap, parse_errors


# ─────────────────────────────────────────────
# RUN FUNCTION
# Compiles and executes a Saral program
# ─────────────────────────────────────────────

def run_saral(source: str,
              filename: str = "<program>",
              show_warnings: bool = True,
              verbose: bool = False) -> bool:
    """
    Compile and run a Saral program.
    Returns True on success, False on error.
    """
    source_lines = source.splitlines()

    # Compile
    try:
        python_code, smap, parse_errors = compile_saral(
            source, filename, show_warnings
        )
    except SystemExit:
        return False

    if verbose:
        print("\n── Generated Python ──────────────────────")
        print(python_code)
        print("──────────────────────────────────────────\n")

    # Write to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py",
        delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write(python_code)
        tmp_path = tmp.name

    # Execute
    try:
        with open(tmp_path, encoding="utf-8") as f:
            code_obj = compile(f.read(), tmp_path, "exec")
        exec(code_obj, {"__name__": "__main__"})
        return True

    except SyntaxError as e:
        print(f"\n❌  Saral generated invalid code — this is a compiler bug.")
        print(f"    Please report your .saral file.")
        print(f"    Python error: {e}\n")
        return False

    except Exception as e:
        # Use source map for precise error location
        loc = locate_error(e, smap, source_lines, filename)

        if _RICH_ERRORS:
            try:
                # build a rich report with exact location
                report = classify_runtime_error(
                    e, source_lines, filename, loc["saral_line"]
                )
                display_error(report)
            except Exception:
                _plain_error(e, loc)
        else:
            _plain_error(e, loc)

        # AI fix attempt
        try:
            from ai_helper import fix_error
            print("\n🤖  Asking AI to help fix this...\n")
            fix = fix_error(source, str(e))
            if fix.get("explanation"):
                print(f"📖  What went wrong:\n    {fix['explanation']}\n")
            if fix.get("fix_summary"):
                print(f"🔧  Fix: {fix['fix_summary']}\n")
        except Exception:
            pass

        return False

    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def _plain_error(err: Exception, loc: dict):
    """Plain text error display (fallback)."""
    print(f"\n❌  Error on line {loc['saral_line']}: {loc['error_msg']}")
    if loc['saral_source']:
        print(f"    {loc['saral_source'].strip()}")
    print()


# ─────────────────────────────────────────────
# SHOW PYTHON (debug)
# ─────────────────────────────────────────────

def show_python(source: str, filename: str = "<program>"):
    """Show generated Python code with source mapping."""
    python_code, smap, _ = compile_saral(source, filename, show_warnings=False)

    print("\n── Saral Source ──────────────────────────")
    for i, line in enumerate(source.splitlines(), 1):
        print(f"  {i:3}  {line}")

    print("\n── Generated Python ──────────────────────")
    py_lines = python_code.splitlines()
    for i, line in enumerate(py_lines, 1):
        saral_ln = smap.py_to_saral.get(i, "")
        marker   = f"← Saral {saral_ln}" if saral_ln else ""
        print(f"  {i:4}  {line:<50}  {marker}")
    print("──────────────────────────────────────────\n")


# ─────────────────────────────────────────────
# CHECK (validate without running)
# ─────────────────────────────────────────────

def check_saral(source: str, filename: str = "<program>") -> bool:
    """
    Validate Saral source without running it.
    Returns True if no errors found.
    """
    source_lines = source.splitlines()
    errors       = []
    warnings_out = []

    print(f"\n🔍  Checking '{filename}'...\n")

    # Parse
    ast, parse_errors = _parse(source, filename)
    if parse_errors:
        for e in parse_errors:
            errors.append(e)

    # Analyze
    if ast.body:
        table, warnings = analyze(ast, source_lines, filename)
        for w in warnings:
            if w.severity == "warning":
                warnings_out.append(str(w))

    # Try to compile generated Python
    if ast.body:
        try:
            python_code, _, _ = compile_saral(
                source, filename, show_warnings=False
            )
            compile(python_code, filename, "exec")
        except SyntaxError as e:
            errors.append(f"Generated code syntax error: {e}")
        except SystemExit:
            pass

    # Report
    if errors:
        print(f"❌  {len(errors)} error(s):\n")
        for e in errors:
            print(f"    • {e}")
    else:
        print("✅  No errors found.")

    if warnings_out:
        print(f"\n⚠️   {len(warnings_out)} warning(s):\n")
        for w in warnings_out:
            print(f"    • {w}")

    # Stats
    non_blank = sum(
        1 for l in source_lines
        if l.strip() and not l.strip().startswith("#")
    )
    print(f"\n📊  {len(source_lines)} lines total, {non_blank} code lines.\n")
    return len(errors) == 0


# ─────────────────────────────────────────────
# BACKWARDS COMPATIBILITY
# Drop-in replacement for transpiler.py functions
# ─────────────────────────────────────────────

def transpile(source: str) -> str:
    """
    Backwards compatible wrapper.
    Returns Python source string (like old transpiler.py).
    """
    python_code, _, _ = compile_saral(source, show_warnings=False)
    return python_code


def format_runtime_error(err: Exception, saral_lines: list) -> str:
    """Backwards compatible wrapper for old runtime error format."""
    err_type = type(err).__name__
    err_msg  = str(err)
    msg = "\n❌  Something went wrong:\n"
    msg += f"    {err_type}: {err_msg}\n"
    return msg


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_src = """
# Full v4.0 pipeline test
store 10 in price
store price * 2 in double_price
show "Price: {price}, Double: {double_price}"

if price > 5 and price < 100
    show "in range" in green
otherwise
    show "out of range" in red
done

make list called names
add "bread" to names
add "cake" to names
add "pastry" to names
sort names
for each item in names
    show item
done

make list called prices
add 20 to prices
add 150 to prices
add 75 to prices
store sum of prices in total
show total

define greet using name, title = "Mr"
    global price
    show "Hello " + title + " " + name + " — price is " + price as text
end

call greet with "Arun"
store result of greet with "Team" in msg

store today in date
show "Today: {date}"

store sqrt of 144 in sq
store round of 3.14159 to 3 places in pi
show "sqrt(144) = {sq}, pi ≈ {pi}"

make dictionary called person
set "name" of person to "Arun"
set "city" of person to "Irinjalakuda"
store value of "city" in person in city
show "City: {city}"

try
    store 10 / 0 in bad
catch
    show "Caught: division by zero" in yellow
done

check that "arun@bakesmart.com" is valid email and store in ok
show ok

store text block in note
This is a multiline
text block in Saral v4.0.
It preserves all content.
end block
show note

show "── All tests complete ✅" in bold
"""

    print("Testing Saral v4.0 complete pipeline...")
    print("=" * 50)
    success = run_saral(test_src, "pipeline_test.saral")
    print("=" * 50)
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
