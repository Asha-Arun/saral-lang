"""
errors.py — Saral v3.1 Production Error System

Features:
  - Error codes (E001-E020) for documentation and searchability
  - Code snippets with line/column pointers
  - Plain English suggestions
  - Educational explanations
  - ANSI colors (zero external dependencies)
  - Original source preservation (not normalized)
  - Designed for future Malayalam/multilingual translation
"""

import os
import re
import sys
from dataclasses import dataclass, field
from typing import Optional, List


# ─────────────────────────────────────────────
# ANSI COLORS (zero dependencies)
# ─────────────────────────────────────────────

class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    BLUE    = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN    = "\033[96m"
    WHITE   = "\033[97m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"

def _c(text: str, *codes) -> str:
    """Apply ANSI color codes to text."""
    return "".join(codes) + text + C.RESET


# ─────────────────────────────────────────────
# ERROR CODES
# ─────────────────────────────────────────────

ERROR_CODES = {
    "E001": "Unknown keyword or command",
    "E002": "Variable used before it was stored",
    "E003": "Block not closed (missing done or end)",
    "E004": "Type mismatch (mixing text and numbers)",
    "E005": "File not found",
    "E006": "Invalid regular expression pattern",
    "E007": "Wrong number of return values",
    "E008": "Unexpected block closer (done/end without opener)",
    "E009": "Division by zero",
    "E010": "Multiline block not closed (missing end block)",
    "E011": "List index out of range",
    "E012": "Dictionary key not found",
    "E013": "Invalid number conversion",
    "E014": "Function not defined",
    "E015": "Cannot import library",
    "E016": "Network/fetch error",
    "E017": "CSV read/write error",
    "E018": "JSON parse error",
    "E019": "Permission denied on file operation",
    "E020": "General runtime error",
}


# ─────────────────────────────────────────────
# SARAL ERROR CLASS
# ─────────────────────────────────────────────

@dataclass
class SaralErrorReport:
    code:        str
    message:     str
    line_num:    int
    col_num:     int              = 0
    filename:    str              = "<program>"
    source_line: str              = ""
    context:     List[str]        = field(default_factory=list)
    suggestions: List[str]        = field(default_factory=list)
    explanation: Optional[str]    = None
    severity:    str              = "error"   # "error" or "warning"

    def format(self) -> str:
        lines = []
        width = 60

        # ── Header ──────────────────────────────────────────
        if self.severity == "error":
            icon  = "❌"
            color = C.RED
        else:
            icon  = "⚠️ "
            color = C.YELLOW

        code_desc = ERROR_CODES.get(self.code, "Unknown error")
        lines.append("")
        lines.append(_c(f"{icon}  [{self.code}] {self.message}", C.BOLD, color))
        lines.append(_c(f"     {code_desc}", C.DIM))
        lines.append("")

        # ── File + location ──────────────────────────────────
        loc = f"  --> {self.filename}:{self.line_num}"
        if self.col_num:
            loc += f":{self.col_num}"
        lines.append(_c(loc, C.CYAN))

        # ── Code snippet with pointer ────────────────────────
        if self.context or self.source_line:
            lines.append(_c("   |", C.DIM))

            # show context lines before
            ctx_lines = self.context or []
            for ctx_line in ctx_lines:
                parts = ctx_line.split(":", 1)
                if len(parts) == 2:
                    lno  = parts[0].strip().rjust(3)
                    code = parts[1]
                    lines.append(_c(f" {lno} |", C.DIM) + code)

            # show the error line
            if self.source_line:
                lno    = str(self.line_num).rjust(3)
                lines.append(_c(f" {lno} | ", C.BOLD) + self.source_line.rstrip())
                # pointer arrow
                col    = max(0, self.col_num - 1)
                src    = self.source_line.rstrip()
                space  = " " * (col + 7)  # 7 = len(" NNN | ") visible prefix
                caret  = _c("^" * max(1, len(src) - col), C.BOLD, color)
                lines.append(f"{space}{caret}")
                lines.append("")

        # ── Suggestions ──────────────────────────────────────
        if self.suggestions:
            lines.append(_c("  💡  Did you mean:", C.BOLD, C.GREEN))
            for s in self.suggestions:
                lines.append(_c(f"       • {s}", C.GREEN))
            lines.append("")

        # ── Explanation ──────────────────────────────────────
        if self.explanation:
            lines.append(_c("  📖  Explanation:", C.BOLD, C.BLUE))
            # wrap explanation at 60 chars
            words = self.explanation.split()
            curr  = "     "
            for word in words:
                if len(curr) + len(word) > 65:
                    lines.append(_c(curr, C.BLUE))
                    curr = "     " + word + " "
                else:
                    curr += word + " "
            if curr.strip():
                lines.append(_c(curr.rstrip(), C.BLUE))
            lines.append("")

        return "\n".join(lines)

    def __str__(self):
        return self.format()


