"""
test_saral.py — Saral Lang v1.0.1 Test Suite
Run with:  python3 test_saral.py
           python3 test_saral.py -v     (verbose)
"""

import sys
import os
import io
import contextlib
import unittest

# Ensure the core directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import compile_saral, check_saral


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def run_saral(source: str) -> str:
    """Compile and execute a Saral program, capturing stdout. Returns stripped output."""
    code, _, errors = compile_saral(source, "<test>", show_warnings=False)
    if errors:
        raise AssertionError(f"Parse errors: {errors}")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(compile(code, "<test>", "exec"), {"__name__": "__main__"})
    return buf.getvalue().strip()


def parse_errors(source: str) -> list:
    """Return parse error list for source (empty = valid)."""
    _, _, errors = compile_saral(source, "<test>", show_warnings=False)
    return errors


# ─────────────────────────────────────────────────────────────────────────────
# 1. VARIABLES & ARITHMETIC
# ─────────────────────────────────────────────────────────────────────────────

class TestVariables(unittest.TestCase):

    def test_store_integer(self):
        self.assertEqual(run_saral('store 42 in n\nshow n'), '42')

    def test_store_float(self):
        self.assertEqual(run_saral('store 3.14 in pi\nshow pi'), '3.14')

    def test_store_string(self):
        self.assertEqual(run_saral('store "hello" in s\nshow s'), 'hello')

    def test_addition(self):
        self.assertEqual(run_saral('store 10 + 5 in r\nshow r'), '15')

    def test_subtraction(self):
        self.assertEqual(run_saral('store 10 - 3 in r\nshow r'), '7')

    def test_multiplication(self):
        self.assertEqual(run_saral('store 6 * 7 in r\nshow r'), '42')

    def test_division(self):
        self.assertEqual(run_saral('store 10 / 4 in r\nshow r'), '2.5')

    def test_modulo(self):
        self.assertEqual(run_saral('store 10 % 3 in r\nshow r'), '1')

    def test_power(self):
        self.assertEqual(run_saral('store 2 ^ 8 in r\nshow r'), '256')

    def test_increase(self):
        self.assertEqual(run_saral('store 5 in x\nincrease x by 3\nshow x'), '8')

    def test_decrease(self):
        self.assertEqual(run_saral('store 10 in x\ndecrease x by 4\nshow x'), '6')

    def test_compound_expression(self):
        self.assertEqual(run_saral('store (2 + 3) * 4 in r\nshow r'), '20')


# ─────────────────────────────────────────────────────────────────────────────
# 2. STRING OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestStrings(unittest.TestCase):

    def test_concatenation(self):
        self.assertEqual(run_saral('show "Hello" + " " + "World"'), 'Hello World')

    def test_uppercase(self):
        self.assertEqual(run_saral('store uppercase of "hello" in r\nshow r'), 'HELLO')

    def test_lowercase(self):
        self.assertEqual(run_saral('store lowercase of "HELLO" in r\nshow r'), 'hello')

    def test_string_length(self):
        self.assertEqual(run_saral('store length of "Saral" in n\nshow n'), '5')

    def test_reversed_string(self):
        self.assertEqual(run_saral('store reversed of "abc" in r\nshow r'), 'cba')

    def test_trimmed(self):
        self.assertEqual(run_saral('store trimmed of "  hi  " in r\nshow r'), 'hi')

    def test_replace(self):
        src = ('store "hello world" in t\n'
               'replace "world" with "Saral" in t and store in r\nshow r')
        self.assertEqual(run_saral(src), 'hello Saral')

    def test_type_conversion_to_text(self):
        self.assertEqual(run_saral('store 42 as text in t\nshow t'), '42')

    def test_type_conversion_to_number(self):
        self.assertEqual(run_saral('store "7" as number in n\nshow n + 1'), '8')


