"""
lexer.py — Saral Language Tokenizer v4.0
Converts raw Saral source text into a clean token stream.
Every token carries its exact line and column number.
"""

import re
from dataclasses import dataclass
from typing import List, Optional


# ─────────────────────────────────────────────
# TOKEN TYPES
# ─────────────────────────────────────────────

class TT:
    """Token Types — every possible token in Saral."""

    # Literals
    NUMBER  = "NUMBER"
    STRING  = "STRING"
    BOOL    = "BOOL"

    # Identifier (variable/function name)
    NAME    = "NAME"

    # Multi-word keywords (matched as single tokens)
    # Listed longest-first so longer matches win
    STORE_TEXT_BLOCK   = "STORE_TEXT_BLOCK"
    END_BLOCK          = "END_BLOCK"
    OTHERWISE_IF       = "OTHERWISE_IF"
    FOR_EACH           = "FOR_EACH"
    MAKE_LIST          = "MAKE_LIST"
    MAKE_DICT          = "MAKE_DICT"
    MAKE_UNIQUE        = "MAKE_UNIQUE"
    STORE_RESULT       = "STORE_RESULT"
    MULTIPLE_RESULT    = "MULTIPLE_RESULT"
    RUN_BACKGROUND     = "RUN_BACKGROUND"
    WAIT_FOR_ALL       = "WAIT_FOR_ALL"
    SHOW_PROGRESS      = "SHOW_PROGRESS"
    SHOW_ERROR         = "SHOW_ERROR"
    SHOW_BLANK         = "SHOW_BLANK"
    RETURN_NOTHING     = "RETURN_NOTHING"
    ASK_AI             = "ASK_AI"
    ASK_NUMBER         = "ASK_NUMBER"
    CURRENT_TIME       = "CURRENT_TIME"
    CURRENT_YEAR       = "CURRENT_YEAR"
    CURRENT_MONTH      = "CURRENT_MONTH"
    CURRENT_DAY        = "CURRENT_DAY"
    READ_FILE          = "READ_FILE"
    READ_LINES         = "READ_LINES"
    READ_CSV           = "READ_CSV"
    READ_JSON          = "READ_JSON"
    WRITE_FILE         = "WRITE_FILE"    # handled via WRITE token
    DELETE_FILE        = "DELETE_FILE"
    WRITE_CSV          = "WRITE_CSV"
    WRITE_JSON         = "WRITE_JSON"
    FETCH_JSON         = "FETCH_JSON"
    FIND_PATTERN       = "FIND_PATTERN"
    REPLACE_PATTERN    = "REPLACE_PATTERN"
    PARSE_JSON         = "PARSE_JSON"
    CONVERT_TO_JSON    = "CONVERT_TO_JSON"
    CHECK_THAT         = "CHECK_THAT"
    NOT_EMPTY          = "NOT_EMPTY"
    VALID_EMAIL        = "VALID_EMAIL"
    VALID_PHONE        = "VALID_PHONE"
    IN_REVERSE         = "IN_REVERSE"
    AND_STORE_IN       = "AND_STORE_IN"
    PADDED_LEFT        = "PADDED_LEFT"
    PADDED_RIGHT       = "PADDED_RIGHT"
    PADDED_CENTER      = "PADDED_CENTER"
    STOP_PROGRAM       = "STOP_PROGRAM"
    EXIT_PROGRAM       = "EXIT_PROGRAM"
    CLEAR_SCREEN       = "CLEAR_SCREEN"
    RAISE_ERROR        = "RAISE_ERROR"
    DEEP_VALUE         = "DEEP_VALUE"
    COUNT_FROM         = "COUNT_FROM"
    FLATTEN            = "FLATTEN"

    # Single-word keywords
    STORE      = "STORE"
    IN         = "IN"
    SHOW       = "SHOW"
    ASK        = "ASK"
    IF         = "IF"
    OTHERWISE  = "OTHERWISE"
    DONE       = "DONE"
    REPEAT     = "REPEAT"
    TIMES      = "TIMES"
    FOR        = "FOR"
    EACH       = "EACH"
    WHILE      = "WHILE"
    DEFINE     = "DEFINE"
    USING      = "USING"
    END        = "END"
    RETURN     = "RETURN"
    CALL       = "CALL"
    WITH       = "WITH"
    ADD        = "ADD"
    TO         = "TO"
    REMOVE     = "REMOVE"
    FROM       = "FROM"
    MAKE       = "MAKE"
    LIST       = "LIST"
    CALLED     = "CALLED"
    DICTIONARY = "DICTIONARY"
    SORT       = "SORT"
    REVERSE    = "REVERSE"
    GLOBAL     = "GLOBAL"
    INCLUDE    = "INCLUDE"
    USE        = "USE"
    AS         = "AS"
    BY         = "BY"
    INCREASE   = "INCREASE"
    DECREASE   = "DECREASE"
    READ       = "READ"
    WRITE      = "WRITE"
    APPEND     = "APPEND"
    DELETE     = "DELETE"
    FILE       = "FILE"
    CSV        = "CSV"
    JSON       = "JSON"
    FETCH      = "FETCH"
    PATTERN    = "PATTERN"
    FIND       = "FIND"
    REPLACE    = "REPLACE"
    SPLIT      = "SPLIT"
    JOIN       = "JOIN"
    CHECK      = "CHECK"
    THAT       = "THAT"
    IS         = "IS"
    VALID      = "VALID"
    EMAIL      = "EMAIL"
    PHONE      = "PHONE"
    NUMBER_KW  = "NUMBER_KW"   # 'number' as keyword vs NUMBER literal
    BETWEEN    = "BETWEEN"
    NOT        = "NOT"
    EMPTY      = "EMPTY"
    A          = "A"
    AN         = "AN"
    RESULT     = "RESULT"
    OF         = "OF"
    MULTIPLE   = "MULTIPLE"
    TODAY      = "TODAY"
    NOW        = "NOW"
    CURRENT    = "CURRENT"
    UPPERCASE  = "UPPERCASE"
    LOWERCASE  = "LOWERCASE"
    TRIMMED    = "TRIMMED"
    REVERSED   = "REVERSED"
    LENGTH     = "LENGTH"
    PADDED     = "PADDED"
    LEFT       = "LEFT"
    RIGHT      = "RIGHT"
    CENTER     = "CENTER"
    PLACES     = "PLACES"
    SQRT       = "SQRT"
    SQUARE     = "SQUARE"
    CUBE       = "CUBE"
    ROUND      = "ROUND"
    FLOOR      = "FLOOR"
    CEILING    = "CEILING"
    ABSOLUTE   = "ABSOLUTE"
    SIN        = "SIN"
    COS        = "COS"
    TAN        = "TAN"
    LOG        = "LOG"
    RANDOM     = "RANDOM"
    SUM        = "SUM"
    AVERAGE    = "AVERAGE"
    MAXIMUM    = "MAXIMUM"
    MINIMUM    = "MINIMUM"
    ITEM       = "ITEM"
    ITEMS      = "ITEMS"
    FIRST      = "FIRST"
    LAST       = "LAST"
    DEEP       = "DEEP"
    VALUE      = "VALUE"
    THEN       = "THEN"
    PROGRESS   = "PROGRESS"
    ERROR      = "ERROR"
    BLANK      = "BLANK"
    TEXT       = "TEXT"
    DECIMAL    = "DECIMAL"
    BOOLEAN    = "BOOLEAN"
    TRY        = "TRY"
    CATCH      = "CATCH"
    RAISE      = "RAISE"
    RUN        = "RUN"
    BACKGROUND = "BACKGROUND"
    WAIT       = "WAIT"
    ALL        = "ALL"
    SECONDS    = "SECONDS"
    SECOND     = "SECOND"
    CLEAR      = "CLEAR"
    SCREEN     = "SCREEN"
    EXIT       = "EXIT"
    STOP       = "STOP"
    SKIP       = "SKIP"
    AI         = "AI"
    MATCHES    = "MATCHES"
    EXISTS     = "EXISTS"
    COUNT      = "COUNT"
    UNIQUE     = "UNIQUE"
    FLATTEN_KW = "FLATTEN_KW"
    AND        = "AND"
    OR         = "OR"
    COLOR_RED  = "COLOR_RED"
    COLOR_GREEN= "COLOR_GREEN"
    COLOR_YELLOW="COLOR_YELLOW"
    COLOR_BLUE = "COLOR_BLUE"
    COLOR_MAGENTA="COLOR_MAGENTA"
    COLOR_CYAN = "COLOR_CYAN"
    COLOR_WHITE= "COLOR_WHITE"
    COLOR_BOLD = "COLOR_BOLD"
    PARSE      = "PARSE"
    CONVERT    = "CONVERT"
    LINES      = "LINES"
    COLUMN     = "COLUMN"
    RAW        = "RAW"
    STORE_KW   = "STORE_KW"
    SET_KW     = "SET_KW"

    # Operators
    PLUS    = "PLUS"
    MINUS   = "MINUS"
    STAR    = "STAR"
    SLASH   = "SLASH"
    PERCENT = "PERCENT"
    CARET   = "CARET"
    EQ      = "EQ"
    NEQ     = "NEQ"
    GT      = "GT"
    LT      = "LT"
    GTE     = "GTE"
    LTE     = "LTE"
    COMMA   = "COMMA"
    LPAREN  = "LPAREN"
    RPAREN  = "RPAREN"

    # Structure
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"
    EOF     = "EOF"
    UNKNOWN = "UNKNOWN"


