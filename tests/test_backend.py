"""Backend tests. These drive uChip without any GUI, the way a command-line tool would.

Run from the repository root with `python -m pytest tests` or `python tests/test_backend.py`.
"""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend import project_file  # noqa: E402
from backend.chip import Chip, Script, Valve  # noqa: E402
from backend.programs import MessageKind  # noqa: E402
from backend.runner import Runner  # noqa: E402
from backend.session import new_session  # noqa: E402

EXAMPLE = Path("examples/PluriDrop.uchip")


def test_open_compile_and_round_trip():
    session = new_session()
    session.open_chip(EXAMPLE)
    assert len(session.chip.valves) == 20 and len(session.chip.programs) == 9
    assert session.chip.images[0].path.exists()
    runner = Runner(session)
    runner.compile_all()
    for compiled in runner.compiled.values():
        assert [m.text for m in compiled.messages if m.kind == MessageKind.COMPILE_ERROR] == []
    assert not session.is_modified()

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "copy.uchip"
        session.save_chip(path)
        reloaded = project_file.load_chip(path)
    assert project_file.chip_to_json(reloaded, EXAMPLE.parent) == project_file.chip_to_json(session.chip,
                                                                                            EXAMPLE.parent)


def test_valve_parameter_references_survive_saving():
    chip = Chip()
    valve = chip.add_valve()
    program = chip.add_program(Script(builtin="Pump"))
    program.parameter_values = {"pumpValveA": valve, "list": [valve, valve]}
    reloaded = project_file.chip_from_json(project_file.chip_to_json(chip, Path.cwd()), Path.cwd())
    values = reloaded.programs[0].parameter_values
    assert values["pumpValveA"] is reloaded.valves[0] and values["list"] == [reloaded.valves[0]] * 2


def test_script_kinds_survive_saving():
    chip = Chip()
    user_script = chip.import_script(Path("examples/Priming.py"))
    chip.add_program(user_script)
    chip.add_program(Script(builtin="Pump"))
    data = project_file.chip_to_json(chip, Path.cwd())
    assert data["scripts"] == [{"path": "examples/Priming.py"}]
    assert [p["script"] for p in data["programs"]] == [{"path": "examples/Priming.py"}, {"builtin": "Pump"}]
    reloaded = project_file.chip_from_json(data, Path.cwd())
    assert not reloaded.programs[0].script.is_builtin() and reloaded.programs[1].script.is_builtin()


def test_modified_tracking():
    session = new_session()
    assert not session.is_modified()
    session.chip.add_valve()
    assert session.is_modified()


def test_duplicate_valve_names():
    chip = Chip()
    v = chip.add_valve()
    assert (v.name, v.solenoid) == ("Valve 0", 0)
    copy = chip.duplicate_element(v, (50, 0))
    assert (copy.name, copy.solenoid, copy.rect[0]) == ("Valve 1", 1, 50)
    assert v.rect[0] == 0  # The original is untouched.
    named = Valve(name="Inlet", solenoid=7)
    chip.valves.append(named)
    assert chip.duplicate_element(named).solenoid == 8


def test_run_program_function():
    session = new_session()
    session.open_chip(EXAMPLE)
    program = next(p for p in session.chip.programs if not p.script.is_builtin() and p.script.path.stem == "PluriDrop")
    runner = Runner(session)
    compiled = runner.compiled_program(program)
    compiled.call_function("FullSeal")
    assert not any(session.rig.get_solenoid(v.solenoid) for v in session.chip.valves)
    compiled.call_function("Debubble")  # Yields, so it keeps running in the run loop.
    assert "Debubble" in compiled.running
    runner.tick(time.time())
    discard = next(v for v in session.chip.valves if v.name == "Discard")
    assert session.rig.get_solenoid(discard.solenoid)
    compiled.stop_function("Debubble")
    assert "Debubble" not in compiled.running


def test_removed_programs_stop_running():
    session = new_session()
    session.open_chip(EXAMPLE)
    program = next(p for p in session.chip.programs if not p.script.is_builtin() and p.script.path.stem == "PluriDrop")
    runner = Runner(session)
    runner.compiled_program(program).call_function("Debubble")
    session.chip.remove_elements([program])
    runner.tick()
    assert program not in runner.compiled

    runner.compile_all()
    assert runner.compiled
    session.new_chip()
    runner.tick()
    assert not runner.compiled


def test_compile_error_is_logged_and_kept():
    with tempfile.TemporaryDirectory() as d:
        script_path = Path(d) / "broken.py"
        script_path.write_text("this is not python")
        session = new_session()
        script = session.chip.import_script(script_path)
        program = session.chip.add_program(script)
        compiled = Runner(session).compiled_program(program)
        assert compiled.messages[0].kind == MessageKind.COMPILE_ERROR
        compiled.clear_messages()
        assert len(compiled.messages) == 1


def test_remove_script_in_use_is_refused():
    chip = Chip()
    script = chip.import_script(Path("examples/Priming.py"))
    chip.add_program(script)
    try:
        chip.remove_script(script)
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_undo_redo_edits():
    session = new_session()
    valve = session.chip.add_valve()
    session.record_edit()
    valve.rect[0] = 50.0
    valve.name = "Inlet"
    session.record_edit()
    session.chip.remove_elements([valve])
    session.record_edit()

    session.undo()
    assert session.chip.valves == [valve]
    session.undo()
    assert (valve.name, valve.rect[0]) == ("Valve 0", 0.0)
    session.redo()
    assert (valve.name, valve.rect[0]) == ("Inlet", 50.0)
    session.undo()
    session.undo()
    assert session.chip.valves == []
    session.undo()  # Nothing left to undo.
    session.redo()
    assert session.chip.valves == [valve] and valve.name == "Valve 0"

    # A new edit drops the redo steps.
    valve.solenoid = 5
    session.record_edit()
    session.redo()
    assert valve.name == "Valve 0" and valve.solenoid == 5


def test_undo_keeps_unrecorded_changes():
    session = new_session()
    program = session.chip.add_program(Script(builtin="Pump"))
    program.parameter_values = {"a": 1, "b": 1}
    session.record_edit()
    program.parameter_values["a"] = 2
    session.record_edit()
    # Changed while running: accepted, not undoable.
    program.parameter_values["b"] = 3
    session.accept_changes()

    session.undo()
    assert program.parameter_values == {"a": 1, "b": 3}
    session.redo()
    assert program.parameter_values == {"a": 2, "b": 3}


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok", test.__name__)