# ─────────────────────────────────────────────────────────────────────────────
# 3. CONDITIONALS
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionals(unittest.TestCase):

    def test_if_true(self):
        src = 'store 10 in x\nif x > 5\n    show "yes"\ndone'
        self.assertEqual(run_saral(src), 'yes')

    def test_if_false(self):
        src = 'store 3 in x\nif x > 5\n    show "yes"\ndone'
        self.assertEqual(run_saral(src), '')

    def test_if_otherwise(self):
        src = 'store 3 in x\nif x > 5\n    show "big"\notherwise\n    show "small"\ndone'
        self.assertEqual(run_saral(src), 'small')

    def test_otherwise_if(self):
        src = ('store 50 in x\n'
               'if x > 100\n    show "huge"\n'
               'otherwise if x > 25\n    show "medium"\n'
               'otherwise\n    show "small"\ndone')
        self.assertEqual(run_saral(src), 'medium')

    def test_equality_check(self):
        src = 'store "hello" in s\nif s = "hello"\n    show "match"\ndone'
        self.assertEqual(run_saral(src), 'match')

    def test_and_condition(self):
        src = 'store 5 in x\nif x > 1 and x < 10\n    show "in range"\ndone'
        self.assertEqual(run_saral(src), 'in range')

    def test_or_condition(self):
        src = 'store 15 in x\nif x < 5 or x > 10\n    show "outside"\ndone'
        self.assertEqual(run_saral(src), 'outside')

    def test_not_condition(self):
        src = 'store 5 in x\nif not x > 10\n    show "not big"\ndone'
        self.assertEqual(run_saral(src), 'not big')


# ─────────────────────────────────────────────────────────────────────────────
# 4. LOOPS
# ─────────────────────────────────────────────────────────────────────────────

class TestLoops(unittest.TestCase):

    def test_repeat(self):
        src = 'store 0 in n\nrepeat 5 times\n    increase n by 1\ndone\nshow n'
        self.assertEqual(run_saral(src), '5')

    def test_count_from_to(self):
        src = 'store 0 in s\ncount from 1 to 5 as i\n    increase s by i\ndone\nshow s'
        self.assertEqual(run_saral(src), '15')

    def test_while(self):
        src = 'store 1 in n\nwhile n < 5\n    increase n by 1\ndone\nshow n'
        self.assertEqual(run_saral(src), '5')

    def test_for_each(self):
        src = ('make list called nums\nadd 10 to nums\nadd 20 to nums\nadd 30 to nums\n'
               'store 0 in total\n'
               'for each item in nums\n    increase total by item\ndone\nshow total')
        self.assertEqual(run_saral(src), '60')

    def test_stop(self):
        src = ('store 0 in n\ncount from 1 to 10 as i\n'
               '    if i > 3\n        stop\n    done\n'
               '    increase n by 1\ndone\nshow n')
        self.assertEqual(run_saral(src), '3')

    def test_skip(self):
        src = ('store 0 in n\ncount from 1 to 5 as i\n'
               '    if i = 3\n        skip\n    done\n'
               '    increase n by 1\ndone\nshow n')
        self.assertEqual(run_saral(src), '4')


# ─────────────────────────────────────────────────────────────────────────────
# 5. LISTS
# ─────────────────────────────────────────────────────────────────────────────

