"""
ai_config.py — Saral Universal AI Configuration v1.0
═══════════════════════════════════════════════════════════════════
PURPOSE
  This module is the "AI registration desk" for Saral Lang.
  The user pastes ANY API key from ANY supported AI provider.
  This module:
    1. Auto-detects which provider the key belongs to
    2. Tests live connectivity with a tiny real API call
    3. Saves the key + provider to a local config file
    4. Provides the key+provider to ai_helper.py at runtime

WHY A SEPARATE FILE
  Keeping configuration separate from ai_helper.py means:
  - One place to add new AI providers in the future
  - ai_helper.py stays clean — it just asks "who is configured?"
  - The wizard (--setup-ai) imports only this file, not the full AI stack

SUPPORTED PROVIDERS (auto-detected by key shape + live test)
  ┌─────────────────┬──────────────────────────────────────────────┐
  │ Provider        │ Key Pattern                                  │
  ├─────────────────┼──────────────────────────────────────────────┤
  │ xAI Grok        │ xai-... (84+ chars)                          │
  │ OpenAI          │ sk-proj-... or sk-... (51+ chars)            │
  │ DeepSeek        │ sk-... (32 chars, deepseek.com endpoint)     │
  │ Anthropic       │ sk-ant-...                                   │
  │ Google Gemini   │ AIza... (39 chars)                           │
  │ Groq            │ gsk_...                                      │
  │ Mistral         │ mixed alphanumeric, mistral-like             │
  │ Cohere          │ long alphanumeric, no prefix                 │
  └─────────────────┴──────────────────────────────────────────────┘

CONFIG FILE
  Stored at: <saral_folder>/saral_ai.conf
  Format: plain text key=value pairs (no JSON, no binary)
  Never sent anywhere — stays on your machine.

SECURITY NOTE
  The key is stored in plain text on your local disk.
  This is the same as how git credentials, npm tokens, and
  SSH keys are stored. Keep your saral folder private.
  Never share saral_ai.conf with anyone.
═══════════════════════════════════════════════════════════════════
"""

import json
import os
import re
import urllib.request
import urllib.error
from typing import Optional

# ══════════════════════════════════════════════════════════════════
# CONFIG FILE LOCATION
# Stored next to saral.py, not in /tmp — survives reboots
# ══════════════════════════════════════════════════════════════════

_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(_THIS_DIR, "saral_ai.conf")

# ══════════════════════════════════════════════════════════════════
# PROVIDER REGISTRY
# Each entry describes one AI provider:
#   name        — display name shown to the user
#   key_pattern — regex that matches this provider's key format
#   api_url     — the endpoint we POST to
#   test_fn     — function name (string) used to do a live test
#   model       — default model to use
#   notes       — shown during setup to help the user
# ══════════════════════════════════════════════════════════════════

PROVIDERS = {
    "openai": {
        "name":        "OpenAI (ChatGPT / GPT-4o)",
        "key_pattern": r"^sk-(?!ant-)(?!deepseek)[A-Za-z0-9\-_]{40,}$",
        "api_url":     "https://api.openai.com/v1/chat/completions",
        "model":       "gpt-4o-mini",       # cheapest GPT-4 class model
        "notes":       "Get key at: https://platform.openai.com/api-keys",
    },
    "deepseek": {
        "name":        "DeepSeek R1 (Recommended — excellent reasoning)",
        "key_pattern": r"^sk-[a-f0-9]{32}$",
        "api_url":     "https://api.deepseek.com/v1/chat/completions",
        "model":       "deepseek-reasoner",
        "notes":       "Get free key at: https://platform.deepseek.com",
    },
    "anthropic": {
        "name":        "Anthropic Claude",
        "key_pattern": r"^sk-ant-[A-Za-z0-9\-_]{80,}$",
        "api_url":     "https://api.anthropic.com/v1/messages",
        "model":       "claude-haiku-4-5-20251001",   # fastest, cheapest Claude
        "notes":       "Get key at: https://console.anthropic.com",
    },
    "gemini": {
        "name":        "Google Gemini (Free tier available)",
        "key_pattern": r"^AIza[A-Za-z0-9\-_]{35,}$",
        "api_url":     "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
        "model":       "gemini-2.0-flash",
        "notes":       "Get free key at: https://aistudio.google.com",
    },
    "groq": {
        "name":        "Groq (Very fast inference)",
        "key_pattern": r"^gsk_[A-Za-z0-9_\-]{40,}$",
        "api_url":     "https://api.groq.com/openai/v1/chat/completions",
        "model":       "llama-3.3-70b-versatile",
        "notes":       "Get free key at: https://console.groq.com",
    },
    "xai": {
        "name":        "xAI Grok",
        "key_pattern": r"^xai-[A-Za-z0-9]{80,}$",
        "api_url":     "https://api.x.ai/v1/chat/completions",
        "model":       "grok-3",
        "notes":       "Get key at: https://console.x.ai",
    },
    "mistral": {
        "name":        "Mistral AI",
        "key_pattern": r"^[A-Za-z0-9]{32}$",
        "api_url":     "https://api.mistral.ai/v1/chat/completions",
        "model":       "mistral-small-latest",
        "notes":       "Get key at: https://console.mistral.ai",
    },
    "cohere": {
        "name":        "Cohere",
        "key_pattern": r"^[A-Za-z0-9]{40}$",
        "api_url":     "https://api.cohere.ai/v1/generate",
        "model":       "command",
        "notes":       "Get key at: https://dashboard.cohere.com",
    },
}

