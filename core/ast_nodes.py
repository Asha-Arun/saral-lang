"""
ast_nodes.py — Saral Abstract Syntax Tree Node Definitions v4.0
Every node carries line_num and col_num for precise error reporting.
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Any, Tuple


# ─────────────────────────────────────────────
# BASE CLASSES
# ─────────────────────────────────────────────

@dataclass
class Node:
    """Base class for all AST nodes."""
    line_num:    int  = 0
    col_num:     int  = 0
    source_line: str  = ""

    def node_type(self) -> str:
        return self.__class__.__name__


@dataclass
class Expr(Node):
    """Base class for all expression nodes."""
    pass


@dataclass
class Stmt(Node):
    """Base class for all statement nodes."""
    pass


# ─────────────────────────────────────────────
# PROGRAM
# ─────────────────────────────────────────────

@dataclass
class Program(Node):
    body: List[Stmt] = field(default_factory=list)


# ─────────────────────────────────────────────
# EXPRESSIONS
# ─────────────────────────────────────────────

@dataclass
class NumberLiteral(Expr):
    value: float = 0.0

    def is_int(self):
        return math.isfinite(self.value) and self.value == int(self.value)


@dataclass
class StringLiteral(Expr):
    value:      str  = ""
    is_fstring: bool = False   # True if contains {variable}


@dataclass
class BoolLiteral(Expr):
    value: bool = True


@dataclass
class Identifier(Expr):
    name: str = ""


@dataclass
class BinaryOp(Expr):
    left:  Any = None   # Expr
    op:    str = ""     # + - * / % ** and or
    right: Any = None   # Expr


@dataclass
class UnaryOp(Expr):
    op:      str = ""   # - not
    operand: Any = None # Expr


@dataclass
class MathFnExpr(Expr):
    """sqrt of X, sin of X, round of X to N places, etc."""
    fn:     str = ""    # sqrt floor ceiling sin cos tan log absolute
    arg:    Any = None  # Expr
    places: Optional[int] = None  # for round


@dataclass
class AggregateExpr(Expr):
    """sum of list, average of list, maximum of list, minimum of list"""
    fn:        str = ""  # sum average maximum minimum
    list_name: str = ""


@dataclass
class StringOpExpr(Expr):
    """uppercase of X, lowercase of X, trimmed X, reversed X, length of X"""
    op:  str = ""   # uppercase lowercase trimmed reversed length
    arg: Any = None # Expr


@dataclass
class PadExpr(Expr):
    """X padded left/right/center to N"""
    direction: str = ""  # left right center
    value:     Any = None
    width:     int = 0


@dataclass
class ListOpExpr(Expr):
    """item N of list, items N to M of list, first N of list, last N of list"""
    op:        str = ""  # item items first last
    list_name: str = ""
    index:     Any = None  # for item
    start:     Any = None  # for items/first/last
    end:       Any = None  # for items


@dataclass
class DictOpExpr(Expr):
    """value of key in dict"""
    dict_name: str = ""
    key:       Any = None  # Expr


@dataclass
class DeepGetExpr(Expr):
    """deep value of key1 then key2 in dict"""
    dict_name: str = ""
    keys:      List[Any] = field(default_factory=list)  # List[Expr]


@dataclass
class DateExpr(Expr):
    """today, now, current time/year/month/day"""
    kind: str = ""  # today now current_time current_year current_month current_day


@dataclass
class RandomExpr(Expr):
    """random number from A to B"""
    low:  Optional[Any] = None  # Expr
    high: Optional[Any] = None  # Expr


@dataclass
class ResultOfExpr(Expr):
    """result of fn with args"""
    fn_name: str = ""
    args:    Optional[Any] = None  # Expr or None


@dataclass
class AsTypeExpr(Expr):
    """X as number / as text / as decimal / as boolean"""
    value:    Any = None  # Expr
    type_kw:  str = ""    # number text decimal boolean


@dataclass
class FStringExpr(Expr):
    """String with {variable} interpolation"""
    template: str = ""    # the raw string with {vars}


@dataclass
class PatternCondition(Expr):
    """var matches pattern 'regex'"""
    var_name: str = ""
    pattern:  Any = None  # Expr


@dataclass
class FileExistsCondition(Expr):
    """file 'path' exists"""
    path: Any = None  # Expr


# ─────────────────────────────────────────────
# STATEMENTS — SIMPLE
# ─────────────────────────────────────────────

@dataclass
class StoreStmt(Stmt):
    target: str = ""
    value:  Any = None  # Expr


@dataclass
class StoreAsTypeStmt(Stmt):
    target:  str = ""
    value:   Any = None  # Expr
    type_kw: str = ""    # number text decimal boolean


@dataclass
class ShowStmt(Stmt):
    value: Any = None  # Expr
    color: Optional[str] = None


@dataclass
class ShowErrorStmt(Stmt):
    pass


@dataclass
class ShowBlankStmt(Stmt):
    pass


@dataclass
class ShowProgressStmt(Stmt):
    current: Any = None  # Expr
    total:   Any = None  # Expr


@dataclass
class AskStmt(Stmt):
    prompt:    Any = None  # Expr
    target:    str = ""
    is_number: bool = False


@dataclass
class AskAiStmt(Stmt):
    prompt: Any = None  # Expr
    data:   Optional[str] = None
    target: str = ""


@dataclass
class IncreaseStmt(Stmt):
    target: str = ""
    amount: Any = None  # Expr


@dataclass
class DecreaseStmt(Stmt):
    target: str = ""
    amount: Any = None  # Expr


@dataclass
class ReturnStmt(Stmt):
    values: List[Any] = field(default_factory=list)  # List[Expr]


@dataclass
class CallStmt(Stmt):
    fn_name: str = ""
    args:    Optional[Any] = None  # Expr


@dataclass
class StoreResultStmt(Stmt):
    target:  str = ""
    fn_name: str = ""
    args:    Optional[Any] = None  # Expr


@dataclass
class StoreMultipleResultStmt(Stmt):
    targets: List[str] = field(default_factory=list)
    fn_name: str = ""
    args:    Optional[Any] = None  # Expr


@dataclass
class AddStmt(Stmt):
    value:  Any = None  # Expr
    target: str = ""


@dataclass
class RemoveStmt(Stmt):
    value:   Any = None  # Expr
    target:  str = ""
    is_dict: bool = False


@dataclass
class MakeListStmt(Stmt):
    name: str = ""


@dataclass
class MakeDictStmt(Stmt):
    name: str = ""


@dataclass
class SortStmt(Stmt):
    name:    str  = ""
    reverse: bool = False


@dataclass
class ReverseStmt(Stmt):
    name: str = ""


@dataclass
class SetDictStmt(Stmt):
    dict_name: str = ""
    key:       Any = None  # Expr
    value:     Any = None  # Expr


@dataclass
class SetListStmt(Stmt):
    list_name: str = ""
    index:     Any = None  # Expr
    value:     Any = None  # Expr


@dataclass
class GlobalStmt(Stmt):
    names: List[str] = field(default_factory=list)


@dataclass
class IncludeStmt(Stmt):
    path: Any = None  # Expr


@dataclass
class UseStmt(Stmt):
    library: str = ""
    alias:   Optional[str] = None


@dataclass
class WriteFileStmt(Stmt):
    content: Any = None  # Expr
    path:    Any = None  # Expr


@dataclass
class AppendFileStmt(Stmt):
    content: Any = None  # Expr
    path:    Any = None  # Expr


@dataclass
class DeleteFileStmt(Stmt):
    path: Any = None  # Expr


@dataclass
class ReadFileStmt(Stmt):
    path:   Any = None  # Expr
    target: str = ""
    mode:   str = "text"  # text lines csv json


@dataclass
class WriteCsvStmt(Stmt):
    data: str = ""
    path: Any = None  # Expr


@dataclass
class WriteJsonStmt(Stmt):
    data: str = ""
    path: Any = None  # Expr


@dataclass
class FetchStmt(Stmt):
    url:     Any = None  # Expr
    target:  str = ""
    as_json: bool = False


@dataclass
class ValidateStmt(Stmt):
    kind:   str = ""    # email phone number range not_empty
    source: str = ""
    target: str = ""
    low:    Optional[Any] = None
    high:   Optional[Any] = None


@dataclass
class FindPatternStmt(Stmt):
    pattern: Any = None  # Expr
    source:  str = ""
    target:  str = ""


@dataclass
class ReplacePatternStmt(Stmt):
    pattern:     Any = None  # Expr
    replacement: Any = None  # Expr
    source:      str = ""
    target:      str = ""


@dataclass
class ReplaceStrStmt(Stmt):
    old:    Any = None  # Expr
    new:    Any = None  # Expr
    source: str = ""
    target: str = ""


@dataclass
class SplitStmt(Stmt):
    source: str = ""
    sep:    Any = None  # Expr
    target: str = ""


@dataclass
class JoinStmt(Stmt):
    source: str = ""
    sep:    Any = None  # Expr
    target: str = ""


@dataclass
class WaitStmt(Stmt):
    seconds: Any = None  # Expr


@dataclass
class ClearScreenStmt(Stmt):
    pass


@dataclass
class ExitStmt(Stmt):
    pass


@dataclass
class StopStmt(Stmt):
    pass


@dataclass
class SkipStmt(Stmt):
    pass


@dataclass
class RaiseErrorStmt(Stmt):
    message: Any = None  # Expr


@dataclass
class CommentStmt(Stmt):
    text: str = ""


@dataclass
class MultilineStrStmt(Stmt):
    target: str = ""
    lines:  List[str] = field(default_factory=list)


@dataclass
class RunBackgroundStmt(Stmt):
    fn_name: str = ""
    args:    Optional[Any] = None  # Expr


@dataclass
class WaitForAllStmt(Stmt):
    pass


@dataclass
class MakeUniqueStmt(Stmt):
    source: str = ""
    target: str = ""


@dataclass
class FlattenStmt(Stmt):
    source: str = ""
    target: str = ""


@dataclass
class ConvertJsonStmt(Stmt):
    source: str = ""
    target: str = ""


@dataclass
class ParseJsonStmt(Stmt):
    source: str = ""
    target: str = ""


@dataclass
class StoreCsvColumnStmt(Stmt):
    data:   str = ""
    column: Any = None
    target: str = ""


# ─────────────────────────────────────────────
# STATEMENTS — COMPOUND
# ─────────────────────────────────────────────

@dataclass
class IfStmt(Stmt):
    condition:  Any = None               # Expr
    body:       List[Stmt] = field(default_factory=list)
    elseifs:    List[Tuple[Any, List[Stmt]]] = field(default_factory=list)
    else_body:  Optional[List[Stmt]] = None


@dataclass
class RepeatStmt(Stmt):
    count: Any = None  # Expr
    body:  List[Stmt] = field(default_factory=list)


@dataclass
class ForEachStmt(Stmt):
    var:      str = ""
    iterable: str = ""
    body:     List[Stmt] = field(default_factory=list)
    reverse:  bool = False


@dataclass
class CountStmt(Stmt):
    start: Any = None  # Expr
    end:   Any = None  # Expr
    var:   str = ""
    body:  List[Stmt] = field(default_factory=list)


@dataclass
class WhileStmt(Stmt):
    condition: Any = None  # Expr
    body:      List[Stmt] = field(default_factory=list)


@dataclass
class DefineStmt(Stmt):
    name:   str = ""
    params: List[Tuple[str, Optional[Any]]] = field(default_factory=list)
    body:   List[Stmt] = field(default_factory=list)


@dataclass
class TryStmt(Stmt):
    body:       List[Stmt] = field(default_factory=list)
    catch_body: List[Stmt] = field(default_factory=list)


# ─────────────────────────────────────────────
# AST PRINTER (for debugging)
# ─────────────────────────────────────────────

def print_ast(node, indent=0):
    prefix = "  " * indent
    if isinstance(node, list):
        for item in node:
            print_ast(item, indent)
        return
    if not isinstance(node, Node):
        print(f"{prefix}{node!r}")
        return

    print(f"{prefix}{node.node_type()}  L{node.line_num}")
    for fname in node.__dataclass_fields__:
        if fname in ("line_num", "col_num", "source_line"):
            continue
        val = getattr(node, fname)
        if isinstance(val, Node):
            print(f"{prefix}  {fname}:")
            print_ast(val, indent + 2)
        elif isinstance(val, list) and val and isinstance(val[0], Node):
            print(f"{prefix}  {fname}: [{len(val)} items]")
            for item in val:
                print_ast(item, indent + 2)
        elif isinstance(val, list) and val and isinstance(val[0], tuple):
            # List of tuples e.g. IfStmt.elseifs: List[Tuple[Expr, List[Stmt]]]
            print(f"{prefix}  {fname}: [{len(val)} branches]")
            for i, tup in enumerate(val):
                print(f"{prefix}    branch {i}:")
                for part in tup:
                    print_ast(part, indent + 3)
        else:
            print(f"{prefix}  {fname}: {val!r}")
