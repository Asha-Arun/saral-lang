"""
analyzer.py — Saral Semantic Analyzer v4.0
Walks the AST after parsing and:
  1. Builds a symbol table (variables, functions, their types and locations)
  2. Warns on variable used before defined
  3. Warns on function called before defined
  4. Warns on type mismatches where detectable
  5. Returns enriched AST + symbol table for codegen and error system
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from ast_nodes import *


# ─────────────────────────────────────────────
# SYMBOL TYPES
# ─────────────────────────────────────────────

class SymType:
    UNKNOWN  = "unknown"
    NUMBER   = "number"
    TEXT     = "text"
    BOOLEAN  = "boolean"
    LIST     = "list"
    DICT     = "dict"
    FUNCTION = "function"
    ANY      = "any"


# ─────────────────────────────────────────────
# SYMBOL ENTRIES
# ─────────────────────────────────────────────

@dataclass
class VarSymbol:
    name:         str
    sym_type:     str       = SymType.UNKNOWN
    line_defined: int       = 0
    times_used:   int       = 0
    is_global:    bool      = False
    is_param:     bool      = False


@dataclass
class FuncSymbol:
    name:         str
    params:       List[Tuple[str, Optional[str]]] = field(default_factory=list)
    return_type:  str       = SymType.UNKNOWN
    line_defined: int       = 0
    times_called: int       = 0


# ─────────────────────────────────────────────
# SCOPE
# ─────────────────────────────────────────────

@dataclass
class Scope:
    name:      str                        = "global"
    variables: Dict[str, VarSymbol]       = field(default_factory=dict)
    parent:    Optional["Scope"]          = None

    def define(self, sym: VarSymbol):
        self.variables[sym.name] = sym

    def lookup(self, name: str) -> Optional[VarSymbol]:
        if name in self.variables:
            return self.variables[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_local(self, name: str) -> Optional[VarSymbol]:
        return self.variables.get(name)


# ─────────────────────────────────────────────
# ANALYSIS WARNING
# ─────────────────────────────────────────────

@dataclass
class AnalysisWarning:
    code:     str
    message:  str
    line_num: int
    severity: str = "warning"  # warning / info

    def __str__(self):
        return f"[{self.code}] Line {self.line_num}: {self.message}"


# ─────────────────────────────────────────────
# SYMBOL TABLE
# ─────────────────────────────────────────────

class SymbolTable:
    def __init__(self):
        self.global_scope  = Scope("global")
        self.functions:    Dict[str, FuncSymbol] = {}
        self.globals_decl: Set[str]              = set()
        self.warnings:     List[AnalysisWarning] = []
        self._scope_stack: List[Scope]           = [self.global_scope]

    @property
    def current_scope(self) -> Scope:
        return self._scope_stack[-1]

    def push_scope(self, name: str):
        new_scope = Scope(name=name, parent=self.current_scope)
        self._scope_stack.append(new_scope)

    def pop_scope(self):
        if len(self._scope_stack) > 1:
            self._scope_stack.pop()

    def define_var(self, name: str, sym_type: str = SymType.UNKNOWN,
                   line: int = 0, is_param: bool = False):
        sym = VarSymbol(
            name=name, sym_type=sym_type,
            line_defined=line, is_param=is_param
        )
        self.current_scope.define(sym)

    def define_func(self, name: str, params: list,
                    line: int = 0):
        sym = FuncSymbol(name=name, params=params, line_defined=line)
        self.functions[name] = sym

    def lookup_var(self, name: str) -> Optional[VarSymbol]:
        return self.current_scope.lookup(name)

    def lookup_func(self, name: str) -> Optional[FuncSymbol]:
        return self.functions.get(name)

    def mark_var_used(self, name: str):
        sym = self.lookup_var(name)
        if sym:
            sym.times_used += 1

    def mark_func_called(self, name: str):
        sym = self.lookup_func(name)
        if sym:
            sym.times_called += 1

    def warn(self, code: str, msg: str, line: int,
             severity: str = "warning"):
        self.warnings.append(AnalysisWarning(
            code=code, message=msg,
            line_num=line, severity=severity
        ))

    def all_warnings(self) -> List[AnalysisWarning]:
        return sorted(self.warnings, key=lambda w: w.line_num)

    def summary(self) -> dict:
        all_vars = {}
        self._collect_vars(self.global_scope, all_vars)
        return {
            "variables":    all_vars,
            "functions":    {n: {
                "params":       [p[0] for p in f.params],
                "line_defined": f.line_defined,
                "times_called": f.times_called,
            } for n, f in self.functions.items()},
            "warnings":     len(self.warnings),
        }

    def _collect_vars(self, scope: Scope, result: dict):
        for name, sym in scope.variables.items():
            result[name] = {
                "type":         sym.sym_type,
                "line_defined": sym.line_defined,
                "times_used":   sym.times_used,
            }


# ─────────────────────────────────────────────
# ANALYZER
# ─────────────────────────────────────────────

class Analyzer:
    """
    Walks the AST and builds the symbol table.
    Issues warnings for common mistakes.
    Does NOT modify the AST — analysis only.
    """

    # Built-in variables always available
    BUILTINS = {
        "_saral_err",  # error in catch block
        "_i",          # loop variable in repeat
        "true", "false",
    }

    def __init__(self, source_lines: List[str] = None,
                 filename: str = "<program>"):
        self.table        = SymbolTable()
        self.source_lines = source_lines or []
        self.filename     = filename
        self._in_function = False
        self._in_loop     = 0

    def analyze(self, program: Program) -> SymbolTable:
        """Analyze a complete program. Returns the symbol table."""
        # First pass: collect all function definitions
        # (so forward calls don't warn)
        self._first_pass(program.body)
        # Second pass: full analysis
        self._analyze_block(program.body)
        # Post-analysis checks
        self._check_unused()
        return self.table

    # ── first pass: collect function names ──

    def _first_pass(self, stmts: List[Stmt]):
        for stmt in stmts:
            if isinstance(stmt, DefineStmt):
                params = [(p[0], None) for p in stmt.params]
                self.table.define_func(
                    stmt.name, params, stmt.line_num
                )

    # ── block analysis ───────────────────────

    def _analyze_block(self, stmts: List[Stmt]):
        for stmt in stmts:
            self._analyze_stmt(stmt)

    # ── statement analysis ───────────────────

    def _analyze_stmt(self, node: Stmt):
        if node is None:
            return

        # ── store ──────────────────────────────
        if isinstance(node, StoreStmt):
            # analyze value expression first
            self._analyze_expr(node.value, node.line_num)
            # infer type from value
            sym_type = self._infer_type(node.value)
            # define or update variable
            existing = self.table.lookup_var(node.target)
            if existing:
                existing.sym_type = sym_type
            else:
                self.table.define_var(
                    node.target, sym_type, node.line_num
                )
            return

        # ── show ───────────────────────────────
        if isinstance(node, ShowStmt):
            self._analyze_expr(node.value, node.line_num)
            return

        if isinstance(node, (ShowErrorStmt, ShowBlankStmt)):
            return

        if isinstance(node, ShowProgressStmt):
            self._analyze_expr(node.current, node.line_num)
            self._analyze_expr(node.total, node.line_num)
            return

        # ── ask ────────────────────────────────
        if isinstance(node, AskStmt):
            sym_type = SymType.NUMBER if node.is_number else SymType.TEXT
            self.table.define_var(node.target, sym_type, node.line_num)
            return

        if isinstance(node, AskAiStmt):
            self.table.define_var(node.target, SymType.TEXT, node.line_num)
            return

        # ── increase / decrease ────────────────
        if isinstance(node, IncreaseStmt):
            sym = self.table.lookup_var(node.target)
            if not sym:
                self.table.warn(
                    "W002",
                    f"'{node.target}' used in 'increase' before being stored",
                    node.line_num
                )
            self._analyze_expr(node.amount, node.line_num)
            return

        if isinstance(node, DecreaseStmt):
            sym = self.table.lookup_var(node.target)
            if not sym:
                self.table.warn(
                    "W002",
                    f"'{node.target}' used in 'decrease' before being stored",
                    node.line_num
                )
            self._analyze_expr(node.amount, node.line_num)
            return

        # ── return ─────────────────────────────
        if isinstance(node, ReturnStmt):
            if not self._in_function:
                self.table.warn(
                    "W005",
                    "'return' used outside of a 'define' block",
                    node.line_num
                )
            for v in node.values:
                self._analyze_expr(v, node.line_num)
            return

        # ── call ───────────────────────────────
        if isinstance(node, CallStmt):
            fn = self.table.lookup_func(node.fn_name)
            if not fn:
                self.table.warn(
                    "W003",
                    f"Function '{node.fn_name}' called but not defined",
                    node.line_num
                )
            else:
                self.table.mark_func_called(node.fn_name)
            if node.args:
                self._analyze_expr(node.args, node.line_num)
            return

        if isinstance(node, StoreResultStmt):
            fn = self.table.lookup_func(node.fn_name)
            if not fn:
                self.table.warn(
                    "W003",
                    f"Function '{node.fn_name}' called but not defined",
                    node.line_num
                )
            else:
                self.table.mark_func_called(node.fn_name)
            if node.args:
                self._analyze_expr(node.args, node.line_num)
            self.table.define_var(node.target, SymType.ANY, node.line_num)
            return

        if isinstance(node, StoreMultipleResultStmt):
            fn = self.table.lookup_func(node.fn_name)
            if not fn:
                self.table.warn(
                    "W003",
                    f"Function '{node.fn_name}' called but not defined",
                    node.line_num
                )
            else:
                self.table.mark_func_called(node.fn_name)
            for t in node.targets:
                self.table.define_var(t, SymType.ANY, node.line_num)
            return

        # ── list operations ────────────────────
        if isinstance(node, AddStmt):
            self._analyze_expr(node.value, node.line_num)
            sym = self.table.lookup_var(node.target)
            if not sym:
                self.table.warn(
                    "W002",
                    f"List '{node.target}' used before 'make list called {node.target}'",
                    node.line_num
                )
            return

        if isinstance(node, RemoveStmt):
            self._analyze_expr(node.value, node.line_num)
            sym = self.table.lookup_var(node.target)
            if not sym:
                self.table.warn(
                    "W002",
                    f"'{node.target}' used before being defined",
                    node.line_num
                )
            return

        if isinstance(node, MakeListStmt):
            self.table.define_var(node.name, SymType.LIST, node.line_num)
            return

        if isinstance(node, MakeDictStmt):
            self.table.define_var(node.name, SymType.DICT, node.line_num)
            return

        if isinstance(node, (SortStmt, ReverseStmt, MakeUniqueStmt)):
            name = node.name if hasattr(node, "name") else node.source
            sym  = self.table.lookup_var(name)
            if not sym:
                self.table.warn(
                    "W002",
                    f"'{name}' used before being defined",
                    node.line_num
                )
            return

        if isinstance(node, SetDictStmt):
            sym = self.table.lookup_var(node.dict_name)
            if not sym:
                self.table.warn(
                    "W002",
                    f"Dictionary '{node.dict_name}' used before "
                    f"'make dictionary called {node.dict_name}'",
                    node.line_num
                )
            self._analyze_expr(node.key, node.line_num)
            self._analyze_expr(node.value, node.line_num)
            return

        # ── global ─────────────────────────────
        if isinstance(node, GlobalStmt):
            if not self._in_function:
                self.table.warn(
                    "W006",
                    "'global' used outside a 'define' block — has no effect",
                    node.line_num
                )
            else:
                for name in node.names:
                    self.table.globals_decl.add(name)
                    # define in global scope if not already there
                    gs = self.table.global_scope.lookup_local(name)
                    if not gs:
                        self.table.global_scope.define(
                            VarSymbol(name=name, is_global=True,
                                      line_defined=node.line_num)
                        )
            return

        # ── file / network ─────────────────────
        if isinstance(node, ReadFileStmt):
            self._analyze_expr(node.path, node.line_num)
            mode_type = {
                "text":  SymType.TEXT,
                "lines": SymType.LIST,
                "csv":   SymType.LIST,
                "json":  SymType.ANY,
            }.get(node.mode, SymType.ANY)
            self.table.define_var(node.target, mode_type, node.line_num)
            return

        if isinstance(node, FetchStmt):
            self._analyze_expr(node.url, node.line_num)
            self.table.define_var(node.target, SymType.ANY, node.line_num)
            return

        # ── validate ───────────────────────────
        if isinstance(node, ValidateStmt):
            self.table.define_var(node.target, SymType.BOOLEAN, node.line_num)
            return

        # ── string ops that produce vars ───────
        if isinstance(node, (
            FindPatternStmt, ReplacePatternStmt, ReplaceStrStmt,
            SplitStmt, JoinStmt, ParseJsonStmt, ConvertJsonStmt,
            FlattenStmt
        )):
            tgt = getattr(node, "target", None)
            if tgt:
                typ = SymType.LIST if isinstance(node, (
                    FindPatternStmt, SplitStmt, FlattenStmt
                )) else SymType.TEXT
                self.table.define_var(tgt, typ, node.line_num)
            return

        if isinstance(node, MultilineStrStmt):
            self.table.define_var(node.target, SymType.TEXT, node.line_num)
            return

        if isinstance(node, (WriteFileStmt, AppendFileStmt,
                              DeleteFileStmt, WriteCsvStmt, WriteJsonStmt)):
            return

        if isinstance(node, (UseStmt, IncludeStmt)):
            return

        if isinstance(node, (WaitStmt, ClearScreenStmt, ExitStmt,
                              StopStmt, SkipStmt)):
            return

        if isinstance(node, RaiseErrorStmt):
            self._analyze_expr(node.message, node.line_num)
            return

        if isinstance(node, (RunBackgroundStmt, WaitForAllStmt)):
            return

        if isinstance(node, CommentStmt):
            return

        # ── COMPOUND STATEMENTS ────────────────

        if isinstance(node, IfStmt):
            self._analyze_expr(node.condition, node.line_num)
            self._analyze_block(node.body)
            for elif_cond, elif_body in node.elseifs:
                elif_line = getattr(elif_cond, "line_num", node.line_num)
                self._analyze_expr(elif_cond, elif_line)
                self._analyze_block(elif_body)
            if node.else_body:
                self._analyze_block(node.else_body)
            return

        if isinstance(node, RepeatStmt):
            self._analyze_expr(node.count, node.line_num)
            self._in_loop += 1
            self._analyze_block(node.body)
            self._in_loop -= 1
            return

        if isinstance(node, ForEachStmt):
            # define loop variable
            self.table.define_var(node.var, SymType.ANY, node.line_num)
            # check iterable exists
            sym = self.table.lookup_var(node.iterable)
            if not sym:
                self.table.warn(
                    "W002",
                    f"'{node.iterable}' used in 'for each' but not defined",
                    node.line_num
                )
            self._in_loop += 1
            self._analyze_block(node.body)
            self._in_loop -= 1
            return

        if isinstance(node, CountStmt):
            self._analyze_expr(node.start, node.line_num)
            self._analyze_expr(node.end, node.line_num)
            self.table.define_var(node.var, SymType.NUMBER, node.line_num)
            self._in_loop += 1
            self._analyze_block(node.body)
            self._in_loop -= 1
            return

        if isinstance(node, WhileStmt):
            self._analyze_expr(node.condition, node.line_num)
            self._in_loop += 1
            self._analyze_block(node.body)
            self._in_loop -= 1
            return

        if isinstance(node, DefineStmt):
            # already registered in first pass
            self.table.push_scope(f"fn:{node.name}")
            prev_in_fn = self._in_function
            self._in_function = True
            # define parameters in function scope
            for pname, pdefault in node.params:
                self.table.define_var(
                    pname, SymType.ANY,
                    node.line_num, is_param=True
                )
                if pdefault:
                    self._analyze_expr(pdefault, node.line_num)
            self._analyze_block(node.body)
            self._in_function = prev_in_fn
            self.table.pop_scope()
            return

        if isinstance(node, TryStmt):
            self._analyze_block(node.body)
            # _saral_err is already in BUILTINS — no define_var needed
            self._analyze_block(node.catch_body)
            return

    # ── expression analysis ──────────────────

    def _analyze_expr(self, node: Any, line: int):
        """Walk an expression and check variable usage."""
        if node is None:
            return

        if isinstance(node, Identifier):
            name = node.name
            if name in self.BUILTINS:
                return
            sym = self.table.lookup_var(name)
            if sym:
                self.table.mark_var_used(name)
            else:
                # not defined — warn
                self.table.warn(
                    "W001",
                    f"'{name}' is used but may not have been stored yet",
                    line,
                    severity="info"
                )
            return

        if isinstance(node, (NumberLiteral, StringLiteral, BoolLiteral)):
            return

        if isinstance(node, BinaryOp):
            self._analyze_expr(node.left, line)
            self._analyze_expr(node.right, line)
            # check type mismatch for + operator
            if node.op == "+":
                lt = self._infer_type(node.left)
                rt = self._infer_type(node.right)
                if lt != SymType.UNKNOWN and rt != SymType.UNKNOWN:
                    if lt != rt and {lt, rt} not in (
                        {SymType.NUMBER, SymType.ANY},
                        {SymType.TEXT, SymType.ANY},
                    ):
                        if SymType.NUMBER in {lt, rt} and SymType.TEXT in {lt, rt}:
                            self.table.warn(
                                "W004",
                                "Mixing text and numbers with '+' — "
                                "use 'as text' or 'as number' to convert first",
                                line
                            )
            return

        if isinstance(node, UnaryOp):
            self._analyze_expr(node.operand, line)
            return

        if isinstance(node, (MathFnExpr,)):
            self._analyze_expr(node.arg, line)
            return

        if isinstance(node, AggregateExpr):
            sym = self.table.lookup_var(node.list_name)
            if not sym:
                self.table.warn("W001",
                    f"'{node.list_name}' used before being defined", line,
                    severity="info")
            return

        if isinstance(node, StringOpExpr):
            self._analyze_expr(node.arg, line)
            return

        if isinstance(node, ListOpExpr):
            sym = self.table.lookup_var(node.list_name)
            if not sym:
                self.table.warn("W001",
                    f"'{node.list_name}' used before being defined", line,
                    severity="info")
            if node.index: self._analyze_expr(node.index, line)
            if node.start: self._analyze_expr(node.start, line)
            if node.end:   self._analyze_expr(node.end, line)
            return

        if isinstance(node, DictOpExpr):
            sym = self.table.lookup_var(node.dict_name)
            if not sym:
                self.table.warn("W001",
                    f"'{node.dict_name}' used before being defined", line,
                    severity="info")
            self._analyze_expr(node.key, line)
            return

        if isinstance(node, DeepGetExpr):
            sym = self.table.lookup_var(node.dict_name)
            if not sym:
                self.table.warn("W001",
                    f"'{node.dict_name}' used before being defined", line,
                    severity="info")
            for k in node.keys:
                self._analyze_expr(k, line)
            return

        if isinstance(node, AsTypeExpr):
            self._analyze_expr(node.value, line)
            return

        if isinstance(node, (DateExpr, RandomExpr, BoolLiteral)):
            return

        if isinstance(node, ResultOfExpr):
            fn = self.table.lookup_func(node.fn_name)
            if not fn:
                self.table.warn("W003",
                    f"Function '{node.fn_name}' called but not defined", line)
            if node.args:
                self._analyze_expr(node.args, line)
            return

        if isinstance(node, PatternCondition):
            sym = self.table.lookup_var(node.var_name)
            if not sym and node.var_name:
                self.table.warn("W001",
                    f"'{node.var_name}' used before being defined", line,
                    severity="info")
            return

        if isinstance(node, FileExistsCondition):
            self._analyze_expr(node.path, line)
            return

    # ── type inference ───────────────────────

    def _infer_type(self, node: Any) -> str:
        """Infer the Saral type of an expression node."""
        if isinstance(node, NumberLiteral):  return SymType.NUMBER
        if isinstance(node, StringLiteral):  return SymType.TEXT
        if isinstance(node, BoolLiteral):    return SymType.BOOLEAN
        if isinstance(node, Identifier):
            sym = self.table.lookup_var(node.name)
            return sym.sym_type if sym else SymType.UNKNOWN
        if isinstance(node, BinaryOp):
            if node.op in ("+", "-", "*", "/", "%", "**"):
                lt = self._infer_type(node.left)
                rt = self._infer_type(node.right)
                if lt == SymType.TEXT or rt == SymType.TEXT:
                    return SymType.TEXT
                return SymType.NUMBER
            if node.op in (">", "<", "==", "!=", ">=", "<=",
                           "and", "or"):
                return SymType.BOOLEAN
        if isinstance(node, MathFnExpr):     return SymType.NUMBER
        if isinstance(node, AggregateExpr):  return SymType.NUMBER
        if isinstance(node, StringOpExpr):
            if node.op == "length":          return SymType.NUMBER
            return SymType.TEXT
        if isinstance(node, AsTypeExpr):
            return {
                "number": SymType.NUMBER,
                "text":   SymType.TEXT,
                "decimal":SymType.NUMBER,
                "boolean":SymType.BOOLEAN,
            }.get(node.type_kw, SymType.UNKNOWN)
        if isinstance(node, DateExpr):       return SymType.TEXT
        if isinstance(node, RandomExpr):     return SymType.NUMBER
        if isinstance(node, ListOpExpr):     return SymType.ANY
        if isinstance(node, DictOpExpr):     return SymType.ANY
        return SymType.UNKNOWN

    # ── post-analysis checks ─────────────────

    def _check_unused(self):
        """Warn about variables defined but never used."""
        for name, sym in self.table.global_scope.variables.items():
            if (sym.times_used == 0
                    and not sym.is_param
                    and not name.startswith("_")
                    and sym.line_defined > 0):
                self.table.warn(
                    "W007",
                    f"'{name}' is stored but never used",
                    sym.line_defined,
                    severity="info"
                )


# ─────────────────────────────────────────────
# WARNING FORMATTER
# ─────────────────────────────────────────────

WARNING_DESCRIPTIONS = {
    "W001": "Variable may not be defined yet",
    "W002": "Variable used before being stored",
    "W003": "Function not defined",
    "W004": "Type mismatch — mixing text and numbers",
    "W005": "Return used outside function",
    "W006": "Global used outside function",
    "W007": "Variable defined but never used",
}

def format_warnings(warnings: List[AnalysisWarning],
                    source_lines: List[str] = None) -> str:
    if not warnings:
        return ""
    lines = ["\n── Saral Analysis Warnings ─────────────────"]
    for w in warnings:
        icon = "⚠️ " if w.severity == "warning" else "ℹ️ "
        desc = WARNING_DESCRIPTIONS.get(w.code, "")
        suffix = f" — {desc}" if desc else ""
        lines.append(f"  {icon}  [{w.code}] Line {w.line_num}: {w.message}{suffix}")
        if source_lines and 0 < w.line_num <= len(source_lines):
            src = source_lines[w.line_num - 1].strip()
            lines.append(f"           {src}")
    lines.append("─────────────────────────────────────────────")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────

def analyze(program: Program,
            source_lines: List[str] = None,
            filename: str = "<program>") -> Tuple[SymbolTable, List[AnalysisWarning]]:
    """
    Analyze a parsed Saral program.
    Returns (symbol_table, warnings).
    """
    a   = Analyzer(source_lines or [], filename)
    tbl = a.analyze(program)
    return tbl, tbl.all_warnings()


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    from parser import parse

    test_src = """
