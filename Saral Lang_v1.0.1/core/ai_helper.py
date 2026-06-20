"""
ai_helper.py — Saral AI Layer v4.0
═══════════════════════════════════════════════════════════════════
WHAT THIS FILE DOES
  Implements the 5 AI features of Saral Lang:
    1. generate_code  — AI writes Saral code from a description
    2. fix_error      — AI explains and fixes broken Saral code
    3. explain_code   — AI explains what a Saral program does
    4. autocomplete   — suggests next lines while coding
    5. query          — answers questions from inside Saral programs

SETUP
  Run once to configure your AI provider:
    python saral.py --setup-ai

  Paste any API key — Saral Lang auto-detects the provider.

SUPPORTED AI PROVIDERS
  • xAI Grok         — xai-... key     (console.x.ai)
  • OpenAI GPT-4o    — sk-proj-... key (platform.openai.com)
  • DeepSeek R1      — sk-... key      (platform.deepseek.com — free)
  • Anthropic Claude — sk-ant-... key  (console.anthropic.com)
  • Google Gemini    — AIza... key     (aistudio.google.com — free)
  • Groq             — gsk_... key     (console.groq.com — free)
  • Mistral          — alphanumeric    (console.mistral.ai)
  • Cohere           — alphanumeric    (dashboard.cohere.com)

FALLBACK CHAIN (in order):
  Tier 1 — Configured AI provider  (set up via --setup-ai)
  Tier 2 — Pattern matching         (always works, no key needed)
═══════════════════════════════════════════════════════════════════
"""

# ── Standard library only — no pip installs needed ─────────────
import json
import os
import re
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional

# ── ai_config.py handles provider detection, key storage, testing
from ai_config import get_active_ai, PROVIDERS

# ══════════════════════════════════════════════════════════════════
# TOKEN / TIMEOUT LIMITS — memory safety
# ══════════════════════════════════════════════════════════════════

# Cap output tokens — Saral code is short; 512 is plenty.
# Prevents runaway API costs and large memory allocations.
MAX_OUTPUT_TOKENS = 512

# Timeout per provider type (seconds)
# Reasoning models (DeepSeek R1) think before answering — give more time
_TIMEOUT_BY_PROVIDER = {
    "deepseek":  45,   # R1 does chain-of-thought — can take 20-40s
    "openai":    30,
    "anthropic": 30,
    "gemini":    25,
    "groq":      15,   # Groq is very fast (hardware accelerated)
    "xai":       20,   # xAI Grok — fast inference
    "mistral":   20,
    "cohere":    20,
}
_TIMEOUT_DEFAULT = 30

# ══════════════════════════════════════════════════════════════════
# SARAL LANGUAGE REFERENCE
# Injected into every AI prompt — teaches the model Saral syntax.
# Kept minimal (< 1000 tokens) to save API cost and memory.
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# FORBIDDEN CONSTRUCTS — injected into every code-generation prompt
# Lists the Python / non-Saral things the AI must never write.
# ══════════════════════════════════════════════════════════════════

_SARAL_FORBIDDEN = """
FORBIDDEN — these are Python, NOT Saral. Never use them:
  print(...)              → use:   show value
  input("prompt")         → use:   ask "prompt" and store in var
  len(list)               → use:   store length of list in var
  for i in range(n):      → use:   count from 1 to n as i
  for item in list:       → use:   for each item in list
  if condition:           → use:   if condition         (no colon)
  elif condition:         → use:   otherwise if condition
  else:                   → use:   otherwise
  while condition:        → use:   while condition      (no colon)
  def func(param):        → use:   define func using param
  import module           → use:   use module
  var = value             → use:   store value in var
  var += n                → use:   increase var by n
  var -= n                → use:   decrease var by n
  list.append(val)        → use:   add val to list
  list[i]                 → use:   store item i of list in var
  True / False            → use:   true / false  (lower-case is fine too)
  None                    → use:   0  or  ""  (no None in Saral)
  class / object / self   → NOT available in Saral
  try: / except:          → use:   try / catch / done   (no colons)
  f"string {var}"         → use:   "string " + var  or  show var
"""


SARAL_REFERENCE = """
SARAL LANG — COMPLETE SYNTAX REFERENCE

VARIABLES:
  store 10 in price
  store "hello" in name
  increase price by 5
  decrease price by 2

MATH: + - * / ^ %  |  sqrt, round, floor, ceiling, absolute, random number from A to B
      store sqrt of 144 in result
      store random number from 1 to 100 in lucky
      store sum/average/maximum/minimum of my_list in result

OUTPUT / INPUT:
  show price          show "Hello world"          show blank
  ask "Your name: " and store in username
  ask number "Enter age: " and store in age

CONDITIONS:
  if price > 100
      show "expensive"
  otherwise if price > 50
      show "medium"
  otherwise
      show "cheap"
  done

LOOPS:
  repeat 5 times          for each item in my_list        count from 1 to 10 as n
      show "hello"            show item                       show n
  done                    done                            done

  while count < 10        stop   (break)    skip   (continue)
      increase count by 1
  done

LISTS:
  make list called fruits
  add "apple" to fruits          remove "apple" from fruits
  store length of fruits in n    store item 1 of fruits in first
  sort fruits                    sort fruits in reverse           reverse fruits

DICTIONARIES:
  make dictionary called person
  set "name" of person to "Asha"
  store value of "name" in person in result

STRINGS:
  store uppercase/lowercase/trimmed/reversed/length of name in result
  replace "old" with "new" in text and store in result
  split text by "," and store in parts
  join parts with ", " and store in result

TYPE CONVERSION:
  store "42" as number in n      store 42 as text in t      store 3.14 as decimal in d

FILES:
  read file "data.txt" and store in content
  read lines of "data.txt" and store in lines
  write content to file "output.txt"        append content to file "output.txt"
  delete file "old.txt"                     if file "data.txt" exists

DATE & TIME:
  store today/now/current time/current year/current month/current day in var

FUNCTIONS:
  define greet using name        call greet with "Asha"
      show "Hello " + name       store result of greet with "Asha" in msg
  end                            return value      return nothing

ERROR HANDLING:
  try
      store 10 / 0 in bad
  catch
      show "something went wrong"
      show error
  done

AI COMMANDS (inside Saral programs):
  ask ai "summarize this" using data and store in result
  ask ai "translate to Malayalam" and store in result

LIBRARIES:  use math     use pandas
UTILITY:    wait 2 seconds    clear screen    exit program

RULES:
- Case insensitive: STORE = store = Store
- Use # for comments
- Indentation is optional but recommended
- Single = for equality check inside if statements
"""