# ─────────────────────────────────────────────
# TOKEN DATACLASS
# ─────────────────────────────────────────────

@dataclass
class Token:
    type:    str
    value:   str
    line:    int
    col:     int

    def __repr__(self):
        return f"Token({self.type}, {self.value!r}, L{self.line}:C{self.col})"


# ─────────────────────────────────────────────
# KEYWORD MAP
# Maps lowercase strings to token types
# Order matters for multi-word: longest first
# ─────────────────────────────────────────────

# Multi-word keywords: checked before single words
MULTI_WORD_KEYWORDS = [
    # longest phrases first
    ("store text block in",      TT.STORE_TEXT_BLOCK),
    ("end block",                TT.END_BLOCK),
    ("otherwise if",             TT.OTHERWISE_IF),
    ("for each",                 TT.FOR_EACH),
    ("make list called",         TT.MAKE_LIST),
    ("make dictionary called",   TT.MAKE_DICT),
    ("make unique",              TT.MAKE_UNIQUE),
    ("store multiple result of", TT.MULTIPLE_RESULT),
    ("store result of",          TT.STORE_RESULT),
    ("run in background",        TT.RUN_BACKGROUND),
    ("wait for all",             TT.WAIT_FOR_ALL),
    ("show progress",            TT.SHOW_PROGRESS),
    ("show error",               TT.SHOW_ERROR),
    ("show blank",               TT.SHOW_BLANK),
    ("return nothing",           TT.RETURN_NOTHING),
    ("ask ai",                   TT.ASK_AI),
    ("ask number",               TT.ASK_NUMBER),
    ("current time",             TT.CURRENT_TIME),
    ("current year",             TT.CURRENT_YEAR),
    ("current month",            TT.CURRENT_MONTH),
    ("current day",              TT.CURRENT_DAY),
    ("read lines of",            TT.READ_LINES),
    ("read lines",               TT.READ_LINES),
    ("read csv",                 TT.READ_CSV),
    ("read json",                TT.READ_JSON),
    ("read file",                TT.READ_FILE),
    ("write csv",                TT.WRITE_CSV),
    ("write json",               TT.WRITE_JSON),
    ("delete file",              TT.DELETE_FILE),
    ("fetch json from",          TT.FETCH_JSON),
    ("find pattern",             TT.FIND_PATTERN),
    ("replace pattern",          TT.REPLACE_PATTERN),
    ("parse json",               TT.PARSE_JSON),
    ("convert to json",          TT.CONVERT_TO_JSON),
    ("check that",               TT.CHECK_THAT),
    ("not empty",                TT.NOT_EMPTY),
    ("valid email",              TT.VALID_EMAIL),
    ("valid phone",              TT.VALID_PHONE),
    ("in reverse",               TT.IN_REVERSE),
    ("and store in",             TT.AND_STORE_IN),
    ("padded left to",           TT.PADDED_LEFT),
    ("padded right to",          TT.PADDED_RIGHT),
    ("padded center to",         TT.PADDED_CENTER),
    ("stop program",             TT.STOP_PROGRAM),
    ("exit program",             TT.EXIT_PROGRAM),
    ("clear screen",             TT.CLEAR_SCREEN),
    ("raise error",              TT.RAISE_ERROR),
    ("deep value of",            TT.DEEP_VALUE),
    ("count from",               TT.COUNT_FROM),
    ("flatten",                  TT.FLATTEN),
]