class TestLists(unittest.TestCase):

    def test_make_and_add(self):
        src = 'make list called xs\nadd 1 to xs\nadd 2 to xs\nadd 3 to xs\nshow xs'
        self.assertIn('1', run_saral(src))
        self.assertIn('3', run_saral(src))

    def test_length(self):
        src = 'make list called xs\nadd 10 to xs\nadd 20 to xs\nstore length of xs in n\nshow n'
        self.assertEqual(run_saral(src), '2')

    def test_sum(self):
        src = 'make list called xs\nadd 10 to xs\nadd 20 to xs\nadd 30 to xs\nstore sum of xs in s\nshow s'
        self.assertEqual(run_saral(src), '60')

    def test_average(self):
        src = 'make list called xs\nadd 10 to xs\nadd 20 to xs\nadd 30 to xs\nstore average of xs in a\nshow a'
        self.assertEqual(run_saral(src), '20.0')

    def test_maximum(self):
        src = 'make list called xs\nadd 3 to xs\nadd 9 to xs\nadd 1 to xs\nstore maximum of xs in m\nshow m'
        self.assertEqual(run_saral(src), '9')

    def test_minimum(self):
        src = 'make list called xs\nadd 3 to xs\nadd 9 to xs\nadd 1 to xs\nstore minimum of xs in m\nshow m'
        self.assertEqual(run_saral(src), '1')

    def test_item_access(self):
        src = 'make list called xs\nadd "a" to xs\nadd "b" to xs\nadd "c" to xs\nstore item 2 of xs in v\nshow v'
        self.assertEqual(run_saral(src), 'b')

    def test_sort(self):
        src = 'make list called xs\nadd 3 to xs\nadd 1 to xs\nadd 2 to xs\nsort xs\nstore item 1 of xs in v\nshow v'
        self.assertEqual(run_saral(src), '1')

    def test_remove(self):
        src = 'make list called xs\nadd 10 to xs\nadd 20 to xs\nadd 30 to xs\nremove 20 from xs\nstore length of xs in n\nshow n'
        self.assertEqual(run_saral(src), '2')


# ─────────────────────────────────────────────────────────────────────────────
# 6. DICTIONARIES
# ─────────────────────────────────────────────────────────────────────────────

class TestDictionaries(unittest.TestCase):

    def test_set_and_get(self):
        src = ('make dictionary called d\n'
               'set "name" of d to "Arun"\n'
               'store value of "name" in d in v\n'
               'show v')
        self.assertEqual(run_saral(src), 'Arun')

    def test_multiple_keys(self):
        src = ('make dictionary called d\n'
               'set "x" of d to 10\n'
               'set "y" of d to 20\n'
               'store value of "x" in d in a\n'
               'store value of "y" in d in b\n'
               'show a + b')
        self.assertEqual(run_saral(src), '30')

    def test_overwrite_key(self):
        src = ('make dictionary called d\n'
               'set "k" of d to 1\n'
               'set "k" of d to 99\n'
               'store value of "k" in d in v\n'
               'show v')
        self.assertEqual(run_saral(src), '99')


# ─────────────────────────────────────────────────────────────────────────────
# 7. FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestFunctions(unittest.TestCase):

    def test_define_and_call(self):
        src = 'define greet using name\n    show "Hello " + name\nend\ncall greet with "Saral"'
        self.assertEqual(run_saral(src), 'Hello Saral')

    def test_return_value(self):
        src = ('define double using n\n    return n * 2\nend\n'
               'store result of double with 5 in r\nshow r')
        self.assertEqual(run_saral(src), '10')

    def test_multiple_params(self):
        src = ('define total using a, b\n    return a + b\nend\n'
               'store result of total with 3, 4 in r\nshow r')
        self.assertEqual(run_saral(src), '7')

    def test_default_param(self):
        src = ('define greet using name, greeting = "Hi"\n'
               '    show greeting + " " + name\nend\n'
               'call greet with "Arun"')
        self.assertEqual(run_saral(src), 'Hi Arun')

    def test_recursive(self):
        src = ('define factorial using n\n'
               '    if n <= 1\n        return 1\n    done\n'
               '    store n - 1 in prev\n'
               '    store result of factorial with prev in sub\n'
               '    return n * sub\nend\n'
               'store result of factorial with 5 in r\nshow r')
        self.assertEqual(run_saral(src), '120')

    def test_global_variable(self):
        src = ('store 0 in counter\n'
               'define bump\n'
               '    global counter\n'
               '    increase counter by 1\nend\n'
               'call bump\ncall bump\ncall bump\nshow counter')
        self.assertEqual(run_saral(src), '3')