# ══════════════════════════════════════════════════════════════════
# PRIVATE HELPERS — HTTP callers
# ══════════════════════════════════════════════════════════════════

def _cap_text(text: str, max_chars: int = 3000) -> str:
    """
    Memory guard: truncate very long inputs before sending to API.
    3000 chars ~= 750 tokens — safe, cheap, and fast.
    We use character count (not token count) because token counting
    needs a library. Character estimate is conservative and uses
    zero memory overhead.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[...truncated for memory safety...]"


def _call_openai_compat(api_key: str, api_url: str, model: str,
                         prompt: str, timeout: int) -> str:
    """
    Call any OpenAI-compatible endpoint.
    Used for: OpenAI, DeepSeek, Groq, Mistral — they all share
    the same /v1/chat/completions request/response shape.
    """
    payload = json.dumps({
        "model":       model,
        "messages":    [{"role": "user", "content": prompt}],
        "max_tokens":  MAX_OUTPUT_TOKENS,
        "temperature": 0.3,
        "top_p":       0.9,
        "stream":      False,
    }).encode("utf-8")

    req = urllib.request.Request(
        api_url,
        data    = payload,
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent":    "SaralLang/1.0",
        },
        method  = "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data    = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Empty choices in response.")
        content = choices[0].get("message", {}).get("content", "").strip()
        if not content:
            raise RuntimeError("Empty content in response.")
        return content


def _call_anthropic(api_key: str, model: str, prompt: str, timeout: int) -> str:
    """
    Call Anthropic Claude API.
    Different from OpenAI: uses x-api-key header and /v1/messages shape.
    """
    payload = json.dumps({
        "model":      model,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "messages":   [{"role": "user", "content": prompt}],
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data    = payload,
        headers = {
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01",
        },
        method  = "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data    = json.loads(resp.read().decode("utf-8"))
        content = data.get("content", [])
        if not content:
            raise RuntimeError("Empty content in response.")
        return content[0].get("text", "").strip()


def _call_gemini(api_key: str, model: str, prompt: str, timeout: int) -> str:
    """
    Call Google Gemini API.
    Different from OpenAI: key goes in the URL, not in the header.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{urllib.parse.quote(model, safe='')}:generateContent"
        f"?key={urllib.parse.quote(api_key, safe='')}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":     0.3,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
        },
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data    = payload,
        headers = {"Content-Type": "application/json"},
        method  = "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data       = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError("Empty candidates in response.")
        return (
            candidates[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )


def _call_cohere(api_key: str, model: str, prompt: str, timeout: int) -> str:
    """Call Cohere API — uses its own /generate shape."""
    payload = json.dumps({
        "model":      model,
        "prompt":     prompt,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "temperature": 0.3,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.cohere.ai/v1/generate",
        data    = payload,
        headers = {
            "Content-Type":  "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method  = "POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        gens = data.get("generations", [])
        if not gens:
            raise RuntimeError("Empty generations in response.")
        return gens[0].get("text", "").strip()


# ══════════════════════════════════════════════════════════════════
# UNIVERSAL AI DISPATCHER
# ══════════════════════════════════════════════════════════════════

def _call_ai(prompt: str, silent: bool = False) -> str:
    """
    Send a prompt to whatever AI the user has configured.

    REASONING PROCESS:
      Step 1 — Ask ai_config.py: who is configured?
               It checks saral_ai.conf first, then env vars.
      Step 2 — Look up the timeout for this provider type.
      Step 3 — Route to the correct HTTP caller based on provider.
      Step 4 — If the call fails, raise RuntimeError so the caller
               can fall back to pattern matching with a helpful message.

    WHY ONE DISPATCHER INSTEAD OF TWO HARDCODED TIERS:
      The old approach (try DeepSeek, then try Gemini) meant Asha
      decided for the user. Now the user decides once via --setup-ai,
      and _call_ai just follows that decision.
      Adding a new provider in the future = add one entry in ai_config.py.
      No changes needed in this file.
    """
    config = get_active_ai()   # reads saral_ai.conf or env vars

    if config is None:
        raise RuntimeError(
            "No AI configured. Run: python saral.py --setup-ai"
        )

    provider_id = config["provider"]
    api_key     = config["key"]
    model       = config["model"]
    api_url     = config.get("api_url", "")
    timeout     = _TIMEOUT_BY_PROVIDER.get(provider_id, _TIMEOUT_DEFAULT)

    try:
        if provider_id in ("openai", "deepseek", "groq", "mistral", "xai"):
            result = _call_openai_compat(api_key, api_url, model, prompt, timeout)
        elif provider_id == "anthropic":
            result = _call_anthropic(api_key, model, prompt, timeout)
        elif provider_id == "gemini":
            result = _call_gemini(api_key, model, prompt, timeout)
        elif provider_id == "cohere":
            result = _call_cohere(api_key, model, prompt, timeout)
        else:
            raise RuntimeError(f"Unsupported provider: {provider_id}")

        if not silent:
            print(f"  [AI: {config.get('name', provider_id)} \u2713]")
        return result

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        raise RuntimeError(f"HTTP {e.code} from {provider_id}: {body}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error calling {provider_id}: {e.reason}") from e
    except (ValueError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Invalid response from {provider_id} (bad JSON): {e}") from e


# ══════════════════════════════════════════════════════════════════
# RESPONSE CLEANER
# ══════════════════════════════════════════════════════════════════

def _clean(text: str) -> str:
    """
    Strip AI formatting noise from responses.

    WHY EACH STEP:
      1. <think>...</think> — DeepSeek R1 emits chain-of-thought here.
         We want only the final answer, not the reasoning trace.
      2. ```language ... ``` — Markdown code fences from AI formatting.
         Saral users see raw code; fences would confuse them.
      3. Leading/trailing whitespace — cosmetic cleanup.

    MEMORY NOTE:
      re.sub with DOTALL compiles a regex per call.
      For production scale, pre-compile at module level.
      We don't here because these functions are called rarely
      (user typing speed, not batch loops).
    """
    # Remove DeepSeek reasoning traces
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove markdown code fences
    text = re.sub(r"```[a-z]*\n?", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


# ══════════════════════════════════════════════════════════════════
# DEBUGGER AI HELP — with full pattern fallback
# Always returns useful output even when no AI key is configured.
# ══════════════════════════════════════════════════════════════════

def _pattern_debug_hint(error_type: str, error_msg: str,
                         variables: dict) -> str:
    """
    Pattern-based debugging hints used when AI is not configured.
    Covers the most common Saral runtime errors with clear, friendly advice.
    Always returns something useful — no silent failures.
    """
    hints = []
    em = error_msg.lower()

    if "IndexError" in error_type or "index out of range" in em:
        hints.append("Hint: You tried to access an item that does not exist in the list.")
        hints.append("      In Saral, list positions start at 1. Make sure your index")
        hints.append("      is between 1 and the length of the list.")

    elif "TypeError" in error_type and any(
        t in em for t in ("str", "int", "float", "can only concatenate")
    ):
        hints.append("Hint: You mixed text and numbers in an expression.")
        hints.append("      Fix: convert the number to text first —")
        hints.append("        store myNumber as text in t")
        hints.append("        show myText + t")

    elif "NameError" in error_type or "not defined" in em:
        m = re.search(r"name '(\w+)' is not defined", error_msg)
        v = m.group(1) if m else "that variable"
        hints.append(f"Hint: '{v}' has not been stored yet.")
        hints.append(f"      Fix: add  store someValue in {v}  before using it.")

    elif "ZeroDivisionError" in error_type:
        hints.append("Hint: Division by zero — the denominator is 0.")
        hints.append("      Fix: check the value before dividing —")
        hints.append("        if divisor = 0")
        hints.append("            show \"Cannot divide by zero\"")
        hints.append("        done")

    elif "FileNotFoundError" in error_type:
        m = re.search(r"'([^']+)'", error_msg)
        f = m.group(1) if m else "the file"
        hints.append(f"Hint: File '{f}' was not found.")
        hints.append("      Fix: check the file name spelling and make sure")
        hints.append("      it is in the same folder as your program.")

    elif "KeyError" in error_type:
        hints.append("Hint: You tried to read a dictionary key that does not exist.")
        hints.append("      Fix: make sure you used  set \"key\" of dict to value")
        hints.append("      before reading it.")

    elif "RecursionError" in error_type:
        hints.append("Hint: A function called itself endlessly (infinite recursion).")
        hints.append("      Fix: add a stopping condition inside the function.")

    elif error_type or error_msg:
        hints.append(f"Hint: {error_type} — {error_msg[:120]}")
        hints.append("      Use 'vars' to inspect all current values.")
        hints.append("      Use 'list' to see where you are in the code.")
        hints.append("      Run  saral --setup-ai  to enable full AI diagnosis.")

    else:
        hints.append("Tip:  Use 'vars'    to see all current variable values.")
        hints.append("Tip:  Use 'list'    to see your position in the code.")
        hints.append("Tip:  Use 'explain' to understand what the current line does.")
        hints.append("Tip:  Run  saral --setup-ai  to enable full AI-powered analysis.")

    if variables:
        snapshot = ", ".join(
            f"{k}={repr(v)}" for k, v in list(variables.items())[:5]
        )
        hints.append(f"Values now: {snapshot}")

    return "\n".join(hints)


def debug_hint(session_context: str, error_type: str = "",
               error_msg: str = "", variables: dict = None) -> str:
    """
    AI-powered debug analysis with automatic pattern fallback.

    Called by debugger.py at three moments:
      1. Automatically when a runtime error occurs
      2. When the user types 'fix' or 'explain' at the debug> prompt
      3. After the program completes if there was an error

    AI path  — sends the full session context to the configured AI provider.
    Fallback — pattern-based hints so the user always gets useful feedback
               even with no API key configured.
    """
    prompt = f"""You are a Saral programming language debugger assistant.
A developer is debugging a Saral program and needs your help.
You have the COMPLETE session history — every step taken, every variable
value, every error that occurred. Use this full context to give a precise
and helpful diagnosis.

{_cap_text(session_context, max_chars=4000)}

Your task:
1. Identify what is wrong (or what might go wrong if no error yet).
2. Explain it in simple plain English — no jargon, assume a beginner.
3. Point to the exact line number that is the problem.
4. Show the corrected Saral code for that line if needed.
5. If no error, explain what the current variable values mean.

Be specific — reference actual variable names and line numbers from
the session above. Keep your answer under 10 lines.
"""
    try:
        result = _call_ai(prompt, silent=True)
        return _clean(result)
    except RuntimeError:
        return _pattern_debug_hint(error_type, error_msg, variables or {})


# ══════════════════════════════════════════════════════════════════
# PUBLIC API — 5 AI FEATURES
# ══════════════════════════════════════════════════════════════════

# ── 1. CODE GENERATOR ─────────────────────────────────────────────

def generate_code(description: str) -> str:
    """
    User describes what they want in plain English.
    Returns valid Saral code that implements it.

    Pipeline:
      1. Call AI with a strict Saral-only prompt
      2. Run the output through _sanitize_saral() to fix common Python slips
      3. Validate with the Saral compiler
      4. If errors remain, send them back to AI for one correction pass
      5. Sanitize and return the best available result
    """
    description = _cap_text(description, max_chars=500)

    prompt = f"""You are a Saral programming language code generator.
Your ONLY job is to write valid Saral code. NEVER write Python.

{SARAL_REFERENCE}

{_SARAL_FORBIDDEN}

TASK: Write Saral code that does exactly this:
"{description}"

MANDATORY RULES — breaking any rule makes the code unusable:
- Return ONLY raw Saral code. No explanations. No markdown. No backticks.
- Every single line must use ONLY the keywords shown in the reference above.
- End-of-line colons (:) are FORBIDDEN — Saral never uses them.
- Do NOT write print(), input(), len(), def, import, class, x=value, x+=n.
- Use # for comments — they are welcome and encouraged.
- Keep it simple. One task per line.

Saral code:"""

    try:
        generated = _call_ai(prompt)
        generated = _clean(generated)
    except RuntimeError:
        return _pattern_generate(description)

    # ── Step 1: rule-based sanitizer ──────────────────────────────
    generated = _sanitize_saral(generated)

    # ── Step 2: validate with Saral compiler ──────────────────────
    errors = _validate_saral(generated)

    # ── Step 3: retry with error feedback if still invalid ────────
    if errors:
        error_summary = "\n".join(f"  - {e}" for e in errors[:6])
        retry_prompt = f"""The Saral code you wrote has syntax errors. Rewrite it correctly.

{SARAL_REFERENCE}

{_SARAL_FORBIDDEN}

ORIGINAL TASK: "{description}"

YOUR BROKEN CODE:
{generated}

ERRORS FOUND BY SARAL COMPILER:
{error_summary}

Fix ALL errors. Return ONLY corrected Saral code. No explanations. No markdown:"""

        try:
            generated = _call_ai(retry_prompt)
            generated = _clean(generated)
            generated = _sanitize_saral(generated)
        except RuntimeError:
            pass   # keep sanitized first attempt

    return generated


# ── 2. ERROR FIXER ────────────────────────────────────────────────

def fix_error(saral_code: str, error_message: str) -> dict:
    """
    Takes broken Saral code and an error message.
    Returns a dict:
      explanation  — plain English: what went wrong
      fixed_code   — corrected Saral code
      fix_summary  — one-line: what was changed
    """
    # Protect against huge pastes — cap both inputs
    saral_code    = _cap_text(saral_code,    max_chars=1000)
    error_message = _cap_text(error_message, max_chars=300)

    prompt = f"""You are a Saral programming language teacher helping a beginner.

{SARAL_REFERENCE}

BROKEN SARAL CODE:
{saral_code}

ERROR MESSAGE:
{error_message}

Your job:
1. Explain what went wrong in simple plain English (1-3 sentences, no jargon).
2. Show the corrected Saral code.
3. Give a one-line summary of what was fixed.

Respond in this EXACT format (no other text before or after):
EXPLANATION: <plain English explanation here>
FIXED_CODE:
<corrected saral code here>
FIX_SUMMARY: <one line summary>"""

    try:
        result = _call_ai(prompt)
        result = _clean(result)
        return _parse_fix_response(result, saral_code)
    except RuntimeError:
        return {
            "explanation": (
                "AI is not available right now. "
                "Run: python saral.py --setup-ai to configure an AI provider."
            ),
            "fixed_code":  saral_code,
            "fix_summary": "Could not auto-fix — AI unavailable."
        }


def _parse_fix_response(text: str, original_code: str) -> dict:
    """Extract structured fields from the AI fix response."""
    explanation = ""
    fixed_code  = ""
    fix_summary = ""

    exp_match  = re.search(
        r"EXPLANATION:\s*(.+?)(?=FIXED_CODE:|FIX_SUMMARY:|$)", text, re.DOTALL
    )
    code_match = re.search(
        r"FIXED_CODE:\s*\n(.+?)(?=FIX_SUMMARY:|$)", text, re.DOTALL
    )
    fix_match  = re.search(r"FIX_SUMMARY:\s*(.+?)$", text, re.DOTALL)

    if exp_match:
        explanation = exp_match.group(1).strip()
    if code_match:
        fixed_code  = code_match.group(1).strip()
    if fix_match:
        fix_summary = fix_match.group(1).strip()

    return {
        "explanation": explanation or "Something went wrong — check the error message above.",
        "fixed_code":  fixed_code  or original_code,
        "fix_summary": fix_summary or "Unknown fix."
    }


# ── 3. CODE EXPLAINER ─────────────────────────────────────────────

def explain_code(saral_code: str) -> str:
    """
    Takes Saral code and explains what it does in plain English.
    Useful when reading someone else's code or AI-generated code.
    """
    saral_code = _cap_text(saral_code, max_chars=1000)

    prompt = f"""You are a Saral programming language teacher.

{SARAL_REFERENCE}

SARAL CODE TO EXPLAIN:
{saral_code}

Explain what this code does in simple plain English.
Rules:
- Write as if explaining to someone who has never coded before.
- No technical jargon.
- Step by step — one step per line.
- Maximum 10 lines.
- Do not show any code in your explanation.

Explanation:"""

    try:
        result = _call_ai(prompt)
        return _clean(result)
    except RuntimeError:
        return (
            "AI is not available right now. "
            "Run: python saral.py --setup-ai to configure an AI provider."
        )


# ── 4. AUTOCOMPLETE ───────────────────────────────────────────────

def autocomplete(code_so_far: str, current_line: str = "") -> list:
    """
    Given the code so far and the current partial line,
    returns 1-3 suggested completions.

    Fast path: pattern matching (no API call, instant).
    Slow path: AI (only for complex, ambiguous cases).
    """
    # Always try fast pattern path first — saves API cost and latency
    pattern_suggestions = _pattern_autocomplete(current_line, code_so_far)
    if pattern_suggestions:
        return pattern_suggestions

    # AI path — only use last 15 lines for context (memory efficiency)
    context = "\n".join(code_so_far.strip().splitlines()[-15:])
    context = _cap_text(context, max_chars=600)

    prompt = f"""You are a Saral programming language autocomplete engine.

{SARAL_REFERENCE}

CODE SO FAR:
{context}

CURRENT PARTIAL LINE: "{current_line}"

Suggest the 3 most likely next lines the user wants to write.
Rules:
- Return ONLY 3 lines, one per line, numbered 1. 2. 3.
- Each suggestion must be valid Saral syntax.
- Match the context logically.
- No explanations.

Suggestions:"""

    try:
        result = _call_ai(prompt, silent=True)
        result = _clean(result)
        suggestions = []
        for line in result.splitlines():
            line = re.sub(r"^\d+[\.\)]\s*", "", line).strip()
            if line:
                suggestions.append(line)
        return suggestions[:3]
    except RuntimeError:
        return []


# ══════════════════════════════════════════════════════════════════
# PATTERN LIBRARY — Tier 3 code generation
# No AI, no internet, always works.
# Keys are tuples of words to match; values are Saral code templates.
# ══════════════════════════════════════════════════════════════════

_PATTERN_TEMPLATES: dict = {
    ("hello", "world"):
        'show "Hello, World!"',

    ("add", "two", "number"):
        'ask number "Enter first number: " and store in a\n'
        'ask number "Enter second number: " and store in b\n'
        'store a + b in result\n'
        'show result',

    ("greet", "name"):
        'ask "Enter your name: " and store in name\n'
        'show "Hello, " + name',

    ("average", "list"):
        'make list called numbers\n'
        'add 10 to numbers\nadd 20 to numbers\nadd 30 to numbers\n'
        'store average of numbers in avg\n'
        'show avg',

    ("count", "1", "10"):
        'count from 1 to 10 as n\n    show n\ndone',

    ("read", "file"):
        'read file "myfile.txt" and store in content\nshow content',

    ("write", "file"):
        'store "Hello" in message\nwrite message to file "output.txt"',

    ("sort", "list"):
        'make list called items\n'
        'add 3 to items\nadd 1 to items\nadd 2 to items\n'
        'sort items\nshow items',

    ("dictionary", "store"):
        'make dictionary called data\n'
        'set "name" of data to "Asha"\n'
        'set "age" of data to 30\n'
        'store value of "name" in data in name\n'
        'show name',

    ("random", "number"):
        'store random number from 1 to 100 in lucky\nshow lucky',

    ("today", "date"):
        'store today in date\nshow date',

    ("repeat", "loop"):
        'repeat 5 times\n    show "hello"\ndone',

    ("function", "define"):
        'define greet using name\n    show "Hello " + name\nend\n\ncall greet with "World"',

    ("calculator", "math"):
        'ask number "Enter first number: " and store in a\n'
        'ask "Enter operation (+, -, *, /): " and store in op\n'
        'ask number "Enter second number: " and store in b\n'
        'if op = "+"\n    store a + b in result\ndone\n'
        'if op = "-"\n    store a - b in result\ndone\n'
        'if op = "*"\n    store a * b in result\ndone\n'
        'if op = "/"\n    store a / b in result\ndone\n'
        'show result',

    ("even", "odd"):
        'ask number "Enter a number: " and store in n\n'
        'if n % 2 = 0\n    show "Even"\notherwise\n    show "Odd"\ndone',

    ("password", "secret"):
        'ask "Enter password: " and store in entered\n'
        'store "saral123" in correct\n'
        'if entered = correct\n    show "Access granted"\notherwise\n    show "Wrong password"\ndone',
}


def _pattern_generate(description: str) -> str:
    """
    Match the description words against pattern templates.
    Returns the best-matching Saral code, or a helpful fallback message.
    """
    desc_words = set(description.lower().split())
    best_match: Optional[str] = None
    best_score = 0

    for keywords, template in _PATTERN_TEMPLATES.items():
        score = sum(1 for k in keywords if k in desc_words)
        if score > best_score:
            best_score = score
            best_match = template

    if best_match and best_score >= 1:
        return best_match

    return (
        "# Could not generate code from that description.\n"
        "# Run: python saral.py --setup-ai to configure an AI provider.\n"
        'show "AI not available. Run --setup-ai to enable code generation."'
    )


def _sanitize_saral(code: str) -> str:
    """
    Convert common Python constructs in AI output to their Saral equivalents.
    This is a line-by-line rule pass applied BEFORE compiler validation.

    Each rule targets one specific Python habit the AI tends to use:
      print(...)     → show ...
      elif / else:   → otherwise if / otherwise
      for x in y:   → for each x in y
      range(n)       → count from 1 to n as i
      if/while with trailing colon → remove the colon
      def func():    → define func
      var += / -=    → increase / decrease
      list.append()  → add to list
      import x       → use x
      x = value      → store value in x   (only for bare assignments)
    """
    _SARAL_KEYWORDS = {
        'store', 'if', 'make', 'add', 'show', 'ask', 'count', 'repeat',
        'while', 'for', 'define', 'call', 'return', 'increase', 'decrease',
        'write', 'read', 'append', 'delete', 'sort', 'reverse', 'set',
        'remove', 'global', 'include', 'use', 'check', 'find', 'replace',
        'split', 'join', 'wait', 'stop', 'skip', 'exit', 'clear', 'try',
        'catch', 'raise', 'fetch', 'run', 'otherwise', 'done', 'end',
    }

    fixed = []
    for line in code.splitlines():
        stripped = line.strip()
        indent   = line[: len(line) - len(line.lstrip())]

        # Blank lines and comments pass through unchanged
        if not stripped or stripped.startswith('#'):
            fixed.append(line)
            continue

        # ── Inline expression substitutions — applied first so every subsequent
        #    rule benefits from them (e.g. print(str(x)) → print(x as text) → show x as text)
        line     = re.sub(r'\blen\s*\(\s*(\w+)\s*\)',  r'length of \1', line)
        line     = re.sub(r'\bstr\s*\(\s*(\w+)\s*\)',  r'\1 as text',   line)
        line     = re.sub(r'\bint\s*\(\s*(\w+)\s*\)',  r'\1',           line)
        line     = re.sub(r'\bfloat\s*\(\s*(\w+)\s*\)', r'\1',          line)
        stripped = line.strip()

        # print(...) → show ...
        m = re.match(r'^print\s*\((.+)\)\s*$', stripped)
        if m:
            fixed.append(f'{indent}show {m.group(1).strip()}')
            continue

        # elif condition: → otherwise if condition  (and == → =)
        m = re.match(r'^elif\s+(.+?):\s*$', stripped)
        if m:
            cond = re.sub(r'\s*==\s*', ' = ', m.group(1).strip())
            fixed.append(f'{indent}otherwise if {cond}')
            continue

        # else: → otherwise
        if re.match(r'^else\s*:\s*$', stripped):
            fixed.append(f'{indent}otherwise')
            continue

        # for item in list: → for each item in list
        m = re.match(r'^for\s+(\w+)\s+in\s+(?!range)(\w+)\s*:\s*$', stripped)
        if m:
            fixed.append(f'{indent}for each {m.group(1)} in {m.group(2)}')
            continue

        # for i in range(n): → count from 1 to n as i
        # for i in range(a, b): → count from a to b as i
        m = re.match(r'^for\s+(\w+)\s+in\s+range\s*\((.+)\)\s*:\s*$', stripped)
        if m:
            var  = m.group(1)
            args = [a.strip() for a in m.group(2).split(',')]
            if len(args) == 1:
                fixed.append(f'{indent}count from 1 to {args[0]} as {var}')
            else:
                fixed.append(f'{indent}count from {args[0]} to {args[1]} as {var}')
            continue

        # if condition: → if condition  (remove colon, replace == with =)
        m = re.match(r'^(if\s+.+?):\s*$', stripped)
        if m:
            cond_line = re.sub(r'\s*==\s*', ' = ', m.group(1))
            fixed.append(f'{indent}{cond_line}')
            continue

        # while condition: → while condition  (remove colon, replace == with =)
        m = re.match(r'^(while\s+.+?):\s*$', stripped)
        if m:
            cond_line = re.sub(r'\s*==\s*', ' = ', m.group(1))
            fixed.append(f'{indent}{cond_line}')
            continue

        # try: → try
        if re.match(r'^try\s*:\s*$', stripped):
            fixed.append(f'{indent}try')
            continue

        # except ...: → catch
        if re.match(r'^except.*:\s*$', stripped):
            fixed.append(f'{indent}catch')
            continue

        # def func(params): → define func using params
        m = re.match(r'^def\s+(\w+)\s*\(([^)]*)\)\s*:\s*$', stripped)
        if m:
            fname  = m.group(1)
            params = m.group(2).strip()
            if params:
                fixed.append(f'{indent}define {fname} using {params}')
            else:
                fixed.append(f'{indent}define {fname}')
            continue

        # var += n → increase var by n
        m = re.match(r'^(\w+)\s*\+=\s*(.+)$', stripped)
        if m:
            fixed.append(f'{indent}increase {m.group(1)} by {m.group(2).strip()}')
            continue

        # var -= n → decrease var by n
        m = re.match(r'^(\w+)\s*-=\s*(.+)$', stripped)
        if m:
            fixed.append(f'{indent}decrease {m.group(1)} by {m.group(2).strip()}')
            continue

        # list.append(val) → add val to list
        m = re.match(r'^(\w+)\.append\s*\((.+)\)\s*$', stripped)
        if m:
            fixed.append(f'{indent}add {m.group(2).strip()} to {m.group(1)}')
            continue

        # import x → use x
        m = re.match(r'^import\s+(\w+)\s*$', stripped)
        if m:
            fixed.append(f'{indent}use {m.group(1)}')
            continue

        # var = int(input("prompt")) / float(input("prompt")) → ask number "prompt" and store in var
        m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*(?:int|float)\s*\(\s*input\s*\((.+?)\)\s*\)\s*$', stripped)
        if m:
            fixed.append(f'{indent}ask number {m.group(2).strip()} and store in {m.group(1)}')
            continue

        # var = input("prompt") → ask "prompt" and store in var
        m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*input\s*\((.+)\)\s*$', stripped)
        if m:
            fixed.append(f'{indent}ask {m.group(2).strip()} and store in {m.group(1)}')
            continue

        # var = len(list) → store length of list in var
        m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*len\s*\(\s*(\w+)\s*\)\s*$', stripped)
        if m:
            fixed.append(f'{indent}store length of {m.group(2)} in {m.group(1)}')
            continue

        # var = []  → make list called var
        m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*\[\]\s*$', stripped)
        if m:
            fixed.append(f'{indent}make list called {m.group(1)}')
            continue

        # var = {}  → make dictionary called var
        m = re.match(r'^([a-zA-Z_]\w*)\s*=\s*\{\}\s*$', stripped)
        if m:
            fixed.append(f'{indent}make dictionary called {m.group(1)}')
            continue

        # var = value  (bare Python assignment — only when first word is not a Saral keyword)
        first_word = stripped.split()[0].lower() if stripped.split() else ''
        if first_word not in _SARAL_KEYWORDS:
            m = re.match(r'^([a-zA-Z_]\w*)\s*=(?!=)\s*(.+)$', stripped)
            if m:
                fixed.append(f'{indent}store {m.group(2).strip()} in {m.group(1)}')
                continue

        # Replace Python == with Saral = inside if/while/otherwise if conditions
        if re.match(r'^(if|while|otherwise if)\s+', stripped):
            line = re.sub(r'\s*==\s*', ' = ', line)

        fixed.append(line)

    result = '\n'.join(fixed)

    # ── Block-closer pass ──────────────────────────────────────────
    # If the code has no `done`/`end` at all (i.e. it came from Python
    # with indentation blocks), infer where they belong from dedents.
    if not any(re.match(r'^\s*(done|end)\s*$', l) for l in result.splitlines()):
        result = _add_saral_block_closers(result)

    return result


def _add_saral_block_closers(code: str) -> str:
    """
    Insert `done` / `end` before each dedent in code that has no block closers.
    `define` blocks use `end`; everything else uses `done`.
    `otherwise` / `otherwise if` are continuations — they don't close the if block.
    """
    BLOCK_KWS  = {'if', 'count', 'for', 'while', 'repeat', 'try', 'catch'}
    DEFINE_KWS = {'define'}
    CONT_KWS   = {'otherwise'}   # continuations of if — never close

    lines  = code.splitlines()
    result = []
    stack  = []   # list of [indent_col, closer_string]

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            result.append(line)
            continue

        this_indent = len(line) - len(line.lstrip())
        first_word  = stripped.split()[0].lower()

        # Dedented, non-continuation line → close open block(s)
        if stack and this_indent <= stack[-1][0] and first_word not in CONT_KWS:
            while stack and this_indent <= stack[-1][0]:
                col, closer = stack.pop()
                result.append(' ' * col + closer)

        result.append(line)

        if first_word in BLOCK_KWS | DEFINE_KWS:
            closer = 'end' if first_word in DEFINE_KWS else 'done'
            stack.append([this_indent, closer])

    # Close any blocks still open at end-of-file
    while stack:
        col, closer = stack.pop()
        result.append(' ' * col + closer)

    return '\n'.join(result)


def _validate_saral(code: str) -> list:
    """
    Compile the Saral code silently and return a list of parse-error strings.
    Returns [] when the code is fully valid.

    Uses a lazy import of pipeline.py (to avoid the circular import that would
    occur if imported at module level, since pipeline.py imports ai_helper.py).
    """
    import io
    from contextlib import redirect_stdout, redirect_stderr
    try:
        from pipeline import compile_saral   # lazy — avoids circular import
    except ImportError:
        return []   # compiler unavailable; assume valid

    captured_out = io.StringIO()
    captured_err = io.StringIO()
    try:
        with redirect_stdout(captured_out), redirect_stderr(captured_err):
            _, _, parse_errors = compile_saral(
                code, "<ai_generated>", show_warnings=False
            )
        return parse_errors or []
    except SystemExit:
        # compile_saral calls sys.exit on fatal errors; treat as error list
        output = captured_out.getvalue().strip()
        return [output] if output else ["Code contains invalid Saral syntax"]
    except Exception as exc:
        return [str(exc)]


def validate_generated_code(code: str):
    """
    Public function called by saral.py after displaying generated code.
    Returns (is_valid: bool, errors: list[str]).
    """
    errors = _validate_saral(code)
    return (len(errors) == 0), errors


def _pattern_autocomplete(current_line: str, context: str) -> list:
    """
    Instant rule-based autocomplete — covers the most common Saral patterns.
    No AI, no internet, zero latency.
    """
    cl = current_line.strip().lower()

    if cl in ("st", "sto", "stor"):
        return ["store  in ", "store today in date", "store current time in t"]
    if cl.startswith("store") and "in" not in cl:
        return ["store  in result"]
    if cl in ("sh", "sho"):
        return ["show ", "show blank", "show error"]
    if cl == "if":
        return ["if  > 0", 'if  = ""', "if  > 0\n    \ndone"]
    if cl in ("re", "rep"):
        return ["repeat 5 times", "repeat  times", "return "]
    if cl in ("fo", "for"):
        return ["for each item in ", "for each line in lines"]
    if cl in ("de", "def"):
        return ["define  using ", "define  ", "decrease  by 1"]
    if cl in ("ma", "mak"):
        return ["make list called ", "make dictionary called "]
    if cl == "ad":
        return ["add  to "]
    if cl == "ca":
        return ["call  with ", "call ", "catch"]
    if cl == "wh":
        return ["while  > 0", 'write  to file ""']
    if cl == "co":
        return ["count from 1 to  as n", "count from 1 to 10 as n"]
    if cl == "as":
        return ['ask "" and store in ', 'ask number "" and store in ', 'ask ai "" and store in ']
    if cl == "us":
        return ["use math", "use pandas", "use json"]

    return []


# ── 5. QUERY (called from inside Saral programs) ──────────────────

def _pattern_query(prompt: str, data: str = "") -> str:
    """
    Tier 3 query fallback — pattern-based answers for common questions.
    Always works. No internet, no API key, no memory overhead.
    """
    p = prompt.lower().strip()

    # Math questions
    math_match = re.search(r"what is (\d+)\s*([\+\-\*\/])\s*(\d+)", p)
    if math_match:
        a   = int(math_match.group(1))
        op  = math_match.group(2)
        b   = int(math_match.group(3))
        res = {"+": a+b, "-": a-b, "*": a*b, "/": (a/b if b else "undefined")}.get(op)
        return f"{a} {op} {b} = {res}"

    # Saral syntax help
    if "store" in p and any(w in p for w in ("do", "mean", "what")):
        return ("The store command saves a value into a variable. "
                "Example: store 10 in price — saves the number 10 into price.")
    if "show" in p and any(w in p for w in ("do", "mean", "what")):
        return "The show command displays output. Example: show price — prints the value of price."
    if "if" in p and any(w in p for w in ("do", "mean", "what")):
        return "The if command checks a condition. Example: if price > 100 / show 'expensive' / done"
    if "repeat" in p and any(w in p for w in ("do", "mean")):
        return "The repeat command runs a block of code multiple times. Example: repeat 5 times / show 'hello' / done"
    if "define" in p and any(w in p for w in ("do", "mean")):
        return "The define command creates a function. Example: define greet / show 'Hello' / end"
    if "saral lang" in p or "saral language" in p:
        return ("Saral Lang is a programming language that reads like plain English. "
                "Developed by Asha V S from Kerala, India.")

    # Data analysis
    if data:
        numbers = re.findall(r"(\w+)[=:](\d+)", data)
        if numbers:
            if any(w in p for w in ("highest", "maximum", "most", "best")):
                best = max(numbers, key=lambda x: int(x[1]))
                return f"The highest value is {best[0]} with {best[1]}."
            if any(w in p for w in ("lowest", "minimum", "least")):
                worst = min(numbers, key=lambda x: int(x[1]))
                return f"The lowest value is {worst[0]} with {worst[1]}."

        raw_nums = re.findall(r"\d+", data)
        if raw_nums:
            nums = [int(n) for n in raw_nums]
            if any(w in p for w in ("average", "mean")):
                return f"The average is {sum(nums)/len(nums):.2f}."
            if any(w in p for w in ("total", "sum")):
                return f"The total is {sum(nums)}."

    # General knowledge
    if "capital" in p and "kerala" in p:
        return "The capital of Kerala is Thiruvananthapuram."
    if "capital" in p and "india" in p:
        return "The capital of India is New Delhi."
    if "pi" in p or "3.14" in p:
        return "Pi (π) is approximately 3.14159265358979."
    if "speed of light" in p:
        return "The speed of light is approximately 299,792,458 metres per second."

    return ""   # No pattern matched — caller will provide final fallback message


def query(prompt_text: str, data: str = "") -> str:
    """
    Called from inside Saral programs via:
      ask ai "..." using variable and store in result

    Returns a plain string result.
    Fallback chain: Configured AI → Pattern matching → Helpful message.
    """
    # Build the full prompt
    if data:
        full_prompt = f"{prompt_text}\n\nContext data:\n{_cap_text(data, 800)}"
    else:
        full_prompt = _cap_text(prompt_text, 400)

    # Try configured AI first
    try:
        result = _call_ai(full_prompt, silent=True)
        return _clean(result)
    except RuntimeError:
        pass

    # Tier 3: Pattern matching (always works)
    pattern_result = _pattern_query(prompt_text, data)
    if pattern_result:
        return pattern_result

    # Final fallback message
    return (
        "AI is not available right now. "
        "Run: python saral.py --setup-ai to configure an AI provider."
    )


# ══════════════════════════════════════════════════════════════════
# AI STATUS CHECK
# Called by: python saral.py --status
# ══════════════════════════════════════════════════════════════════

def check_ai_status() -> dict:
    """
    Check which AI is configured and whether it is reachable.
    Returns a status dict consumed by saral.py --status.

    REASONING:
      We ask ai_config.py for the active config (file or env var).
      We do NOT make a live test call here — that is done during
      --setup-ai. Status just reports what is saved.
      Live-testing on every --status call would waste API credits
      and slow the command down for no benefit.
    """
    from ai_config import get_active_ai

    config = get_active_ai()

    return {
        "configured":     config is not None,
        "provider":       config["provider"]              if config else None,
        "provider_name":  config.get("name", "Unknown")  if config else None,
        "model":          config["model"]                 if config else None,
        "pattern":        True,   # always available
    }
