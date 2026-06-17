"""
debugger.py — Saral Debugger v1.0
A dedicated interactive debugger for Saral Lang programs.

Usage:
  saral --debug myprogram.saral

Commands inside debugger:
  next        — execute next line
  run         — run until breakpoint or end
  vars        — show all variables and values
  break N     — set breakpoint at line N
  watch NAME  — alert when variable NAME changes
  fix         — AI analyses current state and suggests fix
  history     — show all steps taken this session
  save        — save full session log to file
  list        — show source code with line numbers
  where       — show current position in program
  restart     — start over with same file
  help        — show all commands
  quit        — exit debugger

Architecture:
  Uses pipeline.py  — compile Saral → Python + SourceMap
  Uses sourcemap.py — map Python lines ↔ Saral lines
  Uses errors.py    — classify and display errors
  Uses ai_helper.py — AI fix with full session memory (no memory loss)
"""

import sys
import os
import json
import datetime
import traceback

# ─────────────────────────────────────────────
# ANSI COLORS (matches errors.py exactly)
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

def _c(text, *codes):
    return "".join(codes) + str(text) + C.RESET


# ─────────────────────────────────────────────
# DEBUG SESSION
# Holds all state for one debug session.
# Passed to AI so it has full context — solves
# the "AI has no memory" problem completely.
# ─────────────────────────────────────────────

