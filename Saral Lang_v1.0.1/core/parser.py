"""
parser.py — Saral Recursive Descent Parser v4.0
Converts token stream into a complete AST.
Every node has exact line/column numbers.
"""

import re
from typing import List, Optional, Tuple, Any
from lexer import Token, TT, tokenize
from ast_nodes import *


class ParseError(Exception):
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token   = token
        super().__init__(message)


class Parser:
    def __init__(self, tokens: List[Token], source_lines: List[str],
                 filename: str = "<program>"):
        self.tokens       = [t for t in tokens
                             if t.type not in (TT.NEWLINE, TT.COMMENT)]
        self.all_tokens   = tokens   # with newlines, for line tracking
        self.pos          = 0
        self.source_lines = source_lines
        self.filename     = filename
        self.errors:      List[str] = []

    # ─────────────────────────────────────────
    # TOKEN NAVIGATION
    # ─────────────────────────────────────────

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TT.EOF, "", 0, 0)

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx < len(self.tokens):
            return self.tokens[idx]
        return Token(TT.EOF, "", 0, 0)

    def advance(self) -> Token:
        tok = self.current()
        self.pos += 1
        return tok

    def expect(self, *types) -> Token:
        tok = self.current()
        if tok.type in types:
            return self.advance()
        expected = " or ".join(types)
        raise ParseError(
            f"Expected {expected} but got '{tok.value}' ({tok.type})",
            tok
        )

    def expect_name(self) -> Token:
        """
        Like expect(NAME) but also accepts keywords used as variable names.
        In Saral, 'first', 'last', 'item', 'result' etc are valid variable names.
        """
        tok = self.current()
        if tok.type == TT.NAME:
            return self.advance()
        # Allow any non-structural keyword as a variable name
        NON_STRUCTURAL = {
            TT.STORE, TT.SHOW, TT.ASK, TT.IF, TT.REPEAT,
            TT.FOR_EACH, TT.WHILE, TT.DEFINE, TT.DONE, TT.END,
            TT.RETURN, TT.CALL, TT.ADD, TT.REMOVE,
            TT.MAKE_LIST, TT.MAKE_DICT, TT.SORT, TT.REVERSE,
            TT.GLOBAL, TT.INCLUDE, TT.USE, TT.TRY, TT.CATCH,
            TT.INCREASE, TT.DECREASE, TT.EOF, TT.NEWLINE,
            TT.COMMENT, TT.UNKNOWN, TT.NUMBER, TT.STRING, TT.BOOL,
            TT.LPAREN, TT.RPAREN, TT.COMMA,
            TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
            TT.PERCENT, TT.CARET, TT.EQ, TT.NEQ,
            TT.GT, TT.LT, TT.GTE, TT.LTE,
        }
        if tok.type not in NON_STRUCTURAL:
            # it's a keyword being used as a variable name
            return self.advance()
        raise ParseError(
            f"Expected a variable name but got '{tok.value}'",
            tok
        )

    def match(self, *types) -> bool:
        return self.current().type in types

    def match_value(self, *values) -> bool:
        return self.current().value in values

    def source_line(self, line_num: int) -> str:
        if 0 < line_num <= len(self.source_lines):
            return self.source_lines[line_num - 1]
        return ""

    # ─────────────────────────────────────────
    # MAIN PARSE
    # ─────────────────────────────────────────

    def parse(self) -> Program:
        body = []
        while not self.match(TT.EOF):
            try:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            except ParseError as e:
                self.errors.append(
                    f"Line {e.token.line}: {e.message}"
                )
                self._skip_to_next_statement()

        ln = body[0].line_num if body else 1
        return Program(body=body, line_num=ln)

    def _tokens_contain_of_after_item(self) -> bool:
        """Check if 'item X of' pattern follows (not just 'item padded')."""
        # look 2-3 tokens ahead for OF
        for offset in range(1, 4):
            tok = self.peek(offset)
            if tok.type == TT.OF:
                return True
            if tok.type in (TT.PADDED_LEFT, TT.PADDED_RIGHT, TT.PADDED_CENTER,
                             TT.AS, TT.IN, TT.EOF, TT.NEWLINE):
                return False
        return False

    def _dispatch_store_result(self) -> Stmt:
        """Called when first token is STORE_RESULT (multi-word)."""
        ln = self.current().line
        return self.parse_store_result(ln)

    def _dispatch_multiple_result(self) -> Stmt:
        """Called when first token is MULTIPLE_RESULT (multi-word)."""
        ln = self.current().line
        return self.parse_store_multiple_result(ln)

    def _parse_simple_primary(self) -> Any:
        """
        Parse a primary expression without consuming AS keyword.
        Used in count from X to Y as var — Y must not consume AS.
        Handles: numbers, variables, parenthesised expressions.
        Does NOT consume AS (to avoid count from X to n as i failing).
        """
        tok = self.current()
        if tok.type == TT.NUMBER:
            self.advance()
            val = float(tok.value) if "." in tok.value else int(tok.value)
            return NumberLiteral(value=val, line_num=tok.line)
        if tok.type == TT.MINUS:
            self.advance()
            inner = self._parse_simple_primary()
            return UnaryOp(op="-", operand=inner, line_num=tok.line)
        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN)
            return expr
        if tok.type == TT.NAME:
            self.advance()
            return Identifier(name=tok.value, line_num=tok.line)
        # for any other token — treat as name (keyword used as variable)
        if tok.type not in {
            TT.EOF, TT.NEWLINE, TT.COMMENT,
            TT.DONE, TT.END, TT.OTHERWISE, TT.OTHERWISE_IF,
            TT.CATCH, TT.AS,
        }:
            self.advance()
            return Identifier(name=tok.value, line_num=tok.line)
        # give up gracefully
        raise ParseError(f"Expected a number or variable, got '{tok.value}'", tok)

    def _skip_to_next_statement(self):
        """On error, skip tokens until we find a known statement start."""
        STARTERS = {
            TT.STORE, TT.STORE_RESULT, TT.MULTIPLE_RESULT,
            TT.SHOW, TT.SHOW_ERROR, TT.SHOW_BLANK, TT.SHOW_PROGRESS,
            TT.ASK, TT.ASK_AI, TT.ASK_NUMBER,
            TT.IF, TT.REPEAT, TT.FOR_EACH, TT.WHILE,
            TT.DEFINE, TT.CALL, TT.ADD, TT.REMOVE,
            TT.MAKE_LIST, TT.MAKE_DICT, TT.MAKE_UNIQUE,
            TT.SORT, TT.REVERSE, TT.GLOBAL, TT.INCLUDE,
            TT.USE, TT.TRY, TT.RETURN, TT.RETURN_NOTHING,
            TT.INCREASE, TT.DECREASE, TT.STORE_TEXT_BLOCK,
            TT.COUNT_FROM, TT.WRITE_CSV, TT.WRITE_JSON,
            TT.READ_FILE, TT.READ_LINES, TT.READ_CSV, TT.READ_JSON,
            TT.DELETE_FILE, TT.FETCH, TT.FETCH_JSON,
            TT.FIND_PATTERN, TT.REPLACE_PATTERN, TT.CHECK_THAT,
            TT.RAISE_ERROR, TT.RUN_BACKGROUND, TT.WAIT_FOR_ALL,
            TT.STOP_PROGRAM, TT.EXIT_PROGRAM, TT.CLEAR_SCREEN,
            TT.STOP, TT.SKIP, TT.FLATTEN, TT.SET_KW,
            TT.CURRENT, TT.BACKGROUND, TT.UNIQUE,
            TT.EOF,
        }
        while not self.match(TT.EOF) and \
              self.current().type not in STARTERS:
            self.advance()

    # ─────────────────────────────────────────
    # STATEMENT DISPATCH
    # ─────────────────────────────────────────

    def parse_statement(self) -> Optional[Stmt]:
        tok = self.current()

        if tok.type == TT.STORE_RESULT:    return self._dispatch_store_result()
        if tok.type == TT.MULTIPLE_RESULT: return self._dispatch_multiple_result()
        if tok.type == TT.STORE:           return self.parse_store()
        if tok.type == TT.SHOW_ERROR:      return self.parse_show_error()
        if tok.type == TT.SHOW_BLANK:      return self.parse_show_blank()
        if tok.type == TT.SHOW_PROGRESS:   return self.parse_show_progress()
        if tok.type == TT.SHOW:            return self.parse_show()
        if tok.type == TT.ASK_AI:          return self.parse_ask_ai()
        if tok.type == TT.ASK_NUMBER:      return self.parse_ask_number()
        if tok.type == TT.ASK:             return self.parse_ask()
        if tok.type == TT.IF:              return self.parse_if()
        if tok.type == TT.REPEAT:          return self.parse_repeat()
        if tok.type == TT.FOR_EACH:        return self.parse_for_each()
        if tok.type == TT.COUNT_FROM:      return self.parse_count()
        if tok.type == TT.WHILE:           return self.parse_while()
        if tok.type == TT.DEFINE:          return self.parse_define()
        if tok.type == TT.RETURN_NOTHING:
            t = self.advance()
            return ReturnStmt(values=[], line_num=t.line)
        if tok.type == TT.RETURN:          return self.parse_return()
        if tok.type == TT.CALL:            return self.parse_call()
        if tok.type == TT.ADD:             return self.parse_add()
        if tok.type == TT.REMOVE:          return self.parse_remove()
        if tok.type == TT.MAKE_LIST:       return self.parse_make_list()
        if tok.type == TT.MAKE_DICT:       return self.parse_make_dict()
        if tok.type == TT.MAKE_UNIQUE:     return self.parse_make_unique()
        if tok.type == TT.SORT:            return self.parse_sort()
        if tok.type == TT.SET_KW:          return self.parse_set_dict()
        if tok.type == TT.REVERSE:         return self.parse_reverse()
        if tok.type == TT.GLOBAL:          return self.parse_global()
        if tok.type == TT.INCLUDE:         return self.parse_include()
        if tok.type == TT.USE:             return self.parse_use()
        if tok.type == TT.WRITE:           return self.parse_write()
        if tok.type == TT.APPEND:          return self.parse_append()
        if tok.type == TT.DELETE_FILE:     return self.parse_delete_file()
        if tok.type == TT.READ_FILE:       return self.parse_read_file()
        if tok.type == TT.READ_LINES:      return self.parse_read_lines()
        if tok.type == TT.READ_CSV:        return self.parse_read_csv()
        if tok.type == TT.READ_JSON:       return self.parse_read_json()
        if tok.type == TT.FETCH_JSON:      return self.parse_fetch_json()
        if tok.type == TT.FETCH:           return self.parse_fetch()
        if tok.type == TT.FIND_PATTERN:    return self.parse_find_pattern()
        if tok.type == TT.REPLACE_PATTERN: return self.parse_replace_pattern()
        if tok.type == TT.REPLACE:         return self.parse_replace_str()
        if tok.type == TT.SPLIT:           return self.parse_split()
        if tok.type == TT.JOIN:            return self.parse_join()
        if tok.type == TT.CHECK_THAT:      return self.parse_validate()
        if tok.type == TT.PARSE_JSON:      return self.parse_parse_json()
        if tok.type == TT.CONVERT:         return self.parse_convert_stmt()
        if tok.type == TT.CONVERT_TO_JSON: return self.parse_convert_json()
        if tok.type == TT.INCREASE:        return self.parse_increase()
        if tok.type == TT.DECREASE:        return self.parse_decrease()
        if tok.type == TT.TRY:             return self.parse_try()
        if tok.type == TT.RAISE_ERROR:     return self.parse_raise_error()
        if tok.type == TT.STORE_TEXT_BLOCK:return self.parse_multiline_str()
        if tok.type == TT.RUN_BACKGROUND:  return self.parse_run_background()
        if tok.type == TT.WAIT_FOR_ALL:
            t = self.advance()
            return WaitForAllStmt(line_num=t.line)
        if tok.type == TT.WAIT:            return self.parse_wait()
        if tok.type == TT.CLEAR_SCREEN:
            t = self.advance()
            return ClearScreenStmt(line_num=t.line)
        if tok.type == TT.STOP_PROGRAM or tok.type == TT.EXIT_PROGRAM:
            t = self.advance()
            return ExitStmt(line_num=t.line)
        if tok.type == TT.STOP:
            t = self.advance()
            return StopStmt(line_num=t.line)
        if tok.type == TT.SKIP:
            t = self.advance()
            return SkipStmt(line_num=t.line)
        if tok.type == TT.FLATTEN:
            return self.parse_flatten()

        # Unknown token
        raise ParseError(
            f"I don't understand '{tok.value}' — "
            f"try starting with store, show, ask, if, repeat...",
            tok
        )

    # ─────────────────────────────────────────
    # STORE STATEMENT (most complex dispatcher)
    # ─────────────────────────────────────────

    def parse_store(self) -> Stmt:
        tok = self.advance()  # consume STORE
        ln  = tok.line

        # store text block — handled before store
        # (already dispatched via STORE_TEXT_BLOCK token)

        # Detect special store patterns by lookahead
        # store TODAY/NOW/CURRENT in var
        if self.match(TT.TODAY, TT.NOW):
            kind = self.advance().value
            self.expect(TT.IN)
            target = self.expect_name().value
            expr   = DateExpr(kind=kind, line_num=ln)
            return StoreStmt(target=target, value=expr, line_num=ln,
                             source_line=self.source_line(ln))

        if self.match(TT.CURRENT_TIME, TT.CURRENT_YEAR,
                      TT.CURRENT_MONTH, TT.CURRENT_DAY):
            kind = self.advance().type.lower()  # current_time etc
            self.expect(TT.IN)
            target = self.expect_name().value
            expr   = DateExpr(kind=kind, line_num=ln)
            return StoreStmt(target=target, value=expr, line_num=ln,
                             source_line=self.source_line(ln))

        # store RANDOM NUMBER [from A to B] in target
        if self.match(TT.RANDOM):
            return self.parse_store_random(ln)

        # store SQRT/SIN/COS/TAN/LOG/FLOOR/CEILING/ABSOLUTE of expr in var
        if self.match(TT.SQRT, TT.SIN, TT.COS, TT.TAN, TT.LOG,
                      TT.FLOOR, TT.CEILING, TT.ABSOLUTE,
                      TT.SQUARE, TT.CUBE):
            return self.parse_store_mathfn(ln)

        # store ROUND of expr [to N places] in var
        if self.match(TT.ROUND):
            return self.parse_store_round(ln)

        # store SUM/AVERAGE/MAXIMUM/MINIMUM of list in var
        if self.match(TT.SUM, TT.AVERAGE, TT.MAXIMUM, TT.MINIMUM):
            fn   = self.advance().value
            self.expect(TT.OF)
            name = self.expect_name().value
            self.expect(TT.IN)
            tgt  = self.expect_name().value
            return StoreStmt(
                target=tgt,
                value=AggregateExpr(fn=fn, list_name=name, line_num=ln),
                line_num=ln, source_line=self.source_line(ln))

        # store UPPERCASE/LOWERCASE/TRIMMED/REVERSED/LENGTH of X in var
        if self.match(TT.UPPERCASE, TT.LOWERCASE, TT.TRIMMED,
                      TT.LENGTH, TT.REVERSED):
            return self.parse_store_stringop(ln)

        # store ITEM N/var of list in var
        # BUT: "store item padded right..." means item is a variable name
        # Distinguish: "store item N of" vs "store item padded/as/in"
        if self.match(TT.ITEM) and self.peek().type in (
            TT.NUMBER, TT.NAME
        ) and self._tokens_contain_of_after_item():
            return self.parse_store_item(ln)

        # store ITEMS N to M of list in var
        if self.match(TT.ITEMS):
            return self.parse_store_items(ln)

        # store FIRST/LAST N of list in var
        if self.match(TT.FIRST, TT.LAST):
            return self.parse_store_firstlast(ln)

        # store DEEP VALUE of key then key in dict in var
        if self.match(TT.DEEP_VALUE):
            return self.parse_store_deep(ln)

        # store COLUMN "key" of data in var (CSV column)
        if self.match(TT.COLUMN):
            self.advance()
            key   = self.parse_expr()
            self.expect(TT.OF)
            data  = self.expect_name().value
            self.expect(TT.IN)
            tgt   = self.expect_name().value
            return StoreCsvColumnStmt(data=data, column=key,
                                      target=tgt, line_num=ln)

        # store VALUE of key in dict in var
        if self.match(TT.VALUE):
            return self.parse_store_value(ln)

        # store expr AS type IN var
        # store expr IN var
        expr = self.parse_expr()

        # Check for AS type
        if self.match(TT.AS):
            self.advance()
            type_kw = self.current().value
            self.advance()
            self.expect(TT.IN)
            tgt = self.expect_name().value
            return StoreStmt(
                target=tgt,
                value=AsTypeExpr(value=expr, type_kw=type_kw, line_num=ln),
                line_num=ln, source_line=self.source_line(ln))

        # check for PADDED
        if self.match(TT.PADDED_LEFT, TT.PADDED_RIGHT, TT.PADDED_CENTER):
            direction_map = {
                TT.PADDED_LEFT:   "left",
                TT.PADDED_RIGHT:  "right",
                TT.PADDED_CENTER: "center",
            }
            direction = direction_map[self.current().type]
            self.advance()
            width = int(self.expect(TT.NUMBER).value)
            self.expect(TT.IN)
            tgt = self.expect_name().value
            return StoreStmt(
                target=tgt,
                value=PadExpr(direction=direction, value=expr,
                              width=width, line_num=ln),
                line_num=ln, source_line=self.source_line(ln))

        self.expect(TT.IN)
        target = self.expect_name().value
        return StoreStmt(target=target, value=expr, line_num=ln,
                         source_line=self.source_line(ln))

    def parse_store_result(self, ln: int) -> Stmt:
        self.advance()  # STORE_RESULT (multi-word token: "store result of")
        fn_name = self.expect(TT.NAME).value
        args = None
        if self.match(TT.WITH):
            self.advance()
            first = self.parse_expr()
            if self.match(TT.COMMA):
                arg_list = [first]
                while self.match(TT.COMMA):
                    self.advance()
                    arg_list.append(self.parse_expr())
                args = arg_list
            else:
                args = first
        self.expect(TT.IN)
        target = self.expect_name().value
        return StoreResultStmt(target=target, fn_name=fn_name, args=args,
                               line_num=ln, source_line=self.source_line(ln))

    def parse_store_multiple_result(self, ln: int) -> Stmt:
        self.advance()  # MULTIPLE_RESULT (multi-word token)
        fn_name = self.expect(TT.NAME).value
        args = None
        if self.match(TT.WITH):
            self.advance()
            first = self.parse_expr()
            if self.match(TT.COMMA):
                arg_list = [first]
                while self.match(TT.COMMA):
                    self.advance()
                    arg_list.append(self.parse_expr())
                # collect until IN
                args = arg_list
            else:
                args = first
        self.expect(TT.IN)
        targets = [self.expect_name().value]
        while self.match(TT.COMMA):
            self.advance()
            targets.append(self.expect_name().value)
        return StoreMultipleResultStmt(targets=targets, fn_name=fn_name,
                                       args=args, line_num=ln,
                                       source_line=self.source_line(ln))

    def parse_store_mathfn(self, ln: int) -> Stmt:
        fn  = self.advance().value  # sqrt sin cos etc
        self.expect(TT.OF)
        arg = self.parse_expr()
        self.expect(TT.IN)
        tgt = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=MathFnExpr(fn=fn, arg=arg, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_round(self, ln: int) -> Stmt:
        self.advance()  # round
        self.expect(TT.OF)
        arg    = self.parse_expr()
        places = None
        if self.match(TT.TO):
            self.advance()
            places = int(self.expect(TT.NUMBER).value)
            self.expect(TT.PLACES)
        self.expect(TT.IN)
        tgt = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=MathFnExpr(fn="round", arg=arg, places=places, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_random(self, ln: int) -> Stmt:
        self.advance()  # random
        # skip optional 'number' keyword
        if self.match(TT.NUMBER_KW):
            self.advance()
        low = high = None
        if self.match(TT.FROM):
            self.advance()
            low  = self._parse_simple_primary()
            self.expect(TT.TO)
            high = self._parse_simple_primary()
        elif self.match(TT.BETWEEN):
            self.advance()
            low  = self._parse_simple_primary()
            # accept 'and' between the two bounds
            if self.match(TT.AND):
                self.advance()
            high = self._parse_simple_primary()
        self.expect(TT.IN)
        tgt = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=RandomExpr(low=low, high=high, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_stringop(self, ln: int) -> Stmt:
        op  = self.advance().value
        if self.match(TT.OF): self.advance()  # "of" is optional
        arg = self.parse_expr()
        self.expect(TT.IN)
        tgt = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=StringOpExpr(op=op, arg=arg, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_item(self, ln: int) -> Stmt:
        self.advance()  # item
        idx  = self.parse_expr()
        self.expect(TT.OF)
        name = self.expect_name().value
        self.expect(TT.IN)
        tgt  = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=ListOpExpr(op="item", list_name=name,
                             index=idx, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_items(self, ln: int) -> Stmt:
        self.advance()  # items
        start = self.parse_expr()
        self.expect(TT.TO)
        end   = self.parse_expr()
        self.expect(TT.OF)
        name  = self.expect_name().value
        self.expect(TT.IN)
        tgt   = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=ListOpExpr(op="items", list_name=name,
                             start=start, end=end, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_firstlast(self, ln: int) -> Stmt:
        op   = self.advance().value  # first or last
        n    = self.parse_expr()
        # allow optional 'items' or 'item' word: "first 2 items of" or "first 2 of"
        if self.match(TT.ITEMS, TT.ITEM):
            self.advance()
        self.expect(TT.OF)
        name = self.expect_name().value
        self.expect(TT.IN)
        tgt  = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=ListOpExpr(op=op, list_name=name,
                             start=n, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_deep(self, ln: int) -> Stmt:
        self.advance()  # deep value of (multi-word token)
        keys  = [self.parse_expr()]
        while self.match(TT.THEN):
            self.advance()
            keys.append(self.parse_expr())
        self.expect(TT.IN)
        dict_ = self.expect_name().value
        self.expect(TT.IN)
        tgt   = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=DeepGetExpr(dict_name=dict_, keys=keys, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    def parse_store_value(self, ln: int) -> Stmt:
        self.advance()  # value
        self.expect(TT.OF)
        key   = self.parse_expr()
        self.expect(TT.IN)
        dict_ = self.expect_name().value
        self.expect(TT.IN)
        tgt   = self.expect_name().value
        return StoreStmt(
            target=tgt,
            value=DictOpExpr(dict_name=dict_, key=key, line_num=ln),
            line_num=ln, source_line=self.source_line(ln))

    # ─────────────────────────────────────────
    # SHOW STATEMENTS
    # ─────────────────────────────────────────

    def parse_show_error(self) -> Stmt:
        tok = self.advance()
        return ShowErrorStmt(line_num=tok.line)

    def parse_show_blank(self) -> Stmt:
        tok = self.advance()
        # accept optional 'line' word: "show blank" and "show blank line" both work
        if self.match(TT.NAME) and self.current().value.lower() == "line":
            self.advance()
        return ShowBlankStmt(line_num=tok.line)

    def parse_show_progress(self) -> Stmt:
        tok = self.advance()
        current = self.parse_expr()
        self.expect(TT.OF)
        total   = self.parse_expr()
        return ShowProgressStmt(current=current, total=total,
                                line_num=tok.line)

    def parse_show(self) -> Stmt:
        tok   = self.advance()
        value = self.parse_expr()
        color = None
        if self.match(TT.IN) and self.peek().type in {
            TT.COLOR_RED, TT.COLOR_GREEN, TT.COLOR_YELLOW, TT.COLOR_BLUE,
            TT.COLOR_MAGENTA, TT.COLOR_CYAN, TT.COLOR_WHITE, TT.COLOR_BOLD
        }:
            self.advance()
            color = self.advance().value
        return ShowStmt(value=value, color=color,
                        line_num=tok.line,
                        source_line=self.source_line(tok.line))

    # ─────────────────────────────────────────
    # ASK STATEMENTS
    # ─────────────────────────────────────────

    def parse_ask(self) -> Stmt:
        tok    = self.advance()
        prompt = self.parse_expr()
        if self.match(TT.AND_STORE_IN):
            self.advance()
        else:
            self.expect(TT.AND); self.expect(TT.STORE); self.expect(TT.IN)
        target = self.expect_name().value
        return AskStmt(prompt=prompt, target=target,
                       is_number=False, line_num=tok.line,
                       source_line=self.source_line(tok.line))

    def parse_ask_number(self) -> Stmt:
        tok    = self.advance()
        prompt = self.parse_expr()
        if self.match(TT.AND_STORE_IN):
            self.advance()
        else:
            self.expect(TT.AND); self.expect(TT.STORE); self.expect(TT.IN)
        target = self.expect_name().value
        return AskStmt(prompt=prompt, target=target,
                       is_number=True, line_num=tok.line,
                       source_line=self.source_line(tok.line))

    def parse_ask_ai(self) -> Stmt:
        tok    = self.advance()
        prompt = self.parse_expr()
        data   = None
        if self.match(TT.USING):
            self.advance()
            data = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        target = self.expect_name().value
        return AskAiStmt(prompt=prompt, data=data, target=target,
                         line_num=tok.line,
                         source_line=self.source_line(tok.line))

    # ─────────────────────────────────────────
    # CONTROL FLOW
    # ─────────────────────────────────────────

    def parse_if(self) -> Stmt:
        tok       = self.advance()
        condition = self.parse_condition()
        body      = self.parse_block()
        elseifs   = []
        else_body = None

        while self.match(TT.OTHERWISE_IF):
            self.advance()
            elif_cond = self.parse_condition()
            elif_body = self.parse_block()
            elseifs.append((elif_cond, elif_body))

        if self.match(TT.OTHERWISE):
            self.advance()
            else_body = self.parse_block()

        self.expect(TT.DONE)
        return IfStmt(condition=condition, body=body,
                      elseifs=elseifs, else_body=else_body,
                      line_num=tok.line,
                      source_line=self.source_line(tok.line))

    def parse_repeat(self) -> Stmt:
        tok   = self.advance()
        count = self.parse_expr()
        self.expect(TT.TIMES)
        body  = self.parse_block()
        self.expect(TT.DONE)
        return RepeatStmt(count=count, body=body,
                          line_num=tok.line,
                          source_line=self.source_line(tok.line))

    def parse_for_each(self) -> Stmt:
        tok  = self.advance()
        # allow any word as loop variable (item, first, last etc are valid var names)
        var_tok = self.advance()
        var     = var_tok.value
        self.expect(TT.IN)
        iter_name = self.expect_name().value
        reverse = False
        if self.match(TT.IN_REVERSE):
            self.advance()
            reverse = True
        body = self.parse_block()
        self.expect(TT.DONE)
        return ForEachStmt(var=var, iterable=iter_name,
                           body=body, reverse=reverse,
                           line_num=tok.line,
                           source_line=self.source_line(tok.line))

    def parse_count(self) -> Stmt:
        tok   = self.advance()
        # parse start — just a simple literal or identifier, no AS
        start = self._parse_simple_primary()
        self.expect(TT.TO)
        # parse end — just a simple literal or identifier, no AS  
        end   = self._parse_simple_primary()
        self.expect(TT.AS)
        var   = self.expect_name().value
        body  = self.parse_block()
        self.expect(TT.DONE)
        return CountStmt(start=start, end=end, var=var,
                         body=body, line_num=tok.line,
                         source_line=self.source_line(tok.line))

    def parse_while(self) -> Stmt:
        tok       = self.advance()
        condition = self.parse_condition()
        body      = self.parse_block()
        self.expect(TT.DONE)
        return WhileStmt(condition=condition, body=body,
                         line_num=tok.line,
                         source_line=self.source_line(tok.line))

    def parse_block(self) -> List[Stmt]:
        """Parse statements until a block closer or OTHERWISE."""
        CLOSERS = {TT.DONE, TT.END, TT.OTHERWISE, TT.OTHERWISE_IF,
                   TT.CATCH, TT.EOF}
        body = []
        while not self.match(*CLOSERS):
            try:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            except ParseError as e:
                self.errors.append(f"Line {e.token.line}: {e.message}")
                self._skip_to_next_statement()
                if self.match(*CLOSERS):
                    break
        return body

    # ─────────────────────────────────────────
    # DEFINE / CALL / RETURN
    # ─────────────────────────────────────────

    def parse_define(self) -> Stmt:
        tok    = self.advance()
        name   = self.expect_name().value
        params = []
        if self.match(TT.USING):
            self.advance()
            params = self.parse_param_list()
        body = self.parse_define_block()
        self.expect(TT.END)
        return DefineStmt(name=name, params=params, body=body,
                          line_num=tok.line,
                          source_line=self.source_line(tok.line))

    def parse_param_list(self) -> List[Tuple[str, Optional[Any]]]:
        params = []
        name   = self.expect_name().value
        default = None
        if self.match(TT.EQ):
            self.advance()
            default = self.parse_expr()
        params.append((name, default))
        while self.match(TT.COMMA):
            self.advance()
            pname   = self.expect_name().value
            pdefault = None
            if self.match(TT.EQ):
                self.advance()
                pdefault = self.parse_expr()
            params.append((pname, pdefault))
        return params

    def parse_define_block(self) -> List[Stmt]:
        CLOSERS = {TT.END, TT.EOF}
        body = []
        while not self.match(*CLOSERS):
            try:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            except ParseError as e:
                self.errors.append(f"Line {e.token.line}: {e.message}")
                self._skip_to_next_statement()
                if self.match(*CLOSERS):
                    break
        return body

    def parse_return(self) -> Stmt:
        tok    = self.advance()
        values = [self.parse_expr()]
        while self.match(TT.COMMA):
            self.advance()
            values.append(self.parse_expr())
        return ReturnStmt(values=values, line_num=tok.line,
                          source_line=self.source_line(tok.line))

    def parse_call(self) -> Stmt:
        tok  = self.advance()
        name = self.expect_name().value
        args = None
        if self.match(TT.WITH):
            self.advance()
            # parse all args as tuple if comma-separated
            first = self.parse_expr()
            if self.match(TT.COMMA):
                arg_list = [first]
                while self.match(TT.COMMA):
                    self.advance()
                    arg_list.append(self.parse_expr())
                # build comma-joined string for codegen
                args = arg_list  # list of exprs
            else:
                args = first
        return CallStmt(fn_name=name, args=args,
                        line_num=tok.line,
                        source_line=self.source_line(tok.line))

    # ─────────────────────────────────────────
    # LIST / DICT OPERATIONS
    # ─────────────────────────────────────────

    def parse_add(self) -> Stmt:
        tok   = self.advance()
        value = self.parse_expr()
        self.expect(TT.TO)
        tgt   = self.expect_name().value
        return AddStmt(value=value, target=tgt,
                       line_num=tok.line,
                       source_line=self.source_line(tok.line))

    def parse_remove(self) -> Stmt:
        tok   = self.advance()
        value = self.parse_expr()
        self.expect(TT.FROM)
        # check if removing from dictionary
        is_dict = self.match(TT.DICTIONARY)
        if is_dict:
            self.advance()
        tgt = self.expect_name().value
        return RemoveStmt(value=value, target=tgt, is_dict=is_dict,
                          line_num=tok.line,
                          source_line=self.source_line(tok.line))

    def parse_make_list(self) -> Stmt:
        tok  = self.advance()
        name = self.expect_name().value
        return MakeListStmt(name=name, line_num=tok.line,
                            source_line=self.source_line(tok.line))

    def parse_make_dict(self) -> Stmt:
        tok  = self.advance()
        name = self.expect_name().value
        return MakeDictStmt(name=name, line_num=tok.line,
                            source_line=self.source_line(tok.line))

    def parse_make_unique(self) -> Stmt:
        tok  = self.advance()  # MAKE_UNIQUE token
        # Accept: "make unique list from X and store in Y"
        # or:     "make unique list X and store in Y"
        # or:     "make unique X and store in Y"
        if self.match(TT.LIST):
            self.advance()      # skip optional 'list'
        if self.match(TT.FROM):
            self.advance()      # skip optional 'from'
        src  = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        tgt  = self.expect_name().value
        return MakeUniqueStmt(source=src, target=tgt,
                              line_num=tok.line)

    def parse_set_dict(self) -> Stmt:
        """set item IDX of LIST to VALUE  or  set KEY of DICT to VALUE"""
        tok = self.advance()  # SET_KW
        # detect list form: "set item <expr> of <name> to <value>"
        if self.match(TT.ITEM):
            self.advance()  # consume 'item'
            idx = self.parse_expr()
            self.expect(TT.OF)
            list_name = self.expect_name().value
            self.expect(TT.TO)
            value = self.parse_expr()
            return SetListStmt(list_name=list_name, index=idx, value=value,
                               line_num=tok.line,
                               source_line=self.source_line(tok.line))
        # original dict form
        key = self.parse_expr()
        self.expect(TT.OF)
        dict_name = self.expect_name().value
        self.expect(TT.TO)
        value = self.parse_expr()
        return SetDictStmt(dict_name=dict_name, key=key, value=value,
                           line_num=tok.line,
                           source_line=self.source_line(tok.line))

    def parse_sort(self) -> Stmt:
        tok     = self.advance()
        name    = self.expect_name().value
        reverse = False
        if self.match(TT.IN_REVERSE):
            self.advance()
            reverse = True
        return SortStmt(name=name, reverse=reverse,
                        line_num=tok.line,
                        source_line=self.source_line(tok.line))

    def parse_reverse(self) -> Stmt:
        tok  = self.advance()
        name = self.expect_name().value
        return ReverseStmt(name=name, line_num=tok.line,
                           source_line=self.source_line(tok.line))

    # ─────────────────────────────────────────
    # INCREASE / DECREASE / GLOBAL
    # ─────────────────────────────────────────

    def parse_increase(self) -> Stmt:
        tok    = self.advance()
        target = self.expect_name().value
        self.expect(TT.BY)
        amount = self.parse_expr()
        return IncreaseStmt(target=target, amount=amount,
                            line_num=tok.line,
                            source_line=self.source_line(tok.line))

    def parse_decrease(self) -> Stmt:
        tok    = self.advance()
        target = self.expect_name().value
        self.expect(TT.BY)
        amount = self.parse_expr()
        return DecreaseStmt(target=target, amount=amount,
                            line_num=tok.line,
                            source_line=self.source_line(tok.line))

    def parse_global(self) -> Stmt:
        tok   = self.advance()
        names = [self.expect_name().value]
        while self.match(TT.COMMA):
            self.advance()
            names.append(self.expect_name().value)
        return GlobalStmt(names=names, line_num=tok.line,
                          source_line=self.source_line(tok.line))

    # ─────────────────────────────────────────
    # FILE OPERATIONS
    # ─────────────────────────────────────────

    def parse_include(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        return IncludeStmt(path=path, line_num=tok.line)

    def parse_use(self) -> Stmt:
        tok     = self.advance()
        library = self.expect(TT.NAME).value
        alias   = None
        if self.match(TT.AS):
            self.advance()
            alias = self.expect_name().value
        return UseStmt(library=library, alias=alias,
                       line_num=tok.line,
                       source_line=self.source_line(tok.line))

    def parse_write(self) -> Stmt:
        tok = self.advance()
        # content can be string literal or variable name
        content_expr = self.parse_expr()
        self.expect(TT.TO)
        # detect: to csv/json "path" OR to file "path"
        if self.match(TT.CSV):
            self.advance()
            path = self.parse_expr()
            data_name = content_expr.name if hasattr(content_expr, 'name') else "data"
            return WriteCsvStmt(data=data_name, path=path,
                                line_num=tok.line,
                                source_line=self.source_line(tok.line))
        if self.match(TT.JSON):
            self.advance()
            path = self.parse_expr()
            return WriteJsonStmt(data=content_expr.name if hasattr(content_expr,"name") else "data", path=path,
                                 line_num=tok.line,
                                 source_line=self.source_line(tok.line))
        # default: write to file (FILE keyword is optional)
        if self.match(TT.FILE):
            self.advance()
        path = self.parse_expr()
        return WriteFileStmt(content=content_expr, path=path,
                             line_num=tok.line,
                             source_line=self.source_line(tok.line))

    def parse_append(self) -> Stmt:
        tok     = self.advance()
        content = self.parse_expr()
        self.expect(TT.TO)
        if self.match(TT.FILE):
            self.advance()
        path    = self.parse_expr()
        return AppendFileStmt(content=content, path=path,
                              line_num=tok.line,
                              source_line=self.source_line(tok.line))

    def parse_delete_file(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        return DeleteFileStmt(path=path, line_num=tok.line)

    def parse_read_file(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt  = self.expect_name().value
        return ReadFileStmt(path=path, target=tgt, mode="text",
                            line_num=tok.line)

    def parse_read_lines(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt  = self.expect_name().value
        return ReadFileStmt(path=path, target=tgt, mode="lines",
                            line_num=tok.line)

    def parse_read_csv(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt  = self.expect_name().value
        return ReadFileStmt(path=path, target=tgt, mode="csv",
                            line_num=tok.line)

    def parse_read_json(self) -> Stmt:
        tok  = self.advance()
        path = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt  = self.expect_name().value
        return ReadFileStmt(path=path, target=tgt, mode="json",
                            line_num=tok.line)

    def parse_fetch(self) -> Stmt:
        tok = self.advance()
        url = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return FetchStmt(url=url, target=tgt, as_json=False,
                         line_num=tok.line)

    def parse_fetch_json(self) -> Stmt:
        tok = self.advance()
        url = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return FetchStmt(url=url, target=tgt, as_json=True,
                         line_num=tok.line)

    # ─────────────────────────────────────────
    # REGEX / STRING OPS
    # ─────────────────────────────────────────

    def parse_find_pattern(self) -> Stmt:
        tok     = self.advance()
        pattern = self.parse_expr()
        self.expect(TT.IN)
        source  = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        target  = self.expect_name().value
        return FindPatternStmt(pattern=pattern, source=source,
                               target=target, line_num=tok.line)

    def parse_replace_pattern(self) -> Stmt:
        tok         = self.advance()
        pattern     = self.parse_expr()
        self.expect(TT.WITH)
        replacement = self.parse_expr()
        self.expect(TT.IN)
        source      = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        target      = self.expect_name().value
        return ReplacePatternStmt(pattern=pattern,
                                  replacement=replacement,
                                  source=source, target=target,
                                  line_num=tok.line)

    def parse_replace_str(self) -> Stmt:
        tok = self.advance()
        old = self.parse_expr()
        self.expect(TT.WITH)
        new = self.parse_expr()
        self.expect(TT.IN)
        src = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return ReplaceStrStmt(old=old, new=new, source=src,
                              target=tgt, line_num=tok.line)

    def parse_split(self) -> Stmt:
        tok = self.advance()
        src = self.expect_name().value
        self.expect(TT.BY)
        sep = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return SplitStmt(source=src, sep=sep, target=tgt,
                         line_num=tok.line)

    def parse_join(self) -> Stmt:
        tok = self.advance()
        src = self.expect_name().value
        self.expect(TT.WITH)
        sep = self.parse_expr()
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return JoinStmt(source=src, sep=sep, target=tgt,
                        line_num=tok.line)

    # ─────────────────────────────────────────
    # VALIDATION
    # ─────────────────────────────────────────

    def parse_validate(self) -> Stmt:
        tok = self.advance()  # check that
        # source: variable name or string literal
        src_tok = self.current()
        if src_tok.type in (TT.NAME,) or src_tok.type not in {
            TT.IS, TT.EOF, TT.NEWLINE
        }:
            src_tok_val = self.advance()
            src = src_tok_val.value  # variable name or literal
        else:
            src = ""
        self.expect(TT.IS)
        low = high = None

        if self.match(TT.VALID_EMAIL):
            self.advance()
            kind = "email"
        elif self.match(TT.VALID_PHONE):
            self.advance()
            kind = "phone"
        elif self.match(TT.NOT_EMPTY):
            self.advance()
            kind = "not_empty"
        elif self.match(TT.BETWEEN):
            self.advance()
            low  = self._parse_simple_primary()
            # "and" separates low from high — safe to consume
            if self.match(TT.AND):
                self.advance()
            high = self._parse_simple_primary()
            kind = "range"
        elif self.match(TT.A, TT.AN):
            self.advance()
            self.expect(TT.NUMBER_KW)
            kind = "number"
        elif self.match(TT.NOT):
            self.advance()
            self.expect(TT.EMPTY)
            kind = "not_empty"
        else:
            raise ParseError("Unknown validation type", self.current())

        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return ValidateStmt(kind=kind, source=src, target=tgt,
                            low=low, high=high, line_num=tok.line)

    # ─────────────────────────────────────────
    # JSON / MISC
    # ─────────────────────────────────────────

    def parse_convert_stmt(self) -> Stmt:
        """convert X to json and store in var"""
        tok = self.advance()  # CONVERT
        src = self.expect_name().value
        self.expect(TT.TO)
        self.expect(TT.JSON)
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return ConvertJsonStmt(source=src, target=tgt, line_num=tok.line)

    def parse_parse_json(self) -> Stmt:
        tok = self.advance()
        src = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return ParseJsonStmt(source=src, target=tgt, line_num=tok.line)

    def parse_convert_json(self) -> Stmt:
        tok = self.advance()
        src = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return ConvertJsonStmt(source=src, target=tgt, line_num=tok.line)

    def parse_try(self) -> Stmt:
        tok  = self.advance()
        body = self.parse_try_block()
        self.expect(TT.CATCH)
        cb   = self.parse_block()
        self.expect(TT.DONE)
        return TryStmt(body=body, catch_body=cb, line_num=tok.line)

    def parse_try_block(self) -> List[Stmt]:
        CLOSERS = {TT.CATCH, TT.DONE, TT.EOF}
        body = []
        while not self.match(*CLOSERS):
            try:
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
            except ParseError as e:
                self.errors.append(f"Line {e.token.line}: {e.message}")
                self._skip_to_next_statement()
                if self.match(*CLOSERS):
                    break
        return body

    def parse_raise_error(self) -> Stmt:
        tok = self.advance()
        msg = self.parse_expr()
        return RaiseErrorStmt(message=msg, line_num=tok.line)

    def parse_multiline_str(self) -> Stmt:
        tok    = self.advance()   # STORE_TEXT_BLOCK — value is var name
        target = tok.value
        # next token should be END_BLOCK with content in value
        end_tok = self.expect(TT.END_BLOCK)
        lines   = end_tok.value.split("\n") if end_tok.value else []
        return MultilineStrStmt(target=target, lines=lines,
                                line_num=tok.line)

    def parse_run_background(self) -> Stmt:
        tok  = self.advance()
        name = self.expect_name().value
        args = None
        if self.match(TT.WITH):
            self.advance()
            args = self.parse_expr()
        return RunBackgroundStmt(fn_name=name, args=args,
                                 line_num=tok.line)

    def parse_wait(self) -> Stmt:
        tok = self.advance()
        n   = self.parse_expr()
        if self.match(TT.SECONDS, TT.SECOND):
            self.advance()
        return WaitStmt(seconds=n, line_num=tok.line)

    def parse_flatten(self) -> Stmt:
        tok = self.advance()
        src = self.expect_name().value
        self.expect(TT.AND_STORE_IN)
        tgt = self.expect_name().value
        return FlattenStmt(source=src, target=tgt, line_num=tok.line)

    # ─────────────────────────────────────────
    # CONDITION PARSER
    # ─────────────────────────────────────────

    def parse_condition(self) -> Any:
        """Parse a condition expression (for if/while)."""
        # file exists check
        if self.match(TT.FILE):
            self.advance()
            path = self.parse_primary_condition()
            self.expect(TT.EXISTS)
            return FileExistsCondition(path=path,
                                       line_num=path.line_num)

        left = self.parse_primary_condition()

        # matches pattern check
        if self.match(TT.MATCHES):
            self.advance()
            self.expect(TT.PATTERN)
            pattern = self.parse_primary_condition()
            var_name = ""
            if isinstance(left, Identifier):
                var_name = left.name
            cond = PatternCondition(var_name=var_name, pattern=pattern,
                                    line_num=left.line_num)
        else:
            # comparison operators
            COMP_OPS = {
                TT.GT: ">", TT.LT: "<", TT.EQ: "==",
                TT.NEQ: "!=", TT.GTE: ">=", TT.LTE: "<=",
            }
            if self.current().type in COMP_OPS:
                op    = COMP_OPS[self.advance().type]
                right = self.parse_primary_condition()
                cond  = BinaryOp(left=left, op=op, right=right,
                                 line_num=left.line_num)
            else:
                cond = left

        # logical operators — chain multiple conditions
        while self.match(TT.AND, TT.OR):
            logical_op = self.advance().value
            right_cond = self.parse_condition()
            cond = BinaryOp(left=cond, op=logical_op,
                            right=right_cond, line_num=cond.line_num)

        return cond

    def parse_primary_condition(self) -> Any:
        """Parse one side of a condition without consuming and/or."""
        left = self.parse_unary_condition()
        # parse math expression (no and/or)
        while self.current().type in (
            TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
            TT.PERCENT, TT.CARET
        ):
            op_tok = self.advance()
            op     = self._token_to_op(op_tok.type)
            right  = self.parse_unary_condition()
            left   = BinaryOp(left=left, op=op, right=right,
                              line_num=op_tok.line)
        return left

    def parse_unary_condition(self) -> Any:
        tok = self.current()
        if tok.type == TT.MINUS:
            self.advance()
            return UnaryOp(op="-", operand=self.parse_primary(),
                           line_num=tok.line)
        if tok.type == TT.NOT:
            self.advance()
            # NOT should negate the full comparison (e.g. not x > 10)
            operand = self.parse_primary_condition()
            COMP_OPS = {
                TT.GT: ">", TT.LT: "<", TT.EQ: "==",
                TT.NEQ: "!=", TT.GTE: ">=", TT.LTE: "<=",
            }
            if self.current().type in COMP_OPS:
                op    = COMP_OPS[self.advance().type]
                right = self.parse_primary_condition()
                operand = BinaryOp(left=operand, op=op, right=right,
                                   line_num=tok.line)
            return UnaryOp(op="not", operand=operand, line_num=tok.line)
        return self.parse_primary()

    # ─────────────────────────────────────────
    # EXPRESSION PARSER (Pratt parser)
    # Handles full operator precedence correctly
    # ─────────────────────────────────────────

    def parse_expr(self, min_prec: int = 0) -> Any:
        """
        Pratt parser for expressions.
        Correctly handles: + - * / % ^ with precedence.
        """
        left = self.parse_unary()

        while True:
            tok = self.current()
            prec = self._get_precedence(tok.type)
            if prec < min_prec:
                break

            op_tok = self.advance()
            op     = self._token_to_op(op_tok.type)

            # Right-associative for ^ (power)
            next_prec = prec + (0 if op == "**" else 1)
            right     = self.parse_expr(next_prec)

            left = BinaryOp(left=left, op=op, right=right,
                            line_num=op_tok.line)

        return left

    def _get_precedence(self, token_type: str) -> int:
        """Return operator precedence (higher = tighter binding)."""
        return {
            TT.OR:      1,
            TT.AND:     2,
            TT.PLUS:    3,
            TT.MINUS:   3,
            TT.STAR:    4,
            TT.SLASH:   4,
            TT.PERCENT: 4,
            TT.CARET:   5,   # right-associative
        }.get(token_type, -1)

    def _token_to_op(self, token_type: str) -> str:
        return {
            TT.PLUS:    "+",
            TT.MINUS:   "-",
            TT.STAR:    "*",
            TT.SLASH:   "/",
            TT.PERCENT: "%",
            TT.CARET:   "**",
            TT.AND:     "and",
            TT.OR:      "or",
        }.get(token_type, token_type)

    def parse_unary(self) -> Any:
        """Handle unary minus and not."""
        tok = self.current()
        if tok.type == TT.MINUS:
            self.advance()
            operand = self.parse_primary()
            return UnaryOp(op="-", operand=operand, line_num=tok.line)
        if tok.type == TT.NOT:
            self.advance()
            operand = self.parse_primary()
            return UnaryOp(op="not", operand=operand, line_num=tok.line)
        base = self.parse_primary()
        # postfix: X padded left/right/center to N
        if self.match(TT.PADDED_LEFT, TT.PADDED_RIGHT, TT.PADDED_CENTER):
            dir_map = {
                TT.PADDED_LEFT:   "left",
                TT.PADDED_RIGHT:  "right",
                TT.PADDED_CENTER: "center",
            }
            direction = dir_map[self.current().type]
            self.advance()
            width = int(self.expect(TT.NUMBER).value)
            base = PadExpr(direction=direction, value=base,
                           width=width, line_num=tok.line)
        # postfix type conversion: result as text, count as text, etc.
        if self.match(TT.AS):
            self.advance()
            type_kw = self.current().value
            self.advance()
            return AsTypeExpr(value=base, type_kw=type_kw,
                              line_num=tok.line)
        return base

    def parse_primary(self) -> Any:
        """Parse a primary expression — literal, identifier, or grouped."""
        tok = self.current()

        # Number literal
        if tok.type == TT.NUMBER:
            self.advance()
            val = float(tok.value) if "." in tok.value else int(tok.value)
            return NumberLiteral(value=val, line_num=tok.line)

        # String literal — check for f-string
        if tok.type == TT.STRING:
            self.advance()
            raw = tok.value[1:-1]  # strip quotes
            is_f = bool(re.search(r'\{[a-zA-Z_]\w*\}', raw))
            return StringLiteral(value=tok.value, is_fstring=is_f,
                                 line_num=tok.line)

        # Bool literal
        if tok.type == TT.BOOL:
            self.advance()
            return BoolLiteral(value=(tok.value == "true"),
                               line_num=tok.line)

        # Parenthesised expression
        if tok.type == TT.LPAREN:
            self.advance()
            expr = self.parse_expr()
            self.expect(TT.RPAREN)
            return expr

        # Identifier (variable name)
        if tok.type == TT.NAME:
            self.advance()
            name = tok.value
            # handle dot notation: math.pi, os.path etc
            while self.current().value == "." or (
                self.current().type == TT.UNKNOWN and
                self.current().value == "."
            ):
                self.advance()  # consume dot
                attr = self.advance().value
                name = name + "." + attr
            return Identifier(name=name, line_num=tok.line)

        # Inline type conversion on literals: "42" as number
        # (handled above via parse_expr flow)

        # Math functions used inline: sin of X, sqrt of X etc
        MATH_FN_TOKENS = {
            TT.SIN, TT.COS, TT.TAN, TT.LOG,
            TT.SQRT, TT.FLOOR, TT.CEILING, TT.ABSOLUTE,
            TT.SQUARE, TT.CUBE,
        }
        if tok.type in MATH_FN_TOKENS:
            fn = self.advance().value
            self.expect(TT.OF)
            arg = self.parse_primary()   # recursive — handles nesting
            return MathFnExpr(fn=fn, arg=arg, line_num=tok.line)

        # LENGTH OF X used as expression (e.g. "if length of list > 0")
        if tok.type == TT.LENGTH:
            self.advance()
            self.expect(TT.OF)
            arg = self.parse_primary()
            return StringOpExpr(op="length", arg=arg, line_num=tok.line)

        # NOT handled in parse_unary above

        NON_NAMES = {
            TT.STORE, TT.SHOW, TT.ASK, TT.IF, TT.REPEAT,
            TT.FOR_EACH, TT.WHILE, TT.DEFINE, TT.DONE, TT.END,
            TT.RETURN, TT.CALL, TT.ADD, TT.REMOVE,
            TT.MAKE_LIST, TT.MAKE_DICT, TT.SORT, TT.REVERSE,
            TT.GLOBAL, TT.INCLUDE, TT.USE, TT.TRY, TT.CATCH,
            TT.INCREASE, TT.DECREASE, TT.WRITE, TT.APPEND,
            TT.DELETE_FILE, TT.READ_FILE, TT.READ_LINES,
            TT.READ_CSV, TT.READ_JSON, TT.FETCH, TT.FETCH_JSON,
            TT.FIND_PATTERN, TT.REPLACE_PATTERN, TT.REPLACE,
            TT.SPLIT, TT.JOIN, TT.CHECK_THAT, TT.RAISE_ERROR,
            TT.RUN_BACKGROUND, TT.WAIT_FOR_ALL, TT.WAIT,
            TT.STOP_PROGRAM, TT.EXIT_PROGRAM, TT.CLEAR_SCREEN,
            TT.STORE_TEXT_BLOCK, TT.END_BLOCK, TT.COUNT_FROM,
            TT.SHOW_ERROR, TT.SHOW_BLANK, TT.SHOW_PROGRESS,
            TT.RETURN_NOTHING, TT.ASK_AI, TT.ASK_NUMBER,
            TT.OTHERWISE_IF, TT.OTHERWISE,
            TT.NUMBER, TT.STRING, TT.BOOL,
            TT.EOF, TT.NEWLINE, TT.COMMENT, TT.UNKNOWN,
            TT.LPAREN, TT.RPAREN, TT.COMMA,
            TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH,
            TT.PERCENT, TT.CARET, TT.EQ, TT.NEQ,
            TT.GT, TT.LT, TT.GTE, TT.LTE,
        }
        if tok.type not in NON_NAMES:
            self.advance()
            return Identifier(name=tok.value, line_num=tok.line)

        raise ParseError(
            f"Expected a value (number, text, or variable name) "
            f"but got '{tok.value}'",
            tok
        )


# ─────────────────────────────────────────────
# CONVENIENCE FUNCTION
# ─────────────────────────────────────────────

def parse(source: str, filename: str = "<program>") -> Tuple[Program, List[str]]:
    """Parse Saral source and return (AST, errors)."""
    tokens       = tokenize(source, filename)
    source_lines = source.splitlines()
    p            = Parser(tokens, source_lines, filename)
    ast          = p.parse()
    return ast, p.errors


# ─────────────────────────────────────────────
# TEST
# ─────────────────────────────────────────────

if __name__ == "__main__":
    test_src = """
# Full parser test
store 10 in price
store price * 2 in double_price
show "Price: {price}" in green

if price > 5 and price < 100
    show "in range"
otherwise if price >= 100
    show "too high"
otherwise
    show "too low"
done

repeat 3 times
    show price
done

for each item in my_list
    show item
done

count from 1 to 10 as n
    show n
done

define greet using name, title = "Mr"
    show "Hello " + title + " " + name
end

store result of greet with "Arun" in msg
show msg

make list called fruits
add "apple" to fruits
sort fruits
store item 1 of fruits in first
store items 1 to 2 of fruits in some

store sqrt of 144 in sq
store round of 3.14159 to 2 places in pi
store sum of fruits in total

try
    store 10 / 0 in bad
catch
    show error
done
"""
    ast, errors = parse(test_src)

    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  {e}")
    else:
        print(f"✅  Parse successful — {len(ast.body)} top-level statements")
        print_ast(ast)
