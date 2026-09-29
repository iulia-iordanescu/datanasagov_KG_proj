# Setting up a local virtual environment

These instructions create an isolated Python environment for every script in this repo. The environment is a `.myvenv` folder in the repo root. It holds its own Python and packages, so nothing you install here affects the rest of your machine.

The commands are for Windows PowerShell. Where Git Bash differs, the Bash version is shown too.

## Quick version

If you've done this before, these are all the commands, run from the repo root. Each part below explains them.

```powershell
py -3.14 -m venv .myvenv
.\.myvenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install requests python-dotenv
python -m pip freeze | Out-File -Encoding utf8 requirements.txt
```

Then add `.myvenv/` to `.gitignore` (part 2), create the `.env` file (part 6) and run the checks (part 7).

## What the repo needs

| Need | Detail |
|---|---|
| Python | **3.14**, the newest stable release. It's already installed on this machine |
| Packages | `requests`, used by every script that calls the data.nasa.gov API or Ask Sage, and `python-dotenv`, used by `common/llm.py` to read your Ask Sage key from `.env`. Everything else comes with Python |
| Credentials | A `.env` file with your Ask Sage email and API key. Only the scripts that call a model need it |

## Part 1: Check that Python 3.14 is installed

```powershell
py -0
```

This lists the Python versions on the machine. Look for a line containing `3.14`.

If it's missing, download the latest 3.14 installer from [python.org](https://www.python.org/downloads/windows/), run it, and keep the **py launcher** option ticked.

Why 3.14: it's the newest stable version, so it gets bug and security fixes the longest. Don't use a 3.15 pre-release (alpha, beta or release candidate).

## Part 2: Create the environment

```powershell
cd C:\repos\datanasagov_KG_proj
py -3.14 -m venv .myvenv
```

This creates the `.myvenv` folder in the repo root. You only do this once.

Then keep the folder out of Git: open `.gitignore` in the repo root and add this line at the end.

```
.myvenv/
```

Without it, Git lists the thousands of files inside `.myvenv` as new files, and they could be committed by accident.

Don't rename the folder later. A virtual environment records its own location, so a renamed one stops working. To use a different name, delete the folder and create it again.

## Part 3: Activate the environment

PowerShell:

```powershell
.\.myvenv\Scripts\Activate.ps1
```

Git Bash:

```bash
source .myvenv/Scripts/activate
```

Your prompt now starts with `(.myvenv)`. That means `python` and `pip` refer to the environment instead of the system Python.

Activation lasts only as long as that terminal window, so repeat this part each time you open a new terminal.

**If PowerShell says "running scripts is disabled on this system":** run this once to allow local scripts for your Windows account, then run the activate command again.

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Part 4: Install the packages

With the environment active:

```powershell
python -m pip install --upgrade pip
python -m pip install requests python-dotenv
```

The first line updates pip, Python's package installer. The second installs the two packages the repo needs.

## Part 5: Save the package list to `requirements.txt`

This records the exact package versions so the environment can be rebuilt the same way later.

PowerShell:

```powershell
python -m pip freeze | Out-File -Encoding utf8 requirements.txt
```

Git Bash:

```bash
python -m pip freeze > requirements.txt
```

In Windows PowerShell, use `Out-File -Encoding utf8` rather than `>`. A plain `>` can save the file as UTF-16, which Git treats as a binary file.

Commit `requirements.txt`. From then on, anyone setting up the repo, including you on another machine, replaces the second command in part 4 with:

```powershell
python -m pip install -r requirements.txt
```

## Part 6: Add your Ask Sage credentials

Skip this part if you only need the pipeline steps that call no model (010 to 030) and the audit tool.

Create a file named `.env` in the repo root, containing these two lines with your own values:

```
ASKSAGE_EMAIL=you@example.com
ASKSAGE_API_KEY=your-key-here
```

Don't add quotes or spaces around the `=`.

`.gitignore` excludes `.env`, so your key stays on your machine. The code that calls the model (`common/llm.py`) searches for `.env` starting in its own folder and then in each folder above it, so it finds it in the repo root.

The pipeline steps that call the model need the file: steps 040 (`040_induce_schema.py`), 050 (`050_annotate.py`) and 060 (`060_extract.py`). Ask Sage only answers from NASA's network, so these steps run on a NASA laptop (see `docs/running_on_nasa_laptop.md`).

## Part 7: Check the setup

With the environment active:

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -c "import requests, dotenv; print('packages OK')"
```

You should see:

1. `Python 3.14.x`
2. A path ending in `datanasagov_KG_proj\.myvenv\Scripts\python.exe`
3. `packages OK`

If the path points somewhere else, the environment isn't active. Go back to part 3.

## Part 8: Run the scripts

The usage examples in the scripts and in `instructions/` use `py`, for example `py audit.py <key>`. While the environment is active, `py` without a version number uses the environment's Python, so you can copy those examples as they are. `python` works the same way.

**Pipeline steps in the repo root.** These find their files relative to the repo, so the folder you run them from doesn't matter. Running them from the repo root is simplest:

```powershell
py 010_harvest.py --help
py 010_harvest.py --max_records 2000
py audit.py <record id>
```

Each step's guide in `instructions/` says how to run it. `docs/running_on_nasa_laptop.md` gives the order to run them in.

**Scripts in `to_be_reshaped/`** are the earlier scripts, kept for reference while the pipeline steps replace them. They aren't run.

## Day-to-day use

| Task | Command |
|---|---|
| Start work in a new terminal | `.\.myvenv\Scripts\Activate.ps1` from the repo root |
| Leave the environment | `deactivate` |
| Add a package | `python -m pip install <package>`, then repeat part 5 and commit `requirements.txt` |

To rebuild the environment from scratch, for example after upgrading Python:

```powershell
deactivate
Remove-Item -Recurse -Force .myvenv
py -3.14 -m venv .myvenv
.\.myvenv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If the environment isn't active, `deactivate` gives an error. That's harmless, so carry on with the next command.

## Using the environment in VS Code

This needs the Python extension from Microsoft.

1. Open the Command Palette with Ctrl+Shift+P.
2. Choose **Python: Select Interpreter**.
3. Pick the entry that shows `.myvenv`, or browse to `.myvenv\Scripts\python.exe`.

New VS Code terminals then activate the environment automatically, and the Run button uses it.