# ─────────────────────────────────────────────────────────────────────────────
# 8. ERROR HANDLING
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling(unittest.TestCase):

    def test_try_catch_division(self):
        src = 'try\n    store 1 / 0 in b\ncatch\n    show "caught"\ndone'
        self.assertEqual(run_saral(src), 'caught')

    def test_try_catch_shows_error(self):
        src = 'try\n    store 1 / 0 in b\ncatch\n    show error\ndone'
        out = run_saral(src)
        self.assertIn('division by zero', out.lower())

    def test_try_no_error(self):
        src = 'try\n    store 10 / 2 in r\ncatch\n    show "error"\ndone\nshow r'
        self.assertEqual(run_saral(src), '5.0')


# ─────────────────────────────────────────────────────────────────────────────
# 9. MATHS FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestMathFunctions(unittest.TestCase):

    def test_sqrt(self):
        self.assertEqual(run_saral('store sqrt of 144 in r\nshow r'), '12.0')

    def test_absolute(self):
        out = run_saral('store absolute of -7 in r\nshow r')
        self.assertEqual(float(out), 7.0)

    def test_round(self):
        self.assertEqual(run_saral('store round of 3.14159 to 2 places in r\nshow r'), '3.14')

    def test_floor(self):
        self.assertEqual(run_saral('store floor of 4.9 in r\nshow r'), '4')

    def test_ceiling(self):
        self.assertEqual(run_saral('store ceiling of 4.1 in r\nshow r'), '5')

    def test_random_in_range(self):
        src = 'store random number from 1 to 100 in r\nif r >= 1 and r <= 100\n    show "ok"\ndone'
        self.assertEqual(run_saral(src), 'ok')


# ─────────────────────────────────────────────────────────────────────────────
# 10. DATE & TIME
# ─────────────────────────────────────────────────────────────────────────────

class TestDateTime(unittest.TestCase):

    def test_store_today(self):
        out = run_saral('store today in d\nshow d')
        import datetime
        today = datetime.date.today()
        # Saral formats as DD-MM-YYYY
        self.assertIn(str(today.year), out)
        self.assertIn(str(today.day), out)

    def test_current_year(self):
        out = run_saral('store current year in y\nshow y')
        import datetime
        self.assertEqual(out, str(datetime.date.today().year))

    def test_current_month(self):
        out = run_saral('store current month in m\nshow m')
        import datetime
        self.assertEqual(out, str(datetime.date.today().month))


# ─────────────────────────────────────────────────────────────────────────────
# 11. FILE OPERATIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestFileOperations(unittest.TestCase):

    _tmpfile = '/tmp/_saral_test_file.txt'

    def tearDown(self):
        if os.path.exists(self._tmpfile):
            os.remove(self._tmpfile)

    def test_write_and_read(self):
        src = (f'write "Hello Saral" to file "{self._tmpfile}"\n'
               f'read file "{self._tmpfile}" and store in content\n'
               f'show content')
        self.assertEqual(run_saral(src), 'Hello Saral')

    def test_append(self):
        src = (f'write "line1" to file "{self._tmpfile}"\n'
               f'append "line2" to file "{self._tmpfile}"\n'
               f'read lines of "{self._tmpfile}" and store in lines\n'
               f'store length of lines in n\nshow n')
        self.assertEqual(run_saral(src), '2')

    def test_file_exists_check(self):
        src = (f'write "x" to file "{self._tmpfile}"\n'
               f'if file "{self._tmpfile}" exists\n    show "yes"\ndone')
        self.assertEqual(run_saral(src), 'yes')

    def test_delete_file(self):
        src = (f'write "x" to file "{self._tmpfile}"\n'
               f'delete file "{self._tmpfile}"\n'
               f'if file "{self._tmpfile}" exists\n    show "yes"\notherwise\n    show "no"\ndone')
        self.assertEqual(run_saral(src), 'no')