# ─────────────────────────────────────────────
# ERROR BUILDER
# Creates rich SaralErrorReport from context
# ─────────────────────────────────────────────

def build_error(
    code:        str,
    message:     str,
    line_num:    int,
    source_lines: List[str],
    filename:    str    = "<program>",
    col_num:     int    = 0,
    severity:    str    = "error",
) -> SaralErrorReport:
    """
    Build a rich error report with code snippet context.
    source_lines: original (non-normalized) source lines.
    """
    # get source line
    src_line = ""
    if 0 < line_num <= len(source_lines):
        src_line = source_lines[line_num - 1]

    # get 2 lines of context before
    context = []
    start   = max(0, line_num - 3)
    for i in range(start, line_num - 1):
        if i < len(source_lines):
            context.append(f"{i+1}: {source_lines[i]}")

    # detect col from source line (first non-space)
    if not col_num and src_line:
        col_num = len(src_line) - len(src_line.lstrip()) + 1

    suggestions, explanation = _suggest_and_explain(code, src_line, source_lines, line_num)

    return SaralErrorReport(
        code        = code,
        message     = message,
        line_num    = line_num,
        col_num     = col_num,
        filename    = filename,
        source_line = src_line,
        context     = context,
        suggestions = suggestions,
        explanation = explanation,
        severity    = severity,
    )


# ─────────────────────────────────────────────
# SUGGESTION ENGINE
# Generates helpful suggestions per error code
# ─────────────────────────────────────────────

