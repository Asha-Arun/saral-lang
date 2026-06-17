# Saral Lang
## Official Documentation

**Version 1.0.1 | June 2026**

Written by Asha V S  
Irinjalakuda, Thrissur, Kerala, India  
Contact: ashavs@zohomail.in  
GitHub: https://github.com/Asha-Arun/saral-lang.git

**SARAL LANG™**  
Trademark Pending Registration — Class 42, Indian Trade Marks Registry

Apache License 2.0

*सरल — Simple in Sanskrit*

> "Write code the way you think."

---

## A Letter to Every Saral Lang User

My name is Asha V S. I am from Irinjalakuda in Thrissur district, Kerala. I have no computer science background. I am basically an Electrical and Electronics Engineer, entirely from a different background. Presently a simple homemaker. In my college days itself I faced difficulties to understand the programming language. All of them were written by computer programmers for programmers. They were not written for common people. Initially debugging was a nightmare. I dropped learning programming languages completely after my college days.

In 2025-26 something incredible happened in my life. My husband taught me AI, specially Claude AI and Grok (X AI). I realized that I can write any program with AI. But there was one problem. Debugging the program and understanding errors. The old hard wall hit again. Finally I decided, I will write codes in a plain English which anyone can understand. Using my 2015 built old basic laptop and a Rs 2000/- monthly Claude subscription I started building my dream.

When I built Saral Lang, I faced every problem that you might be facing right now. I did not know what a terminal was. I typed '~ollama' instead of 'ollama'. When the screen froze, I did not know why. In this process I also started learning Linux because my laptop's old hardware can't run Windows 11 smoothly.

Every error in this guide is a real error I made. Learning new things were the bonus that I got after started working on Saral Lang. I tried my best to incorporate them in this document.

Saral Lang is designed for the billion people who have ideas but were told "you need to learn to code first." I also incorporated an AI Assistant to help you to generate a Saral Lang Code and also help you in debugging. All you need is a valid API Key.

Every error here is one that actually appeared on screen during testing. Every solution is what actually worked. This guide has no jargon and no assumptions. Every concept is explained using a daily life example you already know. Start from Chapter 0. Read slowly. Try each example.

You cannot break your computer by typing commands. I promise. If I can make a program, you can also make a working one.

*— Asha V S, Creator of Saral Lang*  
*Irinjalakuda, Thrissur, Kerala, India*

---

## Table of Contents