class DebugSession:
    """
    Persistent state for one debug session.
    Everything that happens — steps, variable changes,
    errors, watchpoint hits — is recorded here.
    When AI is asked to help, the full session is
    included in the prompt so it has complete context.
    """

    def __init__(self, filename: str, source: str):
        self.filename       = filename
        self.source         = source
        self.source_lines   = source.splitlines()
        self.start_time     = datetime.datetime.now().isoformat()

        # execution state
        self.current_line   = 0        # current Saral line number
        self.variables      = {}       # {name: value} snapshot at current point
        self.prev_variables = {}       # previous snapshot for watchpoint diff

        # debug controls
        self.breakpoints    = set()    # set of Saral line numbers
        self.watchpoints    = set()    # set of variable names to watch

        # history — full record of everything
        self.steps          = []       # list of step records
        self.errors         = []       # list of error records
        self.watch_hits     = []       # list of watchpoint trigger records
        self.is_finished    = False
        self.had_error      = False

    def record_step(self, line_num: int, source_line: str, variables: dict):
        """Record one step of execution."""
        self.steps.append({
            "line":      line_num,
            "source":    source_line.strip(),
            "variables": dict(variables),
        })
        self.prev_variables = dict(self.variables)
        self.variables      = dict(variables)
        self.current_line   = line_num

    def record_error(self, line_num: int, error_type: str, message: str):
        """Record an error that occurred."""
        self.errors.append({
            "line":    line_num,
            "type":    error_type,
            "message": message,
        })
        self.had_error = True

    def check_watchpoints(self) -> list:
        """
        Compare current variables to previous snapshot.
        Return list of (name, old_value, new_value) for watched variables
        that changed.
        """
        hits = []
        for name in self.watchpoints:
            old = self.prev_variables.get(name, "<not set>")
            new = self.variables.get(name, "<not set>")
            if old != new:
                hits.append((name, old, new))
                self.watch_hits.append({
                    "line":     self.current_line,
                    "variable": name,
                    "old":      old,
                    "new":      new,
                })
        return hits

    def ai_context(self) -> str:
        """
        Build a full context string for the AI.
        This gives the AI complete memory of the session —
        every step, every variable change, every error.
        """
        lines = []
        lines.append(f"SARAL DEBUG SESSION")
        lines.append(f"File: {self.filename}")
        lines.append(f"Started: {self.start_time}")
        lines.append("")

        lines.append("SOURCE CODE:")
        for i, line in enumerate(self.source_lines, 1):
            marker = "→" if i == self.current_line else " "
            lines.append(f"  {marker} {i:3}: {line}")
        lines.append("")

        lines.append(f"CURRENT POSITION: line {self.current_line}")
        if self.current_line and 0 < self.current_line <= len(self.source_lines):
            lines.append(f"CURRENT LINE: {self.source_lines[self.current_line-1].strip()}")
        lines.append("")

        lines.append("CURRENT VARIABLE VALUES:")
        if self.variables:
            for name, val in self.variables.items():
                lines.append(f"  {name} = {repr(val)}")
        else:
            lines.append("  (none yet)")
        lines.append("")

        if self.errors:
            lines.append("ERRORS THAT OCCURRED:")
            for e in self.errors:
                lines.append(f"  Line {e['line']}: [{e['type']}] {e['message']}")
            lines.append("")

        if self.watch_hits:
            lines.append("WATCHPOINT HISTORY:")
            for h in self.watch_hits:
                lines.append(f"  Line {h['line']}: {h['variable']} changed {h['old']} → {h['new']}")
            lines.append("")

        lines.append(f"STEPS EXECUTED: {len(self.steps)}")
        if self.steps:
            lines.append("LAST 5 STEPS:")
            for step in self.steps[-5:]:
                lines.append(f"  Line {step['line']}: {step['source']}")
        lines.append("")

        if self.breakpoints:
            lines.append(f"BREAKPOINTS: {sorted(self.breakpoints)}")
        if self.watchpoints:
            lines.append(f"WATCHPOINTS: {sorted(self.watchpoints)}")

        return "\n".join(lines)

    def to_log(self) -> str:
        """Serialise full session to a readable log string."""
        lines = []
        lines.append("=" * 60)
        lines.append(f"SARAL DEBUG SESSION LOG")
        lines.append(f"File:    {self.filename}")
        lines.append(f"Started: {self.start_time}")
        lines.append(f"Ended:   {datetime.datetime.now().isoformat()}")
        lines.append("=" * 60)
        lines.append("")

        lines.append("SOURCE:")
        for i, src in enumerate(self.source_lines, 1):
            bp = " [BREAK]" if i in self.breakpoints else ""
            lines.append(f"  {i:3}: {src}{bp}")
        lines.append("")

        lines.append("STEPS EXECUTED:")
        for step in self.steps:
            lines.append(f"  Line {step['line']:3}: {step['source']}")
            if step['variables']:
                for k, v in step['variables'].items():
                    lines.append(f"           {k} = {repr(v)}")
        lines.append("")

        if self.errors:
            lines.append("ERRORS:")
            for e in self.errors:
                lines.append(f"  Line {e['line']}: [{e['type']}] {e['message']}")
            lines.append("")

        if self.watch_hits:
            lines.append("WATCHPOINT HITS:")
            for h in self.watch_hits:
                lines.append(
                    f"  Line {h['line']}: {h['variable']} "
                    f"{h['old']} → {h['new']}"
                )

        lines.append("")
        lines.append("FINAL VARIABLES:")
        for k, v in self.variables.items():
            lines.append(f"  {k} = {repr(v)}")

        return "\n".join(lines)


# ─────────────────────────────────────────────
# STEP TRACER
# Uses sys.settrace to intercept every line
# of the generated Python and map back to Saral.
# This is the core engine — no polling needed.
# ─────────────────────────────────────────────