def _suggest_and_explain(
    code:         str,
    source_line:  str,
    all_lines:    List[str],
    line_num:     int,
) -> tuple:
    """Return (suggestions_list, explanation_string) for a given error code."""

    stripped = source_line.strip().lower()
    suggestions  = []
    explanation  = ""

    if code == "E001":
        # Unknown keyword — try to guess what they meant
        first_word = stripped.split()[0] if stripped else ""

        typo_map = {
            "pritn":   "show",    "pint":    "show",    "prin":    "show",
            "dispaly": "show",    "display": "show",    "print":   "show",
            "echo":    "show",    "write":   "show",    "output":  "show",
            "input":   'ask "Enter something: " and store in variable',
            "read":    "ask",     "get":     "ask",
            "let":     "store",   "set":     "store",   "var":     "store",
            "int":     "store ... as number in ...",
            "str":     "store ... as text in ...",
            "def":     "define",  "func":    "define",  "function": "define",
            "return":  "return",  "ret":     "return",
            "foreach": "for each item in my_list",
            "loop":    "repeat 5 times",
            "import":  "use math",
        }

        if first_word in typo_map:
            suggestions.append(f'{typo_map[first_word]}')

        # check if it looks like python assignment (single = not ==)
        if "=" in stripped and "==" not in stripped and not stripped.startswith(("store","if","set","#")):
            parts = stripped.split("=", 1)
            suggestions.append(f'store {parts[1].strip()} in {parts[0].strip()}')

        explanation = (
            "Saral did not recognize this command. "
            "Every Saral line must start with a known keyword like "
            "store, show, ask, if, repeat, for, define, make, add, or use."
        )

    elif code == "E002":
        # Variable not found — find similar variable names
        m = re.search(r"'(\w+)'", source_line)
        var_name = m.group(1) if m else ""

        # find all stored variables in lines before this
        stored_vars = []
        for i, l in enumerate(all_lines[:line_num-1]):
            vm = re.match(r'\s*store\s+.+?\s+in\s+(\w+)', l, re.IGNORECASE)
            if vm:
                stored_vars.append(vm.group(1))

        if var_name and stored_vars:
            # find similar names (simple edit distance)
            similar = [v for v in stored_vars if _similar(v, var_name)]
            for v in similar[:3]:
                suggestions.append(f'Did you mean: {v}')

        if var_name:
            suggestions.append(f'store <value> in {var_name}   ← add this before line {line_num}')

        explanation = (
            f"In Saral, you must store a value in a variable before using it. "
            f"Add 'store ... in {var_name}' somewhere before this line."
        )

    elif code == "E003":
        suggestions.append("Make sure every 'if', 'repeat', 'for', 'while', 'define', or 'try' has a matching 'done' or 'end'.")
        explanation = (
            "Saral uses 'done' to close if/repeat/for/while/try blocks, "
            "and 'end' to close define blocks. One of these is missing."
        )

    elif code == "E004":
        suggestions.append("store my_number as text in result   ← convert number to text first")
        suggestions.append("store my_text as number in result   ← convert text to number first")
        explanation = (
            "You tried to mix a number and text together. "
            "Saral cannot add or compare them directly. "
            "Convert one to match the other first."
        )

    elif code == "E005":
        # extract filename from line
        fm = re.search(r'"([^"]+)"', source_line)
        fname = fm.group(1) if fm else "the file"
        suggestions.append(f'Check that "{fname}" exists in the same folder as your .saral file')
        suggestions.append(f'Check the spelling of the file name')
        explanation = (
            f"Saral could not find the file '{fname}'. "
            "Make sure the file exists and the name is spelled correctly."
        )

    elif code == "E009":
        suggestions.append("if divisor != 0\n           store numerator / divisor in result\n       done")
        explanation = (
            "Division by zero is not possible in mathematics. "
            "Always check that the number you are dividing by is not zero before dividing."
        )

    elif code == "E011":
        suggestions.append("store length of my_list in count   ← check list size first")
        suggestions.append("if count >= 3\n           store item 3 of my_list in result\n       done")
        explanation = (
            "You tried to get an item from a list position that does not exist. "
            "Use 'store length of list in count' to check how many items are in the list first."
        )

    elif code == "E012":
        suggestions.append("Check that the key name is spelled correctly")
        suggestions.append("Use: store value of \"key\" in my_dict in result")
        explanation = (
            "The key you are looking for does not exist in the dictionary. "
            "Make sure you used 'set \"key\" of dict to value' before trying to get it."
        )

    elif code == "E013":
        suggestions.append("check that my_variable is a number and store in is_valid")
        suggestions.append("if is_valid\n           store my_variable as number in result\n       done")
        explanation = (
            "Saral could not convert this value to a number. "
            "Make sure the value contains only digits (and optionally a decimal point)."
        )

    elif code == "E014":
        m  = re.search(r"'(\w+)'", source_line)
        fn = m.group(1) if m else "the function"
        suggestions.append(f"define {fn}\n           # your code here\n       end")
        suggestions.append(f"Make sure 'define {fn}' appears before you call it")
        explanation = (
            f"Saral cannot find a function named '{fn}'. "
            "You must define a function with 'define ... end' before you can call it."
        )

    elif code == "E020":
        explanation = (
            "Something unexpected went wrong while running your program. "
            "Check the error message above for clues about what happened."
        )

    return suggestions, explanation


def _similar(a: str, b: str) -> bool:
    """Simple similarity: share 60%+ of characters or one is substring of other."""
    a, b = a.lower(), b.lower()
    if a in b or b in a:
        return True
    common = sum(1 for c in a if c in b)
    return common / max(len(a), len(b), 1) >= 0.6


# ─────────────────────────────────────────────
# RUNTIME ERROR CLASSIFIER
# Maps Python exceptions to Saral error codes
# ─────────────────────────────────────────────