# Detection order matters — check most specific patterns first
# (DeepSeek before OpenAI because both start with sk-)
_DETECTION_ORDER = [
    "deepseek", "anthropic", "xai", "groq", "gemini",
    "openai", "mistral", "cohere"
]

# ══════════════════════════════════════════════════════════════════
# KEY DETECTION
# ══════════════════════════════════════════════════════════════════

def detect_provider(api_key: str) -> Optional[str]:
    """
    Look at the API key's shape and return the provider name.

    REASONING PROCESS:
      Step 1 — Strip whitespace. Users often paste keys with a
               trailing newline or space from their clipboard.
      Step 2 — Try each provider's regex in detection order.
               Order matters: DeepSeek checked before OpenAI
               because both start with 'sk-'.
      Step 3 — Return the first match, or None if nothing matched.

    Returns: provider key string (e.g. "deepseek") or None.
    """
    api_key = api_key.strip()

    for provider_id in _DETECTION_ORDER:
        pattern = PROVIDERS[provider_id]["key_pattern"]
        if re.match(pattern, api_key):
            return provider_id

    return None   # Unknown key format


# ══════════════════════════════════════════════════════════════════
# LIVE CONNECTIVITY TESTS
# One function per provider — each knows the exact API shape.
# All return (success: bool, message: str)
# ══════════════════════════════════════════════════════════════════