class StepTracer:
    """
    Installs itself as Python's line trace function.
    On every line executed it:
      1. Maps Python line → Saral line via SourceMap
      2. Snapshots all user variables (filters out stdlib internals)
      3. Records the step in the DebugSession
      4. Checks breakpoints and watchpoints
      5. If stopped, drops into the interactive prompt
    """

    # Variables from the Saral stdlib header — filtered out of display
    _STDLIB_VARS = {
        '_s', '_m', '_r', '_o', '_dt', '_j', '_csv', '_re', '_th',
        '_ur', '_tw', '_C', '_color', '_progress', '_ai', '_rf', '_wf',
        '_af', '_rl', '_rcsv', '_wcsv', '_rj', '_wj', '_fetch', '_fetchj',
        '_ask_num', '_pad', '_saral_err', '__name__', '__builtins__',
        '__doc__', '__package__', '__spec__', '__loader__',
    }

    def __init__(self, session: DebugSession, source_map,
                 step_mode: bool = False):
        self.session      = session
        self.source_map   = source_map
        self.step_mode    = step_mode   # True = stop at every line
        self.stopped      = False       # True = waiting at prompt

    def _extract_vars(self, frame_locals: dict) -> dict:
        """Extract only user-defined Saral variables from frame locals."""
        result = {}
        for k, v in frame_locals.items():
            if k in self._STDLIB_VARS:
                continue
            if k.startswith('_'):
                continue
            if callable(v) and not isinstance(v, (int, float, str, list, dict, bool)):
                continue
            try:
                # only keep JSON-serialisable types for clean display
                json.dumps(v)
                result[k] = v
            except (TypeError, ValueError):
                result[k] = str(v)
        return result

    def trace_lines(self, frame, event, arg):
        """Called on every line executed in the generated Python."""
        if event != 'line':
            return self.trace_lines

        py_line    = frame.f_lineno
        saral_line = self.source_map.saral_line_for(py_line)

        if not saral_line:
            return self.trace_lines

        # snapshot variables
        variables  = self._extract_vars(frame.f_locals)

        # record step
        src = ""
        if 0 < saral_line <= len(self.session.source_lines):
            src = self.session.source_lines[saral_line - 1]
        self.session.record_step(saral_line, src, variables)

        # check watchpoints
        hits = self.session.check_watchpoints()
        for name, old, new in hits:
            print()
            print(_c(f"  👁  Watchpoint: ", C.YELLOW, C.BOLD) +
                  _c(name, C.CYAN) +
                  _c(f" changed  {old}", C.DIM) +
                  _c(f" → ", C.YELLOW) +
                  _c(f"{new}", C.GREEN) +
                  _c(f"  (line {saral_line})", C.DIM))
            print(_c("  💡  Type 'fix' for AI analysis  or  'explain' to understand this line.", C.DIM))
            self.stopped = True

        # check breakpoints
        if saral_line in self.session.breakpoints:
            print()
            print(_c(f"  🔴 Breakpoint", C.RED, C.BOLD) +
                  _c(f" hit at line {saral_line}: ", C.RED) +
                  _c(src.strip(), C.WHITE))
            self.stopped = True

        # stop if in step mode or breakpoint/watchpoint triggered
        if self.step_mode or self.stopped:
            self.stopped = False
            self._interactive_prompt(saral_line, src, variables, frame)

        return self.trace_lines

    def _interactive_prompt(self, saral_line: int, src: str,
                            variables: dict, frame):
        """Drop into the interactive debug prompt at current line."""
        _print_current_line(saral_line, src, self.session.source_lines)

        while True:
            try:
                raw = input(_c("debug> ", C.GREEN, C.BOLD)).strip()
            except (KeyboardInterrupt, EOFError):
                print("\n  (use 'quit' to exit)")
                continue

            if not raw:
                continue

            cmd   = raw.split()[0].lower()
            parts = raw.split()

            # ── next ──────────────────────────────
            if cmd in ("next", "n", "step", "s"):
                self.step_mode = True
                return

            # ── run ───────────────────────────────
            elif cmd in ("run", "r", "continue", "c"):
                self.step_mode = False
                return

            # ── vars ──────────────────────────────
            elif cmd in ("vars", "v", "variables"):
                _print_vars(variables)

            # ── break ─────────────────────────────
            elif cmd in ("break", "b", "breakpoint"):
                if len(parts) >= 2:
                    try:
                        ln = int(parts[1])
                        self.session.breakpoints.add(ln)
                        print(_c(f"  🔴 Breakpoint set at line {ln}", C.RED))
                    except ValueError:
                        print("  Usage: break <line number>")
                else:
                    if self.session.breakpoints:
                        print(_c("  Breakpoints: ", C.BOLD) +
                              str(sorted(self.session.breakpoints)))
                    else:
                        print("  No breakpoints set.")

            # ── clear break ───────────────────────
            elif cmd in ("clear",):
                if len(parts) >= 2:
                    try:
                        ln = int(parts[1])
                        self.session.breakpoints.discard(ln)
                        print(f"  Breakpoint at line {ln} removed.")
                    except ValueError:
                        print("  Usage: clear <line number>")
                else:
                    self.session.breakpoints.clear()
                    print("  All breakpoints cleared.")

            # ── watch ─────────────────────────────
            elif cmd in ("watch", "w"):
                if len(parts) >= 2:
                    name = parts[1]
                    self.session.watchpoints.add(name)
                    current_val = variables.get(name, "<not set>")
                    print(_c(f"  👁  Watching: ", C.YELLOW) +
                          _c(name, C.CYAN) +
                          _c(f"  (current: {current_val})", C.DIM))
                else:
                    if self.session.watchpoints:
                        print(_c("  Watching: ", C.BOLD) +
                              str(sorted(self.session.watchpoints)))
                    else:
                        print("  No watchpoints set.")

            # ── unwatch ───────────────────────────
            elif cmd in ("unwatch",):
                if len(parts) >= 2:
                    self.session.watchpoints.discard(parts[1])
                    print(f"  Stopped watching: {parts[1]}")

            # ── list ──────────────────────────────
            elif cmd in ("list", "l", "ls"):
                _print_source(self.session.source_lines,
                              self.session.current_line,
                              self.session.breakpoints)

            # ── where ─────────────────────────────
            elif cmd in ("where", "pos", "position"):
                _print_current_line(saral_line, src,
                                    self.session.source_lines)

            # ── history ───────────────────────────
            elif cmd in ("history", "hist", "h"):
                _print_history(self.session)

            # ── fix (AI) ──────────────────────────
            elif cmd in ("fix", "ai"):
                _ai_fix(self.session)

            # ── explain (AI) ──────────────────────
            elif cmd in ("explain", "e"):
                _ai_explain_line(self.session, saral_line, src, variables)

            # ── save ──────────────────────────────
            elif cmd in ("save",):
                _save_session(self.session)

            # ── print expression ──────────────────
            elif cmd in ("print", "p"):
                if len(parts) >= 2:
                    expr = " ".join(parts[1:])
                    val  = variables.get(expr, "<not found>")
                    print(_c(f"  {expr}", C.CYAN) +
                          _c(" = ", C.DIM) +
                          _c(repr(val), C.WHITE))
                else:
                    print("  Usage: print <variable name>")

            # ── help ──────────────────────────────
            elif cmd in ("help", "?"):
                _print_help()

            # ── quit ──────────────────────────────
            elif cmd in ("quit", "exit", "q"):
                print(_c("\n  Debugger stopped.", C.YELLOW))
                sys.settrace(None)
                sys.exit(0)

            else:
                print(_c(f"  Unknown command: {cmd}", C.RED) +
                      "  (type 'help' for commands)")


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────

