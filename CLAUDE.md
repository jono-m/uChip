## Guidelines for working on this project with me.

- Work in this project's main directory and on the current checked-out branch. You do not need to use worktrees or a separate branch as you work alongside me.
- Do not change branches, make commits, push changes, or otherwise change the repository git state unless I explicity request it.
- I may edit files between changes (and these might not be committed yet). You can look at the present version of the file, or look at git diff or git status at any time to make sure you are working with the most updated version.
- You can always prompt me in the middle of your work to ask for advice on conflicts or architecture/other decisions.
- I trust your work, but prefer to work closely with you and have you run design/implementation decisions or other questions by me as you see fit.
- I also want you to keep any running notes/documentation on the code architecture saved in a directory for the project (e.g. .claude/notes) which you can reference across clean runs so you don't have to read through all new code. you can also document when the last code update was done for that note, so that you know when you do need to reread a file (e.g. if git status or git diff has changed or over a commit.)

## Session notes (for Claude)
- At the start of a session, read `.claude/notes/architecture.md` instead of rereading the codebase. Then check `git log -1 --oneline` and `git status --short` against its "Last verified" line, and reread only the files that changed since.
- After changing code (or noticing changes made by me), update the affected sections of the notes and the "Last verified" line. Keep the notes short and at the level of modules, objects and how they connect.
- Run the app with `.venv/Scripts/python.exe uChip.py` and the tests with `.venv/Scripts/python.exe tests/test_backend.py`, both from the repo root.

Now some code guidelines:
- I prefer composition over inheritance, and don't like when things get subclassed unless needed by the library (e.g. Qt for event callbacks)
- I prefer objects to be minimally coupled. Any coupling between objects that isn't strictly defined by the objects themselves (e.g. if object A needs to hold a reference to object B then that is fine) but if it is a "functional" reference I would like that to be connected only in a module-level method (e.g. if object A can be updated based on some settings in object B, that should NOT be a member function of object A, as it can exist independent of object B).

How this is applied in practice:
- Objects are plain classes (usually `@dataclass(eq=False)`) holding data.
- A function is an **instance method** when it only uses the object's own fields, or objects it holds a reference to *by data definition* (e.g. `Session` holds a `Chip` and a `Rig`, so `session.open_chip(path)` is a method; `Rig` holds its `Device`s, so `rig.blink(device)` is a method; `Runner` holds a `Session`, so `runner.tick()` can use `self.session.chip`).
- A function is **module-level** when it connects objects that are not dependent on each other by data definition (e.g. `compile_program(program, chip, rig, ...)`, or a GUI `refresh_valve(valve, parts, session, runner)` that syncs a model element to its widgets).
- Constructing an object: if it only assigns field values, use the class constructor directly. If construction depends on other objects or involves more logic (building widgets, wiring signals, loading files), write a module-level factory function that describes *how* it is created (e.g. `new_session(rig)`, `load_rig(path)`, `build_canvas(session, runner)`), rather than a complex `__init__`.
- Functions that aren't about any one object (type helpers, JSON helpers, serialization in `project_file`) stay module-level.
- Qt subclasses exist only where Qt requires them (event overrides); they delegate to the object's methods or module functions.