# Single-word keywords
SINGLE_KEYWORDS = {
    "store":      TT.STORE,
    "in":         TT.IN,
    "show":       TT.SHOW,
    "ask":        TT.ASK,
    "if":         TT.IF,
    "otherwise":  TT.OTHERWISE,
    "done":       TT.DONE,
    "repeat":     TT.REPEAT,
    "times":      TT.TIMES,
    "while":      TT.WHILE,
    "define":     TT.DEFINE,
    "using":      TT.USING,
    "end":        TT.END,
    "return":     TT.RETURN,
    "call":       TT.CALL,
    "with":       TT.WITH,
    "add":        TT.ADD,
    "to":         TT.TO,
    "remove":     TT.REMOVE,
    "from":       TT.FROM,
    "make":       TT.MAKE,
    "list":       TT.LIST,
    "called":     TT.CALLED,
    "dictionary": TT.DICTIONARY,
    "set":        TT.SET_KW,
    "sort":       TT.SORT,
    "reverse":    TT.REVERSE,
    "global":     TT.GLOBAL,
    "include":    TT.INCLUDE,
    "use":        TT.USE,
    "as":         TT.AS,
    "by":         TT.BY,
    "increase":   TT.INCREASE,
    "decrease":   TT.DECREASE,
    "read":       TT.READ,
    "write":      TT.WRITE,
    "append":     TT.APPEND,
    "delete":     TT.DELETE,
    "file":       TT.FILE,
    "csv":        TT.CSV,
    "json":       TT.JSON,
    "fetch":      TT.FETCH,
    "pattern":    TT.PATTERN,
    "find":       TT.FIND,
    "replace":    TT.REPLACE,
    "split":      TT.SPLIT,
    "join":       TT.JOIN,
    "check":      TT.CHECK,
    "that":       TT.THAT,
    "is":         TT.IS,
    "valid":      TT.VALID,
    "email":      TT.EMAIL,
    "phone":      TT.PHONE,
    "between":    TT.BETWEEN,
    "not":        TT.NOT,
    "empty":      TT.EMPTY,
    "a":          TT.A,
    "an":         TT.AN,
    "result":     TT.RESULT,
    "of":         TT.OF,
    "multiple":   TT.MULTIPLE,
    "today":      TT.TODAY,
    "now":        TT.NOW,
    "current":    TT.CURRENT,
    "uppercase":  TT.UPPERCASE,
    "lowercase":  TT.LOWERCASE,
    "trimmed":    TT.TRIMMED,
    "reversed":   TT.REVERSED,
    "length":     TT.LENGTH,
    "padded":     TT.PADDED,
    "left":       TT.LEFT,
    "right":      TT.RIGHT,
    "center":     TT.CENTER,
    "places":     TT.PLACES,
    "sqrt":       TT.SQRT,
    "square":     TT.SQUARE,
    "cube":       TT.CUBE,
    "round":      TT.ROUND,
    "floor":      TT.FLOOR,
    "ceiling":    TT.CEILING,
    "absolute":   TT.ABSOLUTE,
    "sin":        TT.SIN,
    "cos":        TT.COS,
    "tan":        TT.TAN,
    "log":        TT.LOG,
    "random":     TT.RANDOM,
    "sum":        TT.SUM,
    "average":    TT.AVERAGE,
    "maximum":    TT.MAXIMUM,
    "minimum":    TT.MINIMUM,
    "item":       TT.ITEM,
    "items":      TT.ITEMS,
    "first":      TT.FIRST,
    "last":       TT.LAST,
    "deep":       TT.DEEP,
    "value":      TT.VALUE,
    "then":       TT.THEN,
    "progress":   TT.PROGRESS,
    "error":      TT.ERROR,
    "blank":      TT.BLANK,
    "text":       TT.TEXT,
    "number":     TT.NUMBER_KW,
    "decimal":    TT.DECIMAL,
    "boolean":    TT.BOOLEAN,
    "try":        TT.TRY,
    "catch":      TT.CATCH,
    "raise":      TT.RAISE,
    "run":        TT.RUN,
    "background": TT.BACKGROUND,
    "wait":       TT.WAIT,
    "all":        TT.ALL,
    "seconds":    TT.SECONDS,
    "second":     TT.SECOND,
    "clear":      TT.CLEAR,
    "screen":     TT.SCREEN,
    "exit":       TT.EXIT,
    "stop":       TT.STOP,
    "skip":       TT.SKIP,
    "ai":         TT.AI,
    "matches":    TT.MATCHES,
    "exists":     TT.EXISTS,
    "count":      TT.COUNT,
    "each":       TT.EACH,
    "for":        TT.FOR,
    "and":        TT.AND,
    "or":         TT.OR,
    "red":        TT.COLOR_RED,
    "green":      TT.COLOR_GREEN,
    "yellow":     TT.COLOR_YELLOW,
    "blue":       TT.COLOR_BLUE,
    "magenta":    TT.COLOR_MAGENTA,
    "cyan":       TT.COLOR_CYAN,
    "white":      TT.COLOR_WHITE,
    "bold":       TT.COLOR_BOLD,
    "parse":      TT.PARSE,
    "convert":    TT.CONVERT,
    "lines":      TT.LINES,
    "column":     TT.COLUMN,
    "true":       TT.BOOL,
    "false":      TT.BOOL,
    "unique":     TT.UNIQUE,
    "flatten":    TT.FLATTEN_KW,
}

