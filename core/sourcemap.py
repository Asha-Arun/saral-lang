"""
sourcemap.py — Saral Source Map v4.0
Maps every Python line back to its original Saral line.
Used by the error system to show exact Saral line on runtime errors.
"""

import re
import traceback
from typing import Dict, Optional, List


class SourceMap:
    """
    Bidirectional mapping between Python lines and Saral lines.
    Built by codegen.py during code generation.
    Used by the error system during runtime.
    """

    def __init__(self, py_to_saral: Dict[int, int],
                 saral_lines: List[str],
                 filename: str = "<program>"):
        self.py_to_saral  = py_to_saral        # {python_line → saral_line}
        self.saral_to_py  = {}                  # {saral_line → python_line}
        self.saral_lines  = saral_lines
        self.filename     = filename

        # build reverse map
        for py_line, saral_line in py_to_saral.items():
            if saral_line not in self.saral_to_py:
                self.saral_to_py[saral_line] = py_line

    def saral_line_for(self, python_line: int) -> Optional[int]:
        """
        Given a Python line number, return the Saral line number.
        Returns None if not found.
        """
        # exact match
        if python_line in self.py_to_saral:
            return self.py_to_saral[python_line]

        # search backwards for nearest mapped line
        for offset in range(1, 20):
            candidate = python_line - offset
            if candidate in self.py_to_saral:
                return self.py_to_saral[candidate]

        return None

    def saral_source(self, saral_line: int) -> str:
        """Return the original Saral source line."""
        if 0 < saral_line <= len(self.saral_lines):
            return self.saral_lines[saral_line - 1]
        return ""

    def context_lines(self, saral_line: int,
                      before: int = 2) -> List[tuple]:
        """
        Return context lines around the error.
        Returns list of (line_num, source_text) tuples.
        """
        lines = []
        start = max(1, saral_line - before)
        for i in range(start, saral_line):
            lines.append((i, self.saral_source(i)))
        return lines

    def extract_from_traceback(self, tb) -> Optional[int]:
        """
        Extract Python line number from a traceback object,
        then map to Saral line.
        """
        frames = traceback.extract_tb(tb)
        for frame in reversed(frames):
            saral_line = self.saral_line_for(frame.lineno)
            if saral_line:
                return saral_line
        return None

    def extract_from_exception(self, err: Exception) -> Optional[int]:
        """Get Saral line number from an exception."""
        tb = err.__traceback__
        if tb:
            return self.extract_from_traceback(tb)
        return None


# ─────────────────────────────────────────────
# RUNTIME ERROR LOCATOR
# Integrates with errors.py for precise messages
# ─────────────────────────────────────────────

def locate_error(err: Exception,
                 source_map: SourceMap,
                 source_lines: List[str],
                 filename: str = "<program>") -> dict:
    """
    Given a runtime exception and source map, produce
    a complete error location report:
    {
        saral_line:   int,
        saral_source: str,
        context:      List[(int, str)],
        python_line:  int,
        error_type:   str,
        error_msg:    str,
    }
    """
    error_type = type(err).__name__
    error_msg  = str(err)

    # get Python line from traceback
    python_line = 0
    tb = err.__traceback__
    if tb:
        frames = traceback.extract_tb(tb)
        for frame in reversed(frames):
            if frame.lineno:
                python_line = frame.lineno
                break

    # map to Saral line
    saral_line = source_map.saral_line_for(python_line) if python_line else 0

    # if no map entry found, try to find by error content
    if not saral_line:
        saral_line = _guess_saral_line(error_msg, source_lines)

    saral_line  = max(1, saral_line or 1)
    saral_src   = source_map.saral_source(saral_line)
    context     = source_map.context_lines(saral_line)

    return {
        "saral_line":   saral_line,
        "saral_source": saral_src,
        "context":      context,
        "python_line":  python_line,
        "error_type":   error_type,
        "error_msg":    error_msg,
    }


def _guess_saral_line(error_msg: str,
                      source_lines: List[str]) -> int:
    """
    When source map doesn't have an entry,
    search Saral source for the variable/value in the error.
    """
    # NameError: extract variable name
    m = re.search(r"name '(\w+)' is not defined", error_msg)
    if m:
        var = m.group(1)
        for i, line in enumerate(source_lines, 1):
            if var in line:
                return i

    # FileNotFoundError: extract filename
    m = re.search(r"'(.+?)'", error_msg)
    if m:
        fname = m.group(1)
        for i, line in enumerate(source_lines, 1):
            if fname in line:
                return i

    return 1


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from parser  import parse
    from codegen import generate
    from analyzer import analyze

    test_src = """
store 10 in price
store price * 2 in double_price
show "Price is: {price}"

if price > 5
    show "expensive"
otherwise
    show "cheap"
done

make list called items
add "bread" to items
add "cake" to items
for each item in items
    show item
done

define greet using name
    show "Hello " + name
end

call greet with "Arun"
store today in date
show date
show undefined_variable
"""

    # Full pipeline
    src_lines = test_src.splitlines()
    ast, parse_errors = parse(test_src, "test.saral")

    if parse_errors:
        print("Parse errors:", parse_errors)
    else:
        print(f"✅  Parse: {len(ast.body)} statements")

    table, warnings = analyze(ast, src_lines)
    print(f"✅  Analyze: {len(warnings)} warnings")

    python_code, py_to_saral = generate(ast, src_lines, "test.saral")
    print(f"✅  Generate: {len(python_code.splitlines())} Python lines")
    print(f"✅  Source map: {len(py_to_saral)} entries")

    smap = SourceMap(py_to_saral, src_lines, "test.saral")

    # Show source map
    print("\n── Source Map (Python → Saral) ───────────")
    for py_ln in sorted(smap.py_to_saral.keys())[:15]:
        saral_ln = smap.py_to_saral[py_ln]
        saral_src = smap.saral_source(saral_ln).strip()
        print(f"  Python {py_ln:4} → Saral {saral_ln:3}  |  {saral_src}")

    # Simulate a runtime error
    print("\n── Runtime Error Simulation ──────────────")
    try:
        exec(compile(python_code, "test.saral", "exec"), {})
    except Exception as e:
        loc = locate_error(e, smap, src_lines, "test.saral")
        print(f"Error type:   {loc['error_type']}")
        print(f"Error msg:    {loc['error_msg']}")
        print(f"Python line:  {loc['python_line']}")
        print(f"Saral line:   {loc['saral_line']}")
        print(f"Saral source: {loc['saral_source'].strip()}")
        if loc['context']:
            print("Context:")
            for ln, src in loc['context']:
                print(f"  {ln:3}: {src}")