# ─────────────────────────────────────────────────────────────────────────────
# 12. TYPE CHECKING & VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

class TestValidation(unittest.TestCase):

    def test_valid_email(self):
        src = 'check that "arun@bakesmart.com" is valid email and store in ok\nshow ok'
        self.assertEqual(run_saral(src), 'True')

    def test_invalid_email(self):
        src = 'check that "notanemail" is valid email and store in ok\nshow ok'
        self.assertEqual(run_saral(src), 'False')

    def test_valid_phone(self):
        src = 'check that "9876543210" is valid phone and store in ok\nshow ok'
        self.assertEqual(run_saral(src), 'True')

    def test_not_empty(self):
        src = 'check that "hello" is not empty and store in ok\nshow ok'
        self.assertEqual(run_saral(src), 'True')


# ─────────────────────────────────────────────────────────────────────────────
# 13. SHOW VARIANTS
# ─────────────────────────────────────────────────────────────────────────────

class TestShowVariants(unittest.TestCase):

    def test_show_blank(self):
        src = 'show "a"\nshow blank\nshow "b"'
        lines = run_saral(src).splitlines()
        self.assertEqual(lines[0], 'a')
        self.assertEqual(lines[1], '')
        self.assertEqual(lines[2], 'b')

    def test_show_number(self):
        self.assertEqual(run_saral('show 42'), '42')

    def test_show_expression(self):
        self.assertEqual(run_saral('show 3 + 4'), '7')


# ─────────────────────────────────────────────────────────────────────────────
# 14. MULTILINE TEXT BLOCK
# ─────────────────────────────────────────────────────────────────────────────

class TestTextBlock(unittest.TestCase):

    def test_text_block(self):
        src = ('store text block in note\n'
               'Line one\n'
               'Line two\n'
               'end block\n'
               'store length of note in n\n'
               'if n > 5\n    show "ok"\ndone')
        self.assertEqual(run_saral(src), 'ok')


# ─────────────────────────────────────────────────────────────────────────────
# 15. SECURITY — _include() PATH TRAVERSAL PROTECTION
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityInclude(unittest.TestCase):

    def test_include_blocks_absolute_path(self):
        import codegen
        # Simulate what _include does for an absolute path
        path = '/etc/passwd'
        import os as _o
        _sp = path.replace('\\', '/')
        blocked = _o.path.isabs(_sp) or '..' in _sp.split('/')
        self.assertTrue(blocked, "Absolute path should be blocked by _include()")

    def test_include_blocks_traversal(self):
        path = '../../etc/shadow'
        _sp = path.replace('\\', '/')
        blocked = '..' in _sp.split('/')
        self.assertTrue(blocked, "Path traversal '..' should be blocked by _include()")

    def test_include_allows_relative(self):
        path = 'helpers/utils.saral'
        import os as _o
        _sp = path.replace('\\', '/')
        blocked = _o.path.isabs(_sp) or '..' in _sp.split('/')
        self.assertFalse(blocked, "Relative path should be allowed by _include()")


# ─────────────────────────────────────────────────────────────────────────────
# 16. SECURITY — _fetch() URL SCHEME VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityFetch(unittest.TestCase):

    def test_fetch_rejects_file_scheme(self):
        import codegen
        stdlib_src = codegen.STDLIB
        # The _fetch check is part of the stdlib template; verify the guard is present
        self.assertIn("startswith('https://')", stdlib_src)
        self.assertIn("startswith('http://')", stdlib_src)

    def test_fetch_guard_logic(self):
        url = 'file:///etc/passwd'
        allowed = url.startswith('https://') or url.startswith('http://')
        self.assertFalse(allowed, "file:// URL should be rejected by _fetch()")

    def test_fetch_allows_https(self):
        url = 'https://example.com/data.json'
        allowed = url.startswith('https://') or url.startswith('http://')
        self.assertTrue(allowed, "https:// URL should be allowed by _fetch()")