def _print_current_line(line_num: int, src: str, source_lines: list):
    """Print the current line with context."""
    total = len(source_lines)
    print()
    print(_c(f"  [{line_num}/{total}] ", C.DIM) +
          _c("→ ", C.GREEN, C.BOLD) +
          _c(src.strip(), C.WHITE, C.BOLD))


def _print_source(source_lines: list, current: int, breakpoints: set):
    """Print full source with current line marker and breakpoints."""
    print()
    print(_c("  ── Source ─────────────────────────────", C.DIM))
    start = max(1, current - 4)
    end   = min(len(source_lines), current + 6)
    for i in range(start, end + 1):
        line = source_lines[i - 1] if i <= len(source_lines) else ""
        bp   = _c("🔴", C.RED) if i in breakpoints else "  "
        if i == current:
            marker = _c("→", C.GREEN, C.BOLD)
            text   = _c(f"  {i:3}: {line}", C.WHITE, C.BOLD)
        else:
            marker = " "
            text   = _c(f"  {i:3}: {line}", C.DIM)
        print(f"  {bp} {marker}{text}")
    print(_c("  ───────────────────────────────────────", C.DIM))


def _print_vars(variables: dict):
    """Print all current variables in a clean table."""
    print()
    if not variables:
        print(_c("  (no variables set yet)", C.DIM))
        return
    print(_c("  ── Variables ───────────────────────────", C.DIM))
    for name, val in sorted(variables.items()):
        type_name = type(val).__name__
        print("  " +
              _c(f"{name:20}", C.CYAN) +
              _c(f" = ", C.DIM) +
              _c(f"{repr(val):30}", C.WHITE) +
              _c(f"  ({type_name})", C.DIM))
    print(_c("  ───────────────────────────────────────", C.DIM))