COLOR_KEYWORDS = {
    TT.COLOR_RED, TT.COLOR_GREEN, TT.COLOR_YELLOW, TT.COLOR_BLUE,
    TT.COLOR_MAGENTA, TT.COLOR_CYAN, TT.COLOR_WHITE, TT.COLOR_BOLD,
}


# ─────────────────────────────────────────────
# LEXER CLASS
# ─────────────────────────────────────────────

class Lexer:
    def __init__(self, source: str, filename: str = "<program>"):
        self.source   = source
        self.filename = filename
        self.tokens:  List[Token] = []
        self.errors:  List[str]   = []

    def tokenize(self) -> List[Token]:
        """
        Main entry point.
        Returns list of tokens preserving original case in string literals.
        All keywords are lowercased for matching.
        """
        lines = self.source.splitlines()
        self.tokens = []
        in_text_block = False
        text_block_target = None
        text_block_lines = []
        text_block_start_line = 0

        for line_num, raw_line in enumerate(lines, 1):
            stripped_lower = raw_line.strip().lower()

            # ── Multiline text block handling ─────────────
            if stripped_lower.startswith("store text block in "):
                in_text_block   = True
                var_name        = raw_line.strip()[len("store text block in "):].strip()
                text_block_target = var_name.lower()
                text_block_lines  = []
                text_block_start_line = line_num
                self.tokens.append(Token(TT.STORE_TEXT_BLOCK,
                    text_block_target, line_num, 1))
                continue

            if in_text_block:
                if stripped_lower == "end block":
                    in_text_block = False
                    self.tokens.append(Token(TT.END_BLOCK,
                        "\n".join(text_block_lines), line_num, 1))
                    text_block_lines = []
                else:
                    text_block_lines.append(raw_line)
                continue

            # ── Skip blank lines ───────────────────────────
            if not stripped_lower:
                self.tokens.append(Token(TT.NEWLINE, "", line_num, 1))
                continue

            # ── Comments ───────────────────────────────────
            if stripped_lower.startswith("#"):
                self.tokens.append(Token(TT.COMMENT,
                    raw_line.strip(), line_num, 1))
                self.tokens.append(Token(TT.NEWLINE, "", line_num, 1))
                continue

            # ── Tokenize the line ──────────────────────────
            line_tokens = self._tokenize_line(raw_line, line_num)
            self.tokens.extend(line_tokens)
            self.tokens.append(Token(TT.NEWLINE, "", line_num,
                len(raw_line) + 1))

        self.tokens.append(Token(TT.EOF, "", len(lines) + 1, 1))
        return self.tokens

    def _tokenize_line(self, line: str, line_num: int) -> List[Token]:
        """Tokenize a single line into tokens."""
        tokens  = []
        pos     = 0
        stripped_line = line.strip()
        lower_line    = stripped_line.lower()
        col_offset    = len(line) - len(line.lstrip())

        while pos < len(lower_line):
            # Skip whitespace (spaces and tabs)
            if lower_line[pos].isspace():
                pos += 1
                continue

            # ── Comment mid-line ───────────────────────────
            if lower_line[pos] == "#":
                break

            col = col_offset + pos + 1

            # ── String literal ─────────────────────────────
            if lower_line[pos] in ('"', "'"):
                tok, new_pos = self._read_string(
                    stripped_line, pos, line_num, col)
                tokens.append(tok)
                pos = new_pos
                continue

            # ── Number literal ─────────────────────────────
            if lower_line[pos].isdigit() or (
                lower_line[pos] == "-" and
                pos + 1 < len(lower_line) and
                lower_line[pos+1].isdigit() and
                (not tokens or tokens[-1].type not in
                 (TT.NAME, TT.NUMBER, TT.RPAREN))
            ):
                tok, new_pos = self._read_number(
                    lower_line, pos, line_num, col)
                tokens.append(tok)
                pos = new_pos
                continue

            # ── Operators ──────────────────────────────────
            op_tok = self._read_operator(lower_line, pos, line_num, col)
            if op_tok:
                tokens.append(op_tok)
                pos += len(op_tok.value)
                continue

            # ── Multi-word keywords ────────────────────────
            mw_result = self._read_multiword(lower_line, pos, line_num, col)
            if mw_result:
                mw_tok, mw_len = mw_result
                tokens.append(mw_tok)
                pos += mw_len
                continue

            # ── Word (keyword or name) ─────────────────────
            if lower_line[pos].isalpha() or lower_line[pos] == "_":
                tok, new_pos = self._read_word(
                    lower_line, pos, line_num, col)
                tokens.append(tok)
                pos = new_pos
                continue

            # ── Unknown character ──────────────────────────
            tokens.append(Token(TT.UNKNOWN,
                lower_line[pos], line_num, col))
            pos += 1

        return tokens

    def _read_string(self, line: str, pos: int,
                     line_num: int, col: int) -> tuple:
        """Read a string literal preserving original case."""
        quote   = line[pos]
        start   = pos
        pos    += 1
        result  = quote
        while pos < len(line) and line[pos] != quote:
            if line[pos] == "\\" and pos + 1 < len(line):
                result += line[pos] + line[pos+1]
                pos    += 2
            else:
                result += line[pos]
                pos    += 1
        if pos < len(line):
            result += line[pos]
            pos    += 1
        return Token(TT.STRING, result, line_num, col), pos

    def _read_number(self, line: str, pos: int,
                     line_num: int, col: int) -> tuple:
        """Read a numeric literal."""
        start = pos
        if line[pos] == "-":
            pos += 1
        dot_seen = False
        while pos < len(line) and (line[pos].isdigit() or
                                   (line[pos] == "." and not dot_seen)):
            if line[pos] == ".":
                dot_seen = True
            pos += 1
        value = line[start:pos]
        return Token(TT.NUMBER, value, line_num, col), pos

    def _read_operator(self, line: str, pos: int,
                       line_num: int, col: int) -> Optional[Token]:
        """Read an operator token."""
        ops = {
            "!=": TT.NEQ,
            ">=": TT.GTE,
            "<=": TT.LTE,
            "+":  TT.PLUS,
            "-":  TT.MINUS,
            "*":  TT.STAR,
            "/":  TT.SLASH,
            "%":  TT.PERCENT,
            "^":  TT.CARET,
            "=":  TT.EQ,
            ">":  TT.GT,
            "<":  TT.LT,
            ",":  TT.COMMA,
            "(":  TT.LPAREN,
            ")":  TT.RPAREN,
        }
        # Try two-char operators first
        two = line[pos:pos+2]
        if two in ops:
            return Token(ops[two], two, line_num, col)
        one = line[pos:pos+1]
        if one in ops:
            return Token(ops[one], one, line_num, col)
        return None

    def _read_multiword(self, line: str, pos: int,
                        line_num: int, col: int) -> Optional[tuple]:
        """Try to match a multi-word keyword at current position.
        Returns (Token, matched_length) or None.
        """
        remaining = line[pos:]
        for phrase, token_type in MULTI_WORD_KEYWORDS:
            if remaining.startswith(phrase):
                # Make sure it ends at word boundary
                end = pos + len(phrase)
                if end >= len(line) or not (line[end].isalnum() or line[end] == "_"):
                    return Token(token_type, phrase, line_num, col), len(phrase)
        return None

    def _read_word(self, lower_line: str,
                   pos: int, line_num: int, col: int) -> tuple:
        """Read a word and classify as keyword or identifier."""
        start = pos
        while pos < len(lower_line) and (
            lower_line[pos].isalnum() or lower_line[pos] == "_"
        ):
            pos += 1
        word = lower_line[start:pos]

        if word in SINGLE_KEYWORDS:
            tt = SINGLE_KEYWORDS[word]
            # Bool literals keep their original value
            if tt == TT.BOOL:
                return Token(TT.BOOL, word, line_num, col), pos
            return Token(tt, word, line_num, col), pos

        # Not a keyword — it's an identifier (variable/function name)
        return Token(TT.NAME, word, line_num, col), pos


# ─────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────

def tokenize(source: str, filename: str = "<program>") -> List[Token]:
    """Tokenize Saral source and return token list."""
    return Lexer(source, filename).tokenize()


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_src = """
# Test program
store 10 in price
store "Hello World" in greeting
show greeting in green
if price > 5
    show "expensive"
otherwise
    show "cheap"
done
repeat 3 times
    show price
done
define greet using name, title = "Mr"
    show "Hello " + title + " " + name
end
store text block in letter
Dear Arun,
Welcome to Saral.
end block
show letter
"""
    tokens = tokenize(test_src)
    for tok in tokens:
        if tok.type not in (TT.NEWLINE, TT.EOF):
            print(f"  L{tok.line:3}  {tok.type:<20} {tok.value!r}")