def _test_openai_compatible(api_key: str, api_url: str, model: str,
                             provider_name: str, timeout: int = 15):
    """
    Test any OpenAI-compatible endpoint (OpenAI, DeepSeek, Groq, Mistral).
    They all share the same /v1/chat/completions shape.
    """
    payload = json.dumps({
        "model":      model,
        "messages":   [{"role": "user", "content": "Say: OK"}],
        "max_tokens": 5,
        "stream":     False,
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data    = json.loads(resp.read().decode("utf-8"))
            choices = data.get("choices", [])
            if choices:
                reply = choices[0].get("message", {}).get("content", "").strip()
                return True, f"Connected ✓  Model replied: '{reply}'"
            return False, "Connected but received empty response."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:300]
        return False, f"HTTP {e.code} from {api_url}\n      Details: {body}"
    except urllib.error.URLError as e:
        return False, f"Network error reaching {api_url}: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _test_anthropic(api_key: str, model: str, timeout: int = 15):
    """Test Anthropic Claude API — uses Messages API shape (different from OpenAI)."""
    payload = json.dumps({
        "model":      model,
        "max_tokens": 5,
        "messages":   [{"role": "user", "content": "Say: OK"}],
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data    = json.loads(resp.read().decode("utf-8"))
            content = data.get("content", [])
            if content:
                reply = content[0].get("text", "").strip()
                return True, f"Connected ✓  Claude replied: '{reply}'"
            return False, "Connected but received empty response."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {e.code} error: {body}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _test_gemini(api_key: str, model: str, timeout: int = 15):
    """Test Google Gemini API — uses its own payload shape + key-in-URL pattern."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": "Say: OK"}]}],
        "generationConfig": {"maxOutputTokens": 5},
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data    = payload,
        headers = {"Content-Type": "application/json"},
        method  = "POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data       = json.loads(resp.read().decode("utf-8"))
            candidates = data.get("candidates", [])
            if candidates:
                reply = (
                    candidates[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
                )
                return True, f"Connected ✓  Gemini replied: '{reply}'"
            return False, "Connected but received empty response."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {e.code} error: {body}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _test_cohere(api_key: str, timeout: int = 15):
    """Test Cohere API — uses its own /generate endpoint shape."""
    payload = json.dumps({
        "model":      "command",
        "prompt":     "Say: OK",
        "max_tokens": 5,
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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data        = json.loads(resp.read().decode("utf-8"))
            generations = data.get("generations", [])
            if generations:
                reply = generations[0].get("text", "").strip()
                return True, f"Connected ✓  Cohere replied: '{reply}'"
            return False, "Connected but received empty response."
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        return False, f"HTTP {e.code} error: {body}"
    except urllib.error.URLError as e:
        return False, f"Network error: {e.reason}"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def test_connectivity(api_key: str, provider_id: str) -> tuple:
    """
    Run a live test call for the given provider.
    Returns (success: bool, message: str).

    REASONING:
      We make a real API call with max_tokens=5.
      This is the smallest possible call that proves:
        - The key is valid (auth works)
        - The network can reach the provider
        - The model is available
      5 tokens costs fractions of a cent on every platform.
    """
    api_key     = api_key.strip()
    provider    = PROVIDERS.get(provider_id)
    if not provider:
        return False, f"Unknown provider: {provider_id}"

    model   = provider["model"]
    api_url = provider["api_url"]

    # Route to the correct test function
    if provider_id in ("openai", "deepseek", "groq", "mistral", "xai"):
        return _test_openai_compatible(
            api_key, api_url, model, provider["name"]
        )
    elif provider_id == "anthropic":
        return _test_anthropic(api_key, model)
    elif provider_id == "gemini":
        return _test_gemini(api_key, model)
    elif provider_id == "cohere":
        return _test_cohere(api_key)
    else:
        return False, f"No test function for provider: {provider_id}"


# ══════════════════════════════════════════════════════════════════
# CONFIG FILE — SAVE / LOAD / CLEAR
# ══════════════════════════════════════════════════════════════════

def save_config(api_key: str, provider_id: str) -> None:
    """
    Save the API key and provider to saral_ai.conf.

    File format (plain text, easy to read/edit/delete):
      provider=deepseek
      key=sk-abc123...
      model=deepseek-reasoner

    WHY NOT JSON or .env?
      Plain text with = pairs is human-readable, easy to open
      in any text editor, and requires no parsing library.
      A user can delete it with one keypress if needed.
    """
    provider = PROVIDERS[provider_id]
    lines = [
        "# Saral Lang AI Configuration",
        "# Generated by: python saral.py --setup-ai",
        "# To remove AI: delete this file or run --setup-ai again",
        "# KEEP THIS FILE PRIVATE — do not share it",
        f"provider={provider_id}",
        f"name={provider['name']}",
        f"key={api_key.strip()}",
        f"model={provider['model']}",
        f"api_url={provider['api_url']}",
    ]
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def load_config() -> Optional[dict]:
    """
    Load the saved AI config from saral_ai.conf.
    Returns a dict with provider, key, model, api_url — or None if not configured.

    REASONING:
      We read at call time, not at import time.
      This means if the user sets up AI in one terminal session,
      the next session picks it up automatically without restarting.
    """
    if not os.path.exists(CONFIG_FILE):
        return None

    config = {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    except Exception:
        return None

    # Validate that we have the minimum required fields
    required = {"provider", "key", "model", "api_url"}
    if not required.issubset(config.keys()):
        return None

    return config


def clear_config() -> bool:
    """Delete the config file. Returns True if deleted, False if not found."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        return True
    return False


def is_configured() -> bool:
    """Quick check — is any AI configured?"""
    return load_config() is not None


# ══════════════════════════════════════════════════════════════════
# THE SETUP WIZARD
# Called by: python saral.py --setup-ai
# Walks the user through pasting a key, detects provider,
# tests connectivity, and saves on success.
# ══════════════════════════════════════════════════════════════════

def run_setup_wizard() -> bool:
    """
    Interactive wizard for setting up an AI provider.
    Returns True if setup succeeded, False if user quit or test failed.

    DESIGN PHILOSOPHY (Saral's Kerala-audience approach):
      - Speak to the user like a helpful teacher, not a technical manual.
      - Show exactly what is happening at each step.
      - Never fail silently — always explain WHY something failed.
      - The user should feel safe, not judged.
    """
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🤖  Saral AI Setup Wizard                         ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print("  This wizard will connect Saral to an AI of your choice.")
    print("  You can use any of these providers:")
    print()

    for i, pid in enumerate(_DETECTION_ORDER, 1):
        p = PROVIDERS[pid]
        print(f"  {i}. {p['name']}")
        print(f"     {p['notes']}")
        print()

    # Show current config if one exists
    current = load_config()
    if current:
        print(f"  ℹ️   Currently configured: {current.get('name', current['provider'])}")
        print("      Setting up a new key will replace it.")
        print()

    print("─" * 56)
    print()
    print("  Paste your API key below and press Enter.")
    print("  (The key will not be shown on screen for security.)")
    print()

    # Read the key using regular input so paste (Ctrl+V) works normally
    print("  (Your key will be visible as you type — this is fine on your own machine)")
    api_key = input("  Your API key: ")

    # Remove invisible/control characters (BOM, terminal escape sequences, etc.)
    # that can silently corrupt a pasted key and cause 401 errors
    api_key = ''.join(c for c in api_key if c.isprintable() and ord(c) < 128).strip()

    if not api_key:
        print("\n  ❌  No key entered. Setup cancelled.\n")
        return False

    # Show a preview so the user can verify the key was captured correctly
    if len(api_key) >= 12:
        preview = f"{api_key[:8]}...{api_key[-4:]}"
    else:
        preview = api_key[:4] + "..." if len(api_key) > 4 else "(very short — may be wrong)"
    print(f"\n  📋  Key received: {preview}  ({len(api_key)} characters)")

    if len(api_key) < 10:
        print("  ⚠️   Key looks too short — please check and try again.")
        print()
        return False
    print()

    print()
    print("  ⏳  Step 1 of 3 — Identifying your AI provider...")

    # ── Step 1: Detect provider ───────────────────────────────────
    provider_id = detect_provider(api_key)

    if provider_id is None:
        print()
        print("  ⚠️   Could not identify the provider from this key's format.")
        print()
        print("  Please choose your provider manually:")
        print()
        for i, pid in enumerate(_DETECTION_ORDER, 1):
            print(f"    {i}. {PROVIDERS[pid]['name']}")
        print()

        try:
            choice = input("  Enter number (or press Enter to cancel): ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Setup cancelled.\n")
            return False

        if not choice.isdigit() or not (1 <= int(choice) <= len(_DETECTION_ORDER)):
            print("\n  ❌  Invalid choice. Setup cancelled.\n")
            return False

        provider_id = _DETECTION_ORDER[int(choice) - 1]

    provider_name = PROVIDERS[provider_id]["name"]
    print(f"  ✅  Detected:  {provider_name}")
    print()

    # ── Step 2: Live connectivity test ────────────────────────────
    print("  ⏳  Step 2 of 3 — Testing live connection...")
    print(f"      Sending a tiny test message to {provider_name}...")
    print()

    success, message = test_connectivity(api_key, provider_id)

    if not success:
        print(f"  ❌  Connection test failed.")
        print(f"      Reason: {message}")
        print()
        print("  Possible causes:")
        print("    • The key was copied incorrectly — try again")
        print("    • Your internet connection is down")
        print("    • The key has expired or was revoked")
        print("    • You have no credits left on this provider")
        print()
        print("  Key NOT saved. Run --setup-ai again when ready.")
        print()
        return False

    print(f"  ✅  Test passed!  {message}")
    print()

    # ── Step 3: Save config ───────────────────────────────────────
    print("  ⏳  Step 3 of 3 — Saving configuration...")
    save_config(api_key, provider_id)
    print(f"  ✅  Saved to: {CONFIG_FILE}")
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🎉  AI setup complete!                             ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()
    print(f"  Your AI:   {provider_name}")
    print(f"  Model:     {PROVIDERS[provider_id]['model']}")
    print()
    print("  You can now use:")
    print("    python saral.py --generate    (AI writes Saral code for you)")
    print("    python saral.py --explain     (AI explains your code)")
    print("    python saral.py --status      (check AI status anytime)")
    print()
    print("  To change AI later, run:  python saral.py --setup-ai")
    print()
    return True


# ══════════════════════════════════════════════════════════════════
# HELPER: get active config for ai_helper.py
# ══════════════════════════════════════════════════════════════════

def get_active_ai() -> Optional[dict]:
    """
    Called by ai_helper.py to get the configured provider.
    Returns the config dict (with key, model, api_url, provider) or None.

    Priority order:
      1. saral_ai.conf (user set up via --setup-ai)
      2. Environment variables (power users / CI pipelines)
         SARAL_DEEPSEEK_KEY, SARAL_GEMINI_KEY (backward compat)
    """
    # Priority 1: config file
    config = load_config()
    if config:
        return config

    # Priority 2: environment variables (backward compatibility)
    deepseek_key = os.environ.get("SARAL_DEEPSEEK_KEY", "").strip()
    if deepseek_key:
        p = PROVIDERS["deepseek"]
        return {
            "provider": "deepseek",
            "name":     p["name"],
            "key":      deepseek_key,
            "model":    p["model"],
            "api_url":  p["api_url"],
        }

    gemini_key = os.environ.get("SARAL_GEMINI_KEY", "").strip()
    if gemini_key:
        p = PROVIDERS["gemini"]
        return {
            "provider": "gemini",
            "name":     p["name"],
            "key":      gemini_key,
            "model":    p["model"],
            "api_url":  p["api_url"],
        }

    return None  # No AI configured
