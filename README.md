To use this software, either download the latest binary here (https://drive.google.com/drive/u/0/folders/1-MGCrMjgRNLFyXr9VE3OKBeq-eFqvU55) or run the source code yourself:

1) Download and run PyCharm (https://www.jetbrains.com/pycharm/)
2) Download this repository (clone or as .zip=>extract)
3) Create a PyCharm project with uChip as the root directory. Set up a Python virtual environment. This project has been confirmed to work with Python 3.9.
5) Install the required packages in the virtual environment: `pip install -r requirements.txt`
6) Run uChip.py in the virtual environment, optionally with a project to open: `python uChip.py my_chip.uchip`

uChip loads its assets using paths relative to the working directory, so run it from the repository root.

## Project files

Chip projects are saved as JSON (`.uchip`), with file paths relative to the project's folder. Rig device
settings are saved to `devices.json` in the working directory.

Projects saved by older versions of uChip (`.ucp`) and old device settings (`devices.pkl`) can be converted once with:

```
python tools/convert_legacy_projects.py old_project.ucp devices.pkl
```

## Architecture

All of uChip's behavior lives in `backend/`, which has no GUI dependencies and could drive a command-line tool:
the chip is plain data (`chip.py`), edits are plain functions, and a `Session` holds an open chip with its
rig and compiled programs. `runner.py` runs programs on a background thread.

`gui/` only displays a session and calls backend functions. It refreshes every widget from the session on
one timer, so it always shows the current state, whether it was changed by the user, a running program or the rig.

Run the backend tests with `python tests/test_backend.py` (or `pytest tests`).

## Project layout

```
uChip.py              Application entry point
setup.py              cx_Freeze build script
backend/              Everything that isn't GUI
  chip.py             Chip data model and edits (add, duplicate, remove, scripts)
  project_file.py     Saving and loading projects as JSON
  rig.py              Serial solenoid-driver devices
  programs.py         Compiling and running program scripts
  session.py          An open chip with its rig and compiled programs
  runner.py           Background thread that runs programs
  ucscript.py         Scripting API exposed to user scripts (`from ucscript import *`)
gui/                  PySide6 front end
  app.py              Startup and the refresh timer
  main_window.py      Menus, toolbar, docks, file actions
  canvas.py           Chip canvas: pan/zoom, selection, moving and resizing
  canvas_elements.py     Widgets for valves, text, images and programs on the canvas
  inspector.py        Side panel for editing the selected element
  parameter_editors.py  Editors for program parameter values
  rig_panel.py        Manual solenoid control and device settings
  script_browser.py   Choosing, importing and relocating scripts
  script_editor.py    Script editing window
  python_editor.py    Code editor widget
tests/                Backend tests
tools/                One-off utilities (legacy project converter)
assets/
  icons/              Application and toolbar icons
  docs/               Scripting reference shown in the script editor
  builtin_scripts/    Scripts bundled with every chip (Pump, ValveSet)
examples/             Example chip projects (.uchip) with their scripts and images
maybe_unused/         Files that appear to be unused, pending review
```