- [Chapter 0 — Before We Start](#chapter-0--before-we-start)
- [Chapter 1 — Installation](#chapter-1--installation)
- [Chapter 2 — Running Saral](#chapter-2--running-saral)
- [Chapter 3 — Core Language Syntax](#chapter-3--core-language-syntax)
- [Chapter 4 — Language Reference](#chapter-4--language-reference)
- [Chapter 5 — AI Features](#chapter-5--ai-features)
- [Chapter 6 — AI Setup](#chapter-6--ai-setup)
- [Chapter 7 — Common Errors and Fixes](#chapter-7--common-errors-and-fixes)
- [Chapter 8 — Checking System Health](#chapter-8--checking-system-health)
- [Chapter 9 — Uninstallation](#chapter-9--uninstallation)
- [Chapter 10 — Complete Reset Procedure](#chapter-10--complete-reset-procedure)
- [Chapter G — Glossary](#chapter-g--glossary)
- [Quick Reference Card](#quick-reference-card)

---

## Chapter 0 — Before We Start

This chapter explains your computer in plain English. No jargon. No assumptions. Understanding your computer helps you fix problems faster.

### What is Linux?

Linux is a free, open-source operating system. An operating system is the main software that runs your computer — like Windows or macOS, but free. Ubuntu and Linux Mint are popular versions of Linux. Saral Lang runs on Linux.

> **Tip:** Linux Mint is the beginner-friendly version of Linux. Ubuntu is also very popular. Both work perfectly with Saral Lang.

### What is the Terminal?

The terminal is a text window where you give instructions to your computer by typing words. Instead of clicking buttons, you type. It looks plain but it is extremely powerful.

Think of it this way: Typing in the terminal is like talking to a very obedient shop assistant. If you say one thing, they respond. You say another thing, they respond again. Each line is one instruction.

#### How to Open the Terminal

- Press **Ctrl + Alt + T** on the keyboard
- Or: Right-click on the empty Desktop → click **Open Terminal Here**
- Or: Click Start Menu → type **terminal** → press Enter

> **Note:** The text showing the terminal is ready looks like: `asha@laptop:~$` — This is called the prompt. NEVER type the `$` sign yourself. Type what comes after the `$`.

### What is RAM?

RAM (Random Access Memory) is your computer's short-term working memory. It holds everything that is currently running — the desktop, Firefox, the terminal, and your Saral program. When RAM gets full, everything freezes.

Think of it this way: RAM is like your kitchen table. When you cook, you keep all the ingredients on the table. If you put too many things on the table, there is no space to work. More RAM = can run more programs at once.

> **Tip:** Before using Saral AI features (cloud AI), close Firefox and file manager windows. This frees memory for smoother operation.

### What is a Command?

A command is an instruction you type in the terminal. For example: `ls`, `cd`, `saral` are commands. The computer runs the command and shows the result.

### You Cannot Break Your Computer

This is the most important thing to know. Typing commands in the terminal is safe. If you type a wrong command, the computer shows an error message — and nothing else happens. It will not delete your files. It will not crash.

The only command that can delete files is `rm`. We tell you when it is safe to use it. Until then, type freely without any fear.

---

## Chapter 1 — Installation

This chapter covers downloading, installing, verifying, and updating Saral Lang step by step.

### System Requirements

| Component | Requirement |
|---|---|
| Operating System | Latest Ubuntu or Linux Mint (recommended) |
| Python | 3.8 or above (3.11+ recommended) |
| RAM | 512 MB minimum \| 2 GB for AI features |
| Storage | 50 MB (core) \| 100 MB (with AI) |
| Internet | Required for cloud AI features only |

### Method 1 — Quick Install (Recommended)

This is the easiest method. It downloads the latest release directly from GitHub:

```bash
# Step 1: Open terminal and go to Downloads folder
cd ~/Downloads

# Step 2: Clone the repository
git clone https://github.com/saral-lang/saral-lang.git

# Step 3: Go into the folder
cd saral-lang

# Step 4: Run the installer
bash install/install_linux.sh

# Step 5: Reload terminal settings
source ~/.bashrc

# Step 6: Verify
saral --version
```

### Method 2 — Install from Downloaded ZIP

If you downloaded the ZIP file from GitHub manually:

```bash
# Step 1: Go to Downloads folder
cd ~/Downloads

# Step 2: Extract the ZIP
unzip saral-lang-main.zip

# Step 3: Go into the extracted folder
cd saral-lang-main

# Step 4: Run the installer
bash install/install_linux.sh

# Step 5: Reload terminal
source ~/.bashrc
```

> **Important:** When asked for your password, type your Linux login password. Nothing appears on screen while typing — no stars, no dots. This is normal. The computer IS receiving your password. Press Enter when done.

### Verify Installation

After installation, confirm Saral Lang is working:

```bash
saral --version
# Expected output:
# SARAL v1.0.1 First Public Release

which saral
# Expected output:
# /usr/local/bin/saral

python3 --version
# Expected output:
# Python 3.10.12 (any version 3.8 or above is fine)
```

### What Gets Installed

| Location | Contents |
|---|---|
| `/usr/local/bin/saral` | The 'saral' command you type in terminal |
| `~/.saral/` | Saral core files and example programs |
| `~/.saral/examples/` | Example .saral programs ready to run |
| `~/.bashrc` | SARAL_DIR path — updated by installer |
| `~/Desktop/Saral.desktop` | Desktop shortcut for interactive mode |

### Updating Saral Lang

```bash
cd ~/saral-lang
git pull
bash install/install_linux.sh
source ~/.bashrc
```

---

## Chapter 2 — Running Saral

There are four ways to use Saral Lang. Each is designed for a different purpose.

### All Saral Commands

| Command | What it does |
|---|---|
| `saral myfile.saral` | Run a saved Saral programme |
| `saral --interactive` | Start interactive mode — type code line by line |
| `saral --generate` | AI writes Saral code from your English description |
| `saral --debug myfile.saral` | Debug mode — run one line at a time |
| `saral --version` | Display the installed Saral Lang version |
| `saral --status` | Check which AI is configured and working |
| `saral --setup-ai` | Interactive wizard to connect your AI provider |
| `saral --explain myfile.saral` | AI explains what the code does in plain English |
| `saral --check myfile.saral` | Check your programme for errors without running |
| `saral --memory` | Show what AI remembers in this session |

### Method 1 — Run a Saved Programme

```bash
saral myfile.saral
```

Think of it this way: Running a .saral file is like pressing Play on a recorded song. The song (programme) is saved as a file. You press Play (type saral filename.saral) and it runs.

### Method 2 — Interactive Mode

```bash
saral --interactive
# Now type code line by line:
saral 1> store 10 in price
saral 2> show price
# Output: 10
saral 3> quit
```

Think of it this way: Interactive mode is like a maths tutor sitting next to you. You type one line, they respond. Each line is answered immediately.

### Method 3 — AI Code Generator

```bash
saral --generate
# Then describe what you want:
> create a bakery calculator
# Saral writes the code for you
# Then type: run / save / explain / new / quit
```

Think of it this way: `saral --generate` is like dictating a letter to a secretary. You describe what you want in plain English, and the AI types it out in Saral Lang for you.

### Method 4 — Debug Mode

```bash
saral --debug myprogram.saral
debug> next   # run one line
debug> vars   # see all variable values
debug> fix    # AI explains what is wrong
debug> quit   # exit debugger
```

Think of it this way: The debugger is like watching a cooking video frame by frame. Instead of the recipe running all at once, you pause at each step, check the ingredients and make sure everything looks right.

### Running the Example Programmes

Example programmes are installed in `~/.saral/examples/` — ready to run:

```bash
ls ~/.saral/examples/
saral ~/.saral/examples/01_bakery_sales.saral
saral ~/.saral/examples/engineering_math.saral
```

> **Tip:** After running an example, you can ask AI about it: type `saral --explain` and the AI knows what programme you were running.

---

## Chapter 3 — Core Language Syntax

Saral Lang reads like plain English. This chapter covers the fundamental building blocks of every Saral programme. Language rules: case insensitive (STORE, Store, store all work the same). Indentation is optional. Comments start with `#` — the computer ignores the rest of the line.

### Variables — Storing Values

```
store 10 in price
store "Hello World" in message
store "yes" in running

show price            # displays the value
show "Price is {price}"   # text with variable inside {}
show "Hello {name}, price is ₹{price}"
```

### Math Operators

Math operators: `+` `−` `*` `/` `^` (power) `%` (modulo)

```
store price * 2 in double_price
store sales * 0.05 in tax
store price * quantity in total
increase price by 5    # same as: store price + 5 in price
decrease price by 2

# Advanced math
store sqrt of 144 in r        # → 12
store square of 4 in sq       # → 16
store cube of 3 in cu         # → 27
store absolute of -5 in a     # → 5
store round of 3.14159 to 2 places in pi  # → 3.14
store floor of 4.9 in f       # → 4
store ceiling of 4.1 in c     # → 5
store log of 1000 in l        # → 3.0
store sin of 90 in s          # → 1.0 (degrees)
store cos of 0 in c           # → 1.0
store random of 1 to 100 in n # random number
```

### Conditions

```
if price > 100
    show "Expensive"
otherwise if price > 50
    show "Medium price"
otherwise
    show "Cheap"
done

# In Saral: use = for equality check inside if conditions
if name = "Asha"
    show "Hello Asha!"
done

if price > 0 and quantity > 0    # both conditions must be true
    store price * quantity in total
done
```

### Loops

```
# Count loop
count from 1 to 10
    show count
done

# Repeat a fixed number of times
repeat 5 times
    show "Hello"
done

# While loop
store "yes" in running
while running = "yes"
    ask "Continue? " and store in running
done

# For each item in a list
for each item in my_list
    show item
done

stop    # exit the loop immediately
skip    # skip to next iteration
```

### Functions

```
# Define a function
define add with a and b
    store a + b in result
    return result
done

# Call a function
store call add with 3 and 4 in result
show result   # → 7

call greet with "Asha"   # → Hello Asha!

# Function with no arguments
define myfunction
    show "Running!"
done
call myfunction
```

### Output Formatting

```
show "Hello"              # normal output
show "Important" in bold
show "Warning!" in yellow
show "Error!" in red
show "Success!" in green
show "Invalid email" in red
show blank                # blank line
```

### Error Handling

```
try
    store 10 / 0 in result
catch
    show "Error: division by zero" in red
done

raise error "Value must be positive"
```

---

## Chapter 4 — Language Reference

### Lists

```
make list called fruits
add "apple" to fruits
add "banana" to fruits
add "mango" to fruits

show item 2 of fruits      # 1-based index → banana
show first item of fruits
show last item of fruits
show length of fruits      # → 3

remove "banana" from fruits
reverse fruits
sort fruits                # alphabetical

show summary for each item in my_list
```

### Strings

```
store length of name in n
store uppercase of name in big
store lowercase of name in small
store trimmed name in clean        # removes spaces
store name reversed in backwards
store parts joined by " " in sentence
store name split by "," in parts
store name replace "old" with "new" in result

check that name is not empty and store in filled
check that code is a number and store in is_num
check that email is valid email and store in ok
check that age is between 1 and 120 and store in valid
```

### Date and Time

```
store today in date           # e.g. 17-06-2026
store now in timestamp        # current date and time
store current time in tm
store current day in dy
store current month in mo
store current year in yr
store now in dt               # e.g. 17-06-2026 14:30:00
```

### Files

```
read file "notes.txt" and store in content
write content to file "output.txt"
append "new line" to file "log.txt"
read lines from "data.txt" and store in lines
delete file "temp.txt"
```

### CSV and JSON

```
read csv "sales.csv" and store in data
write data to csv "updated.csv"
store column "price" of data in prices

read json "config.json" and store in cfg
write cfg to json "output.json"
fetch json "https://api.example.com/json" and store in data
```

### Web Requests

```
fetch "https://api.example.com/data" and store in response
fetch json "https://api.example.com/json" and store in data
```

### Input from User

```
ask "What is your name? " and store in name
ask number "Enter price: " and store in price
ask "Your question: " and store in question
```

---

## Chapter 5 — AI Features

AI is optional in Saral Lang. If you have no API key, Saral Lang still runs all programmes and interactive mode perfectly. AI features (generate, explain) will show: 'AI not configured — run saral --setup-ai'

### AI Remembers Within a Session

Think of it this way: Within one session, the AI is like a helpful assistant who was present for your entire conversation. If you say 'add a save button to it', they know exactly what 'it' means because they were listening from the beginning.

> **Good to know:** Saral always has a built-in pattern-matching fallback that requires no internet. Your programmes run, interactive mode works, and basic fixes are suggested even with no AI provider configured.

### AI Commands from Terminal

| Command | What it does |
|---|---|
| `saral --generate` | AI writes Saral code from your English description |
| `saral --explain myfile.saral` | AI explains what the code does in plain English |
| `saral --status` | Check which AI is configured and working |
| `saral --memory` | Show what AI remembers in this session |
| `ask ai "question"` | Ask AI any question from inside a programme |

### AI Inside Your Programme

Saral Lang lets you call AI directly from inside your .saral programmes:

```
ask ai "What is the capital of Kerala?" and store in answer
show answer

# AI with a calculated value
ask ai "Is this tax rate normal in India?" using tax and store in advice
show advice

# AI processes a variable
ask ai "Summarize this report" using report and store in summary
show summary
```

### Supported AI Providers

| Provider | Key format — starts with |
|---|---|
| Anthropic Claude | `sk-ant-...` |
| OpenAI / GPT-4o | `sk-proj-...` or `sk-...` |
| Google Gemini | `AIza...` |
| Groq | `gsk_...` |
| xAI Grok | `xai-...` |
| Mistral | console.mistral.ai |
| Cohere | dashboard.cohere.com |
| DeepSeek | platform.deepseek.com |

---

## Chapter 6 — AI Setup

### Setup AI in One Command

Saral Lang v1.0.1 includes an interactive setup wizard. Run it once and your AI is configured permanently:

```bash
saral --setup-ai
# Output:
# → Saral Lang AI Setup Wizard
# → Paste your API key (any supported provider):
# (paste your key — it auto-detects which provider)
# → Detected: Anthropic Claude
# → Testing connection...
# → AI connected successfully!
# → You can now use: saral --generate, saral --explain, ask ai
```

> **Note:** The wizard auto-detects which provider your key belongs to by its prefix. You do not need to specify the provider — just paste the key.

### Setting AI Keys Manually

```bash
# Open .bashrc in a text editor:
nano ~/.bashrc

# Add one of these lines at the bottom (use your own key):
export ANTHROPIC_API_KEY='sk-ant-your-key-here'   # Anthropic
export OPENAI_API_KEY='sk-proj-your-key-here'      # OpenAI
export GOOGLE_AI_KEY='AIza-your-key-here'          # Gemini
export GROQ_API_KEY='gsk_your-key-here'            # Groq
export XAI_API_KEY='xai-your-key-here'             # xAI Grok

# Save with Ctrl+O, Enter, Ctrl+X
# Then reload:
source ~/.bashrc
```

### Check AI Status

```bash
saral --status
# Shows:
# AI provider: Anthropic Claude
# Model: claude-3-haiku
# Status: Connected
# → Fallback: Pattern matching (always available)
```

### AI Fallback — No Internet Needed for Core

Saral core syntax, math, conditions, loops, and functions require no internet connection. Your programmes run even without any AI provider configured.

### Remove AI Keys

```bash
nano ~/.bashrc
# Delete the lines that say: export SARAL_DIR=...
# Also delete the API key lines
# Save: Ctrl+O, Enter, Ctrl+X
```

---

## Chapter 7 — Common Errors and Fixes

Every programmer — beginner and expert — sees error messages every day. An error message is not a failure. It is the computer telling you exactly what is wrong and where.

Think of it this way: An error message is like a doctor's diagnosis. It sounds alarming at first, but it is actually the most helpful thing the computer can do. 'syntax error on line 22' is like 'You have a vitamin D deficiency' — now you know exactly what to fix.

### How to Read an Error — 4 Steps

| Step | What to do |
|---|---|
| 1. Read the line number | The error says which line is wrong — that is where to look |
| 2. Read the message | Read the 'Did you mean' suggestion if shown |
| 3. Open the file | `nano myfile.saral` → `Ctrl+_` → type the line number |
| 4. Fix and run | Fix the issue and run again: `saral myfile.saral` |

> **Tip:** Arrows point at the exact problem in the line. Read error messages from top to bottom. The most useful information is usually in the LAST line. Cannot understand the error? Type: `saral --debug myfile.saral` → then type `fix` at the `debug>` prompt. AI explains in plain English.

### Anatomy of a Saral Error

```
myprogram.saral:22:9
↑  ↑  ↑
file line char

22 | b != 0
   | ^^^^^^ ← exact location shown
```

### Error Code Reference

| Error Code | What it means and how to fix |
|---|---|
| E001: I don't understand | Unknown keyword or typo. Check spelling. Read the 'Did you mean' suggestion |
| E002: Variable used before stored | Used a variable before giving it a value. Add: `store 0 in varname` before the line |
| E003: Block not closed | Missing 'done' at the end of if/loop/function. Fix: `if b not = 0` → `done` |
| E004: File not found | Wrong filename or not in correct folder. Check: `ls` and verify the path |
| E005: Permission denied | Add `sudo` before the command: `sudo cp` |
| E009: Type mismatch | Trying to add text to a number. Strings cannot be used as numbers |
| E011: No space left | Disk full. Check: `df -h` and delete old files |
| E012: Dictionary key not found | Getting a key that does not exist in a dictionary |
| E013: Invalid number | Using a string as number on non-numeric text |
| E014: Function not defined | Calling a function before defining it. Define the function first |
| E015: List index out of range | Accessing item 5 when list only has 3 items |
| E020: Division by zero | Dividing by a variable that is 0. Check: `if b not = 0` before dividing |

### How to Ask for Help Effectively

Asking for help is like calling a plumber when your pipe is leaking. A good plumber needs to know: which pipe, where it is leaking, what you already tried. Vague descriptions waste time. Specific descriptions get solutions fast.

Include in your help request:

- Exactly what you typed — copy the exact command
- Exactly what appeared — take a photo of the terminal screen
- What you were trying to do: 'I was running saral --generate'
- What you already tried: 'I closed Firefox and tried again'

Contact: ashavs@zohomail.in | GitHub Issues: github.com/saral-lang/saral-lang/issues

---

## Chapter 8 — Checking System Health

### Check RAM

```bash
free -h
# Output:
# Mem: 3.8Gi  2.1Gi  0.4Gi  1.3Gi
#      total  used   free   available

# If available RAM below 1 GB, close Firefox and other windows
```

### Check Disk Space

```bash
df -h
# Output:
# /dev/sda1  50G  23G  25G  48%
# If Use% is above 90%, delete old files
```

### Check Internet Connection

```bash
ping -c 3 google.com
# → 3 packets transmitted, 3 received, 0% packet loss = connected
# → Temporary failure in name resolution = no internet
```

### Check Saral Status

```bash
saral --version
which saral
saral --status
```

### Things That Always Work

- Restart the laptop — fixes 80% of strange problems
- Close terminal and open a fresh one
- Run: `source ~/.bashrc` (if 'saral: command not found' appears)
- Try: `. ~/.bashrc` (dot space tilde/.bashrc)

> **When You Are Completely Stuck:** The reset procedure is like restarting a stuck ceiling fan. First turn it off (pkill). Wait a few seconds. Turn it on again. If the fan still does not start, check if there is a power cut (free -h for RAM, ping for internet). If everything fails, switch off the main switch and turn it back on (restart the laptop).

---

## Chapter 9 — Uninstallation

The uninstaller does NOT delete your .saral programmes or any files you created. Only the Saral Lang engine is removed.

### Quick Uninstall

```bash
cd ~/saral-lang
bash install/uninstall_linux.sh
```

### What the Uninstaller Removes

- `/usr/local/bin/saral` — the saral command
- `~/.saral/` — the entire Saral core files folder
- `~/Desktop/Saral.desktop` — desktop shortcut
- The SARAL_DIR lines added during install from `~/.bashrc`

### Manual Uninstall (if script is unavailable)

```bash
# Step 1: Remove the saral command
sudo rm /usr/local/bin/saral

# Step 2: Remove the Saral files
rm -rf ~/.saral

# Step 3: Remove the desktop shortcut
rm ~/Desktop/Saral.desktop

# Step 4: Remove PATH entry from .bashrc
nano ~/.bashrc
# Delete the lines that say: export SARAL_DIR=...
# Save: Ctrl+O, Enter, Ctrl+X

# Step 5: Reload terminal
source ~/.bashrc

# Verify removed:
which saral
# → (nothing — Saral is removed)
```

### Reinstalling After Uninstall

To reinstall Saral Lang after uninstalling, simply run the installer again from a fresh download or the existing folder:

```bash
bash install/install_linux.sh
```

---

## Chapter 10 — Complete Reset Procedure

Use this when Saral is behaving strangely and nothing else works.

```bash
# Step 1: Check RAM
free -h
# If available RAM below 1 GB, close Firefox and other windows

# Step 2: Check internet
ping -c 2 google.com

# Step 3: Verify Saral is installed
saral --version

# Step 4: Reload your terminal settings
source ~/.bashrc

# Step 5: Check AI status
saral --status

# If still broken — re-run the installer:
cd ~/saral-lang
bash install/install_linux.sh
source ~/.bashrc
saral --version
```

---

## Chapter G — Glossary

45 technical words explained in plain English. Every technical word used in this documentation.

| Term | Meaning |
|---|---|
| alphanumeric | Letters and numbers combined — like a password "asha123" |
| API key | A password-like code that lets Saral Lang access a cloud AI service. Looks like: sk-ant-xxxxxxxx or AIza... |
| apt | The software installer for Ubuntu/Linux Mint. Like a Supplyco for software. Used to install Python libraries |
| bash | The language the terminal uses to interpret your commands |
| CPU | Central Processing Unit — the brain of the computer |
| command | An instruction you type in the terminal. 'ls', 'cd', 'saral' are commands |
| curl | A tool for downloading files or sending web requests from the terminal |
| debugger | A tool that runs a programme one line at a time. Type commands at the debug> prompt |
| df | Disk Free — shows how much disk space is used and available (df -h) |
| directory | Another word for folder |
| extension | The part of a filename after the dot. '.saral' '.py' '.jpg' are extensions |
| flag | An option added to a command. In 'saral --version', '--version' is a flag |
| free | Shows RAM usage (free -h) |
| function | A reusable block of code you define once and call whenever needed |
| hidden file | A file or folder starting with a dot (.) — not shown by default. ~/.saral is a hidden folder |
| home folder | Your personal folder: /home/yourname/ — also written as ~ |
| interpreter | The programme that reads and runs your Saral code. It translates Saral into Python and runs it |
| Linux | A free, open-source operating system used by programmers, scientists, and governments |
| Linux Mint | A beginner-friendly version of Linux based on Ubuntu |
| model | The AI brain. Different providers use different models (Claude, GPT-4o, Gemini) |
| module | A Python file that adds extra features. Saral uses Python modules internally |
| nano | A simple text editor in the terminal. Use Ctrl+O to save, Ctrl+X to exit |
| operating system | The main software that runs your computer. Windows, Linux, and macOS are operating systems |
| package | A piece of software ready to install with apt |
| path | The full address of a file: /home/asha/Desktop/myfile.saral |
| permissions | Rules about who can read, write, or run a file |
| ping | A command to test internet connectivity. `ping -c 3 google.com` |
| pip | Python's software installer — used to install Python libraries |
| pkill | A command to stop a running programme by name |
| process | A programme that is currently running on the computer |
| prompt | The text showing the terminal is ready: asha@laptop:~$ |
| RAM | Random Access Memory — the computer's short-term working memory. Holds everything running |
| root | Also: the system administrator user. Also: the top-most folder of the computer (/) |
| service | A tool for managing background services. A programme that runs in the background |
| source | A command to reload a file. `source ~/.bashrc` reloads your terminal settings |
| sudo | Super User DO — gives temporary admin permissions for one command |
| syntax | Rules about how to write code. Like grammar rules for a programming language |
| systemctl | A tool for managing background services on Ubuntu/Linux Mint |
| terminal | The text window where you type commands to control your computer |
| tilde (~) | The ~ symbol — always means your home folder (/home/yourname/) |
| Ubuntu | A popular Linux version. Very beginner-friendly |
| unzip | A command to extract files from a .zip archive |
| variable | In Saral: a named box that holds a value. 'store 10 in price' — price is the variable |
| Windows | Microsoft's operating system — costs money, built on a different foundation than Linux |
| ZIP | A compressed file containing multiple files. Ends in .zip |

---

## Quick Reference Card

*Print this page and keep it next to your laptop. Every command on one printable page.*

### Saral Commands

```bash
saral myfile.saral          # Run programme
saral --interactive         # Interactive mode
saral --generate            # AI writes code
saral --debug myfile.saral  # Debug mode
saral --explain myfile.saral # AI explains code
saral --version             # Check version
saral --status              # Check AI status
saral --setup-ai            # Connect AI
saral --check myfile.saral  # Check for errors
saral --memory              # Show AI memory
```

### Keyboard Shortcuts (Terminal)

| Shortcut | What it does |
|---|---|
| Ctrl + C | Stop whatever is running immediately |
| Ctrl + L | Clear the screen |
| Ctrl + Shift + C | COPY selected text FROM terminal |
| Ctrl + Shift + V | PASTE text INTO terminal |
| Ctrl + Shift + T | Open a new terminal tab |
| Up Arrow | Repeat previous command |
| Tab | Auto-complete a filename |

### Core Language — All on One Page

```
store 10 in price               # Variable
show "Price is {price}"         # Output
if price > 100 ... done         # Condition
count from 1 to 10 ... done     # Loop
repeat 5 times ... done         # Loop
while x > 0 ... done            # Loop
for each item in list ... done  # Loop
define func with arg ... done   # Function
call func with value            # Call function
add "item" to mylist            # List
ask "Question" and store in x   # Input
read file "f.txt" and store     # File
ask ai "question" and store     # AI
try ... catch ... done          # Error handling
```

### Linux Commands

```bash
pwd                     # Show current folder location
ls                      # See files in current folder
ls -la                  # See ALL files including hidden
cd folder               # Go into folder
cd ..                   # Go up one folder
cd ~                    # Go to home folder
nano file               # Edit a file
free -h                 # Check RAM available
df -h                   # Check disk space
ping -c 3 google.com    # Check internet
sudo apt install pkg    # Install software
```

---

*Saral Lang v1.0.1 — June 2026 — Apache License 2.0*

*SARAL LANG™ — Trademark Pending Registration, Class 42, Indian Trade Marks Registry*

*Developed by Asha V S — Irinjalakuda, Thrissur, Kerala, India*

*Contact: ashavs@zohomail.in | GitHub: github.com/saral-lang/saral-lang*