store 10 in price
store price * 2 in double_price
show double_price

# undefined variable warning
show undefined_var

if price > 5
    show "expensive"
done

make list called fruits
add "apple" to fruits
for each item in fruits
    show item
done

define greet using name, title = "Mr"
    global price
    show "Hello " + title + " " + name
    show price
end

call greet with "Arun"

# type mismatch warning
store "hello" + 42 in mixed

# unused variable
store 999 in unused_thing
"""

    ast, parse_errors = parse(test_src)
    if parse_errors:
        print("Parse errors:")
        for e in parse_errors:
            print(f"  {e}")

    src_lines = test_src.splitlines()
    table, warnings = analyze(ast, src_lines)

    print(f"✅  Analysis complete")
    print(f"   Variables:  {len(table.global_scope.variables)}")
    print(f"   Functions:  {len(table.functions)}")
    print(f"   Warnings:   {len(warnings)}")
    print()

    if warnings:
        print(format_warnings(warnings, src_lines))

    print("\n── Symbol Table Summary ──────────────────")
    summary = table.summary()
    print("Variables:")
    for name, info in summary["variables"].items():
        print(f"  {name:<20} type={info['type']:<10} "
              f"line={info['line_defined']:<4} "
              f"used={info['times_used']}")
    print("\nFunctions:")
    for name, info in summary["functions"].items():
        print(f"  {name}({', '.join(info['params'])}) "
              f"line={info['line_defined']} "
              f"called={info['times_called']}")