def _print_history(session: DebugSession):
    """Print the full step history."""
    print()
    print(_c("  ── History ─────────────────────────────", C.DIM))
    if not session.steps:
        print(_c("  (no steps yet)", C.DIM))
    else:
        for step in session.steps:
            print("  " +
                  _c(f"line {step['line']:3}: ", C.DIM) +
                  _c(step['source'], C.WHITE))
    if session.errors:
        print()
        print(_c("  Errors:", C.RED, C.BOLD))
        for e in session.errors:
            print(_c(f"  line {e['line']}: [{e['type']}] {e['message']}", C.RED))
    if session.watch_hits:
        print()
        print(_c("  Watchpoint hits:", C.YELLOW, C.BOLD))
        for h in session.watch_hits:
            print(_c(
                f"  line {h['line']}: {h['variable']} "
                f"{h['old']} → {h['new']}", C.YELLOW))
    print(_c("  ───────────────────────────────────────", C.DIM))


def _print_help():
    """Print all debugger commands."""
    print()
    print(_c("  ── Saral Debugger Commands ─────────────", C.CYAN, C.BOLD))
    cmds = [
        ("next  (n)",        "Execute next line"),
        ("run   (r)",        "Run until breakpoint or end"),
        ("vars  (v)",        "Show all variables and values"),
        ("print NAME",       "Show value of one variable"),
        ("break N",          "Set breakpoint at line N"),
        ("break",            "List all breakpoints"),
        ("clear N",          "Remove breakpoint at line N"),
        ("watch NAME",       "Alert when variable changes"),
        ("unwatch NAME",     "Stop watching variable"),
        ("list  (l)",        "Show source code with position"),
        ("where",            "Show current line"),
        ("fix   (ai)",        "AI analyses full session and suggests fix"),
        ("explain (e)",       "AI explains what the current line does"),
        ("history",          "Show all steps taken"),
        ("save",             "Save session log to file"),
        ("restart",          "Restart from beginning"),
        ("quit  (q)",        "Exit debugger"),
    ]
    for cmd, desc in cmds:
        print("  " +
              _c(f"{cmd:20}", C.GREEN) +
              _c(f"— {desc}", C.DIM))
    print(_c("  ───────────────────────────────────────", C.DIM))


# ─────────────────────────────────────────────
# AI FIX — with full session memory
# This is what makes Saral's debugger unique.
# The AI receives the complete session history
# so it has full context, not just the error.
# ─────────────────────────────────────────────

def _ai_fix(session: DebugSession):
    """
    Ask AI to analyse the full debug session and suggest a fix.
    Falls back to pattern-based hints if AI is not configured —
    so the user always gets useful output, never just 'unavailable'.
    """
    print()
    print(_c("  🤖  Analysing your debug session...", C.CYAN))

    try:
        from ai_helper import debug_hint
    except ImportError:
        print(_c("  ❌  ai_helper.py not found.", C.RED))
        return

    context    = session.ai_context()
    error_type = session.errors[-1]["type"]    if session.errors else ""
    error_msg  = session.errors[-1]["message"] if session.errors else ""

    result = debug_hint(
        context,
        error_type = error_type,
        error_msg  = error_msg,
        variables  = session.variables,
    )

    print()
    print(_c("  ── AI Analysis ─────────────────────────", C.CYAN))
    for line in result.splitlines():
        print(f"  {line}")
    print(_c("  ───────────────────────────────────────", C.DIM))