def classify_runtime_error(
    err:          Exception,
    source_lines: List[str],
    filename:     str = "<program>",
    line_num:     int = 0,
) -> SaralErrorReport:
    """
    Convert a Python runtime exception into a rich SaralErrorReport.
    """
    err_type = type(err).__name__
    err_msg  = str(err)

    # map Python exception → Saral error code + message
    mapping = {
        "NameError":         ("E002", f"Variable used before it was stored: {err_msg}"),
        "ZeroDivisionError": ("E009", "You tried to divide by zero"),
        "TypeError":         ("E004", "Type mismatch — you mixed text and numbers"),
        "IndexError":        ("E011", "Tried to get an item that does not exist in the list"),
        "KeyError":          ("E012", f"Dictionary key not found: {err_msg}"),
        "ValueError":        ("E013", f"Invalid value conversion: {err_msg}"),
        "FileNotFoundError": ("E005", f"File not found: {err_msg}"),
        "PermissionError":   ("E019", f"Permission denied: {err_msg}"),
        "AttributeError":    ("E020", f"Internal error: {err_msg}"),
        "ImportError":       ("E015", f"Could not load library: {err_msg}"),
        "ModuleNotFoundError":("E015",f"Library not installed: {err_msg}"),
    }

    code, message = mapping.get(err_type, ("E020", f"Unexpected error: {err_msg}"))

    # try to find line number from traceback
    if not line_num:
        import traceback as _tb_mod
        _frames = _tb_mod.extract_tb(err.__traceback__)
        # Prefer frames whose filename matches the user's file (most accurate)
        for _fi in reversed(_frames):
            if _fi.filename == filename and _fi.lineno:
                try:
                    from codegen import STDLIB as _STDLIB
                    _offset = len(_STDLIB.splitlines())
                except Exception:
                    _offset = 115  # conservative fallback if codegen unavailable
                line_num = max(1, _fi.lineno - _offset)
                break
        # Fallback: use last frame if no matching filename found
        if not line_num:
            for _fi in reversed(_frames):
                if _fi.lineno:
                    try:
                        from codegen import STDLIB as _STDLIB
                        _offset = len(_STDLIB.splitlines())
                    except Exception:
                        _offset = 115
                    line_num = max(1, _fi.lineno - _offset)
                    break

    line_num = max(1, min(line_num, len(source_lines))) if source_lines else 1

    return build_error(
        code         = code,
        message      = message,
        line_num     = line_num,
        source_lines = source_lines,
        filename     = filename,
    )


# ─────────────────────────────────────────────
# COMPILE ERROR BUILDER
# For compiler errors (unknown lines)
# ─────────────────────────────────────────────

def compile_error(
    line_num:     int,
    source_line:  str,
    source_lines: List[str],
    filename:     str = "<program>",
) -> SaralErrorReport:
    """
    Build an E001 compile-time error for an unrecognized Saral line.
    """
    return build_error(
        code         = "E001",
        message      = "I don't understand this line",
        line_num     = line_num,
        source_lines = source_lines,
        filename     = filename,
    )


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

def display_error(report: SaralErrorReport):
    """Print a formatted error report to stderr."""
    print(report.format(), file=sys.stderr)


def display_warning(message: str, line_num: int = 0, filename: str = "<program>"):
    """Print a simple warning."""
    loc = f"{filename}:{line_num}" if line_num else filename
    print(f"\n{_c('⚠️   Warning', C.BOLD, C.YELLOW)} [{_c(loc, C.CYAN)}]: {message}\n")


# ─────────────────────────────────────────────
# BLOCK MISMATCH ERROR
# ─────────────────────────────────────────────

def block_mismatch_error(
    keyword:      str,
    line_num:     int,
    source_lines: List[str],
    filename:     str  = "<program>",
    unclosed:     bool = True,
) -> SaralErrorReport:
    if unclosed:
        msg = f"'{keyword}' block was never closed"
        code = "E003"
    else:
        msg = f"'{keyword}' closes a block that was never opened"
        code = "E008"

    return build_error(
        code         = code,
        message      = msg,
        line_num     = line_num,
        source_lines = source_lines,
        filename     = filename,
        severity     = "warning",
    )