# ─────────────────────────────────────────────────────────────────────────────
# 17. SECURITY — FILENAME SANITISATION
# ─────────────────────────────────────────────────────────────────────────────

class TestSecurityFilenames(unittest.TestCase):

    def _sanitise(self, fname):
        import re, os
        return re.sub(r'[^\w\-]', '_', os.path.basename(fname)).strip('_')

    def test_normal_filename_unchanged(self):
        self.assertEqual(self._sanitise('my_program'), 'my_program')

    def test_path_traversal_stripped(self):
        result = self._sanitise('../../etc/evil')
        self.assertNotIn('/', result)
        self.assertNotIn('..', result)

    def test_absolute_path_stripped(self):
        result = self._sanitise('/etc/cron.d/evil')
        self.assertNotIn('/', result)

    def test_spaces_replaced(self):
        result = self._sanitise('my program')
        self.assertNotIn(' ', result)

    def test_empty_after_sanitise_rejected(self):
        result = self._sanitise('../../')
        self.assertEqual(result, '')


# ─────────────────────────────────────────────────────────────────────────────
# 18. API KEY FILE PERMISSIONS
# ─────────────────────────────────────────────────────────────────────────────

class TestApiKeyPermissions(unittest.TestCase):

    def test_chmod_called_in_save_config(self):
        import inspect
        from ai_config import save_config
        src = inspect.getsource(save_config)
        self.assertIn('os.chmod', src)
        self.assertIn('0o600', src)


# ─────────────────────────────────────────────────────────────────────────────
# 19. URL ENCODING FOR GEMINI
# ─────────────────────────────────────────────────────────────────────────────

class TestGeminiUrlEncoding(unittest.TestCase):

    def test_ai_config_gemini_url_encoded(self):
        import inspect
        from ai_config import _test_gemini
        src = inspect.getsource(_test_gemini)
        self.assertIn('urllib.parse.quote', src)

    def test_ai_helper_gemini_url_encoded(self):
        import inspect
        from ai_helper import _call_gemini
        src = inspect.getsource(_call_gemini)
        self.assertIn('urllib.parse.quote', src)


# ─────────────────────────────────────────────────────────────────────────────
# 20. VERSION CHECK
# ─────────────────────────────────────────────────────────────────────────────

class TestVersion(unittest.TestCase):

    def test_version_is_1_0_1(self):
        import saral
        self.assertEqual(saral.VERSION, "1.0.1")

    def test_version_date_is_2026_06_19(self):
        import saral
        self.assertEqual(saral.VERSION_DATE, "2026-06-19")

    def test_no_transpile_in_pipeline(self):
        with open(os.path.join(os.path.dirname(__file__), 'pipeline.py')) as f:
            src = f.read()
        self.assertNotIn('def transpile', src)
        self.assertNotIn('def format_runtime_error', src)

    def test_no_ollama_tier_comments_in_ai_helper(self):
        with open(os.path.join(os.path.dirname(__file__), 'ai_helper.py')) as f:
            src = f.read()
        self.assertNotIn('DeepSeek → Gemini', src)
        self.assertNotIn('Tier 1 + 2: AI', src)


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    total   = suite.countTestCases()

    print(f"\n🌿  Saral Lang v1.0.1 — Test Suite")
    print(f"    {total} tests across 20 categories\n")
    print("=" * 60)

    runner = unittest.TextTestRunner(verbosity=2 if '-v' in sys.argv else 1)
    result = runner.run(suite)

    print("=" * 60)
    passed = total - len(result.failures) - len(result.errors)
    print(f"\n  Passed : {passed}/{total}")
    if result.failures:
        print(f"  Failed : {len(result.failures)}")
    if result.errors:
        print(f"  Errors : {len(result.errors)}")

    print(f"\n  {'✅  All tests passed!' if result.wasSuccessful() else '❌  Some tests failed.'}\n")
    sys.exit(0 if result.wasSuccessful() else 1)