def _ai_explain_line(session: DebugSession, line_num: int,
                     src: str, variables: dict):
    """
    Ask AI to explain what the current line does in its current context.
    Falls back to pattern-based hints if AI is not configured.
    """
    print()
    print(_c("  🤖  Explaining current line...", C.CYAN))

    try:
        from ai_helper import debug_hint
    except ImportError:
        print(_c("  ❌  ai_helper.py not found.", C.RED))
        return

    # Build a focused context around the current line
    ctx = [
        "SARAL DEBUGGER — Line Explanation Request",
        f"File: {session.filename}",
        "",
        f"CURRENT LINE ({line_num}): {src.strip()}",
        "",
        "CURRENT VARIABLE VALUES:",
    ]
    for name, val in (variables or {}).items():
        ctx.append(f"  {name} = {repr(val)}")
    ctx.append("")
    ctx.append("SURROUNDING SOURCE:")
    start = max(1, line_num - 3)
    end   = min(len(session.source_lines), line_num + 3)
    for i in range(start, end + 1):
        marker = "→" if i == line_num else " "
        ctx.append(f"  {marker} {i:3}: {session.source_lines[i - 1]}")
    if session.steps:
        ctx.append("")
        ctx.append("LAST 3 STEPS:")
        for step in session.steps[-3:]:
            ctx.append(f"  Line {step['line']}: {step['source']}")

    result = debug_hint(
        "\n".join(ctx),
        error_type = "",
        error_msg  = "",
        variables  = variables,
    )

    print()
    print(_c("  ── Line Explanation ────────────────────", C.CYAN))
    for line in result.splitlines():
        print(f"  {line}")
    print(_c("  ───────────────────────────────────────", C.DIM))


# ─────────────────────────────────────────────
# SAVE SESSION
# ─────────────────────────────────────────────

def _save_session(session: DebugSession):
    """Save full debug session log to a file."""
    base    = os.path.splitext(os.path.basename(session.filename))[0]
    date    = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    logfile = f"{base}_debug_{date}.log"

    try:
        with open(logfile, "w", encoding="utf-8") as f:
            f.write(session.to_log())
        print(_c(f"  ✅  Session saved to: {logfile}", C.GREEN))
    except Exception as e:
        print(_c(f"  ❌  Could not save: {e}", C.RED))


def _save_debugged_file(session: DebugSession) -> str:
    """
    Automatically save the debugged program as <name>_debugged.saral
    in the same folder as the original file.

    Adds a comment header summarising the debug session so the user
    knows what was found and when it was debugged.  The body is the
    original source unchanged — the user can now edit this copy with
    the AI suggestions in mind.

    Returns the output path on success, or "" on failure.
    """
    base    = os.path.splitext(os.path.basename(session.filename))[0]
    dirpath = os.path.dirname(os.path.abspath(session.filename))
    outpath = os.path.join(dirpath, f"{base}_debugged.saral")

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    header = [
        f"# ── Debugged by Saral Debugger v1.1 ──────────────────────",
        f"# Date     : {stamp}",
        f"# Original : {os.path.basename(session.filename)}",
        f"# Steps run: {len(session.steps)}",
    ]

    if session.errors:
        header.append(f"# Errors   : {len(session.errors)}")
        for e in session.errors:
            msg = e['message'][:70] + ("…" if len(e['message']) > 70 else "")
            header.append(f"#   Line {e['line']:3}: {e['type']} — {msg}")
    else:
        header.append("# Result   : no errors found — program ran cleanly")

    if session.watch_hits:
        header.append(f"# Watchpoints triggered: {len(session.watch_hits)}")
        for h in session.watch_hits:
            header.append(
                f"#   Line {h['line']:3}: {h['variable']} "
                f"{h['old']} → {h['new']}"
            )

    if session.breakpoints:
        header.append(f"# Breakpoints set: {sorted(session.breakpoints)}")

    header.append("# ────────────────────────────────────────────────────────")
    header.append("")   # blank line before the code

    try:
        with open(outpath, "w", encoding="utf-8") as f:
            f.write("\n".join(header) + "\n" + session.source)
        return outpath
    except Exception as e:
        print(_c(f"  ❌  Could not save debugged file: {e}", C.RED))
        return ""


# ─────────────────────────────────────────────
# MAIN DEBUGGER ENTRY POINT
# ─────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════╗
║   🐛  Saral Debugger v1.1                   ║
║   Step through your code line by line        ║
║   AI help available at every step            ║
║   Type 'help' for all commands               ║
╚══════════════════════════════════════════════╝
"""

def run_debugger(filepath: str):
    """
    Main entry point.
    Called from saral.py when --debug flag is used.
    """
    # ── Load file ─────────────────────────────
    if not os.path.exists(filepath):
        print(f"\n❌  File not found: '{filepath}'\n")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    if not source.strip():
        print(f"\n⚠️   '{filepath}' is empty.\n")
        return

    print(BANNER)
    print(_c(f"  File: {filepath}", C.CYAN) +
          _c(f"  ({len(source.splitlines())} lines)", C.DIM))
    print()

    _run_debug_session(filepath, source)


def _run_debug_session(filepath: str, source: str):
    """Compile and run one debug session. Called also by restart."""

    # ── Compile ───────────────────────────────
    # Ensure compiler modules are importable
    _core_dir = os.path.dirname(os.path.abspath(__file__))
    if _core_dir not in sys.path:
        sys.path.insert(0, _core_dir)

    try:
        from pipeline  import compile_saral
        from sourcemap import SourceMap
    except ImportError as e:
        print(_c(f"  ❌  Cannot load Saral compiler: {e}", C.RED))
        print(_c("  Make sure debugger.py is in the same folder as pipeline.py", C.YELLOW))
        sys.exit(1)

    print(_c("  Compiling...", C.DIM), end=" ", flush=True)
    try:
        python_code, smap, parse_errors = compile_saral(
            source, filepath, show_warnings=False
        )
    except SystemExit:
        print(_c("❌  Compile errors above — fix them before debugging.", C.RED))
        return

    if parse_errors:
        print(_c(f"❌  {len(parse_errors)} parse error(s).", C.RED))
        for e in parse_errors:
            print(f"    {e}")
        print(_c("  Fix these errors first, then run the debugger again.", C.YELLOW))
        return

    print(_c("✅  Ready", C.GREEN))
    print()

    # ── Create session ────────────────────────
    session = DebugSession(filepath, source)

    # ── Ask how to start ──────────────────────
    print(_c("  How do you want to start?", C.BOLD))
    print(_c("  step", C.GREEN) + " — go line by line from the start")
    print(_c("  run ", C.GREEN) + " — run until a breakpoint (set one with: break N)")
    print(_c("  help", C.GREEN) + " — see all commands")
    print()

    try:
        choice = input(_c("debug> ", C.GREEN, C.BOLD)).strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
        return

    if choice in ("quit", "q", "exit"):
        print("Goodbye!")
        return

    if choice == "help":
        _print_help()
        try:
            choice = input(_c("debug> ", C.GREEN, C.BOLD)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            return

    step_mode = choice in ("step", "next", "n", "s", "")

    # If they typed break N before running
    if choice.startswith("break"):
        parts = choice.split()
        if len(parts) >= 2:
            try:
                session.breakpoints.add(int(parts[1]))
                print(_c(f"  🔴 Breakpoint set at line {parts[1]}", C.RED))
            except ValueError:
                pass
        step_mode = False

    # ── Install tracer and execute ─────────────
    tracer = StepTracer(session, smap, step_mode=step_mode)

    print()
    print(_c("  ── Running ─────────────────────────────", C.DIM))

    # Build execution globals — same environment as normal saral run
    exec_globals = {"__name__": "__main__"}

    def _trace_call(frame, event, arg):
        return tracer.trace_lines if event == "call" else None

    sys.settrace(_trace_call)
    try:
        code_obj = compile(python_code, filepath, "exec")
        exec(code_obj, exec_globals)
        sys.settrace(None)

        print()
        print(_c("  ✅  Program completed successfully.", C.GREEN, C.BOLD))
        print(_c(f"  {len(session.steps)} lines executed.", C.DIM))

    except SystemExit:
        sys.settrace(None)

    except Exception as e:
        sys.settrace(None)
        err_type = type(e).__name__
        err_msg  = str(e)

        # Map to Saral line — prefer frames from the Saral-generated code
        py_line = 0
        tb = e.__traceback__
        if tb:
            frames = traceback.extract_tb(tb)
            # First pass: find deepest frame that belongs to the compiled Saral code
            for frame_info in reversed(frames):
                if frame_info.filename == filepath and frame_info.lineno:
                    py_line = frame_info.lineno
                    break
            # Fallback: any frame with a line number
            if not py_line:
                for frame_info in reversed(frames):
                    if frame_info.lineno:
                        py_line = frame_info.lineno
                        break
        saral_line = smap.saral_line_for(py_line) or session.current_line or 1
        src_line   = ""
        if 0 < saral_line <= len(session.source_lines):
            src_line = session.source_lines[saral_line - 1].strip()

        session.record_error(saral_line, err_type, err_msg)

        # Map to friendly Saral error — use raw fallback only if errors.py fails
        displayed = False
        try:
            from errors import classify_runtime_error, display_error
            report = classify_runtime_error(
                e, session.source_lines, filepath, saral_line
            )
            display_error(report)
            displayed = True
        except Exception:
            pass

        if not displayed:
            print()
            print(_c(f"  ❌  Error at line {saral_line}: {src_line}", C.RED, C.BOLD))
            print(_c(f"     {err_type}: {err_msg}", C.RED))

        # Auto-trigger AI analysis immediately after any runtime error
        _ai_fix(session)

    # ── Auto-save debugged file ────────────────
    debugged_path = _save_debugged_file(session)
    if debugged_path:
        print()
        print(_c("  📄  Debugged file saved: ", C.GREEN, C.BOLD) +
              _c(os.path.basename(debugged_path), C.CYAN))

    # ── Post-run menu ─────────────────────────
    print()
    print(_c("  Session complete. Options:", C.BOLD))
    if session.had_error:
        print(_c("  fix     ", C.GREEN) + "— show AI analysis again")
    else:
        print(_c("  fix     ", C.GREEN) + "— AI analysis of this session")
    print(_c("  history ", C.GREEN) + "— show all steps")
    print(_c("  vars    ", C.GREEN) + "— show final variable values")
    print(_c("  save    ", C.GREEN) + "— save session log to file")
    print(_c("  restart ", C.GREEN) + "— debug again from the start")
    print(_c("  quit    ", C.GREEN) + "— exit")
    print()

    while True:
        try:
            cmd = input(_c("debug> ", C.GREEN, C.BOLD)).strip().lower()
        except (KeyboardInterrupt, EOFError):
            break

        if cmd in ("quit", "q", "exit"):
            print("Goodbye!")
            break
        elif cmd in ("fix", "ai"):
            _ai_fix(session)
        elif cmd in ("history", "hist", "h"):
            _print_history(session)
        elif cmd in ("vars", "v", "variables"):
            _print_vars(session.variables)
        elif cmd in ("save",):
            _save_session(session)
        elif cmd in ("restart", "r"):
            print(_c("\n  Restarting session...\n", C.CYAN))
            _run_debug_session(filepath, source)
            break
        elif cmd in ("list", "l"):
            _print_source(session.source_lines,
                          session.current_line,
                          session.breakpoints)
        elif cmd in ("help", "?"):
            _print_help()
        elif cmd == "":
            continue
        else:
            print(_c(f"  Unknown: {cmd}", C.DIM) + "  (quit / fix / history / vars / save / restart)")


# ─────────────────────────────────────────────
# STANDALONE TEST
# python3 debugger.py myfile.saral
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 debugger.py myfile.saral")
        sys.exit(1)
    run_debugger(sys.argv[1])
