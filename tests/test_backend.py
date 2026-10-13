"""Backend tests. These drive uChip without any GUI, the way a command-line tool would.

Run from the repository root with `python -m pytest tests` or `python tests/test_backend.py`.
"""
import json
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
    runner.ensure_programs_compiled()
    for compiled in runner.compiled_program_map.values():
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
    compiled = runner.get_compiled_program(program)
    compiled.call_function("FullSeal")
    assert not any(session.rig.get_solenoid(v.solenoid) for v in session.chip.valves)
    compiled.call_function("Debubble")  # Yields, so it keeps running in the run loop.
    assert "Debubble" in compiled.running
    runner.tick()
    discard = next(v for v in session.chip.valves if v.name == "Discard")
    assert session.rig.get_solenoid(discard.solenoid)
    compiled.stop_function("Debubble")
    assert "Debubble" not in compiled.running


def test_removed_programs_stop_running():
    session = new_session()
    session.open_chip(EXAMPLE)
    program = next(p for p in session.chip.programs if not p.script.is_builtin() and p.script.path.stem == "PluriDrop")
    runner = Runner(session)
    runner.get_compiled_program(program).call_function("Debubble")
    session.chip.remove_elements([program])
    runner.tick()
    assert program not in runner.compiled_program_map

    runner.ensure_programs_compiled()
    assert runner.compiled_program_map
    session.new_chip()
    runner.tick()
    assert not runner.compiled_program_map


def test_compile_error_is_logged_and_kept():
    with tempfile.TemporaryDirectory() as d:
        script_path = Path(d) / "broken.py"
        script_path.write_text("this is not python")
        session = new_session()
        script = session.chip.import_script(script_path)
        program = session.chip.add_program(script)
        compiled = Runner(session).get_compiled_program(program)
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


def _session_with_script(directory: str, source: str):
    """A session whose chip has a valve "V" (solenoid 3) and a program running [source]."""
    script_path = Path(directory) / "script.py"
    script_path.write_text(source)
    session = new_session()
    valve = session.chip.add_valve()
    valve.name, valve.solenoid = "V", 3
    program = session.chip.add_program(session.chip.import_script(script_path))
    return session, program


PWM_SCRIPT = """
@onStop(lambda: FindValve("V").Close())
def PWM():
    v = FindValve("V")
    while True:
        v.Open()
        yield WaitForSeconds(0.01)
        v.Close()
        yield WaitForSeconds(0.01)

def Once():
    v = FindValve("V")
    v.Open()
    yield
"""


def test_waits_do_not_drift():
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, PWM_SCRIPT)
        runner = Runner(session)
        runner.get_compiled_program(program).call_function("PWM")
        # Ticks 1.3 ms apart, so each wait ends a little after it is due.
        edges, state = [], None
        for i in range(2000):
            now = 100 + i * 0.0013
            runner.tick(now)
            if session.rig.get_solenoid(3) != state:
                state = session.rig.get_solenoid(3)
                edges.append(now)
        # Each edge is within one tick of when it is due, however many waits came before it.
        for n, edge in enumerate(edges):
            assert 0 <= edge - (100 + n * 0.01) < 0.0013 + 1e-9, (n, edge)


def test_stopped_functions_call_on_stop():
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, PWM_SCRIPT)
        runner = Runner(session)
        runner.get_compiled_program(program).call_function("PWM")
        runner.tick()
        assert session.rig.get_solenoid(3)
        session.chip.remove_elements([program])
        runner.tick()
        assert not runner.compiled_program_map and not session.rig.get_solenoid(3)


def test_finished_function_calls_on_stop():
    source = PWM_SCRIPT + "\nOnce = onStop(lambda: FindValve('V').Close())(Once)\n"
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, source)
        runner = Runner(session)
        compiled = runner.get_compiled_program(program)
        compiled.call_function("Once")
        runner.tick()
        assert session.rig.get_solenoid(3) and compiled.is_function_running("Once")
        runner.tick()
        assert not session.rig.get_solenoid(3) and not compiled.is_function_running("Once")


def test_posted_commands_run_on_next_tick():
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, PWM_SCRIPT)
        runner = Runner(session)
        runner.enqueue_command(lambda: runner.get_compiled_program(program).call_function("PWM"))
        assert not runner.compiled_program_map
        runner.tick()
        assert runner.get_compiled_program(program).is_function_running("PWM") and session.rig.get_solenoid(3)


def test_parameter_types():
    from backend import ucscript
    from backend.programs import default_value_for_type, does_value_match_type
    assert does_value_match_type(3, int) and not does_value_match_type("3", int)
    assert not does_value_match_type(True, int) and does_value_match_type(True, bool)
    assert does_value_match_type(3, float) and not does_value_match_type(1.5, str)
    assert does_value_match_type(Valve(), ucscript.Valve) and not does_value_match_type(None, ucscript.Valve)
    valves = ucscript.ListParameterType(ucscript.Valve)
    assert does_value_match_type([Valve()], valves) and not does_value_match_type([Valve(), 1], valves)
    options = ucscript.OptionsParameterType(["a", "b"])
    assert does_value_match_type("b", options) and not does_value_match_type("c", options)
    assert default_value_for_type(bool) is False


class FakePort:
    is_open = True

    def __init__(self):
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def close(self):
        self.is_open = False


def _rig_with_fake_device():
    from backend.device import Device
    from backend.rig import Rig
    device = Device(hwid="X", enabled=True, available=True, serial_port=FakePort())
    return Rig(devices=[device]), device


def test_rig_sends_changed_banks_together():
    rig, device = _rig_with_fake_device()
    rig.set_solenoid(0, True)
    rig.set_solenoid(20, True)
    rig.flush()
    assert device.serial_port.writes == [b"A\x01B\x00C\x10"]
    rig.flush()
    rig.set_solenoid(0, True)  # Unchanged.
    rig.flush()
    assert len(device.serial_port.writes) == 1
    rig.set_solenoid(0, False)
    rig.flush()
    assert device.serial_port.writes[-1] == b"A\x00"


def test_blink_runs_in_flush_and_restores_states():
    from backend.rig import BLINK_PERIOD
    rig, device = _rig_with_fake_device()
    rig.set_solenoid(1, True)
    rig.flush()
    rig.start_blink(device)
    start = rig.blink_start_time
    rig.flush(start)
    assert device.serial_port.writes[-1] == b"A\xffB\xffC\xff"
    rig.flush(start + BLINK_PERIOD * 1.5)
    assert device.serial_port.writes[-1] == b"A\x00B\x00C\x00"
    rig.flush(start + BLINK_PERIOD * 100)
    assert rig.blinking_device is None and device.serial_port.writes[-1] == b"A\x02"


def test_rescan_does_not_duplicate_ports_without_hwid():
    from types import SimpleNamespace
    from backend import rig as rig_module
    from backend.device import Device
    found = lambda: [Device(hwid="", available=True, port_info=SimpleNamespace(device="COM7"))]
    original = rig_module.get_available_devices
    rig_module.get_available_devices = found
    try:
        rig = rig_module.Rig()
        rig.rescan_devices()
        rig.rescan_devices()
        assert len(rig.devices) == 1 and rig.devices[0].available
    finally:
        rig_module.get_available_devices = original


def test_scripts_are_utf8_and_a_failed_save_keeps_the_file():
    from backend.chip import read_script, write_script
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "script.py"
        write_script(path, "# 25 °C → µl\n")
        assert read_script(path) == "# 25 °C → µl\n"
        try:
            write_script(path, "bad \ud800 surrogate")
            assert False, "expected UnicodeEncodeError"
        except UnicodeEncodeError:
            pass
        assert read_script(path) == "# 25 °C → µl\n"
        # Scripts saved by older versions in the system encoding are still read.
        path.write_bytes("# 25 °C\n".encode("cp1252"))
        assert read_script(path) == "# 25 °C\n"


def test_log_stores_text():
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, "@display\ndef Go():\n    Log(5)\n")
        compiled = Runner(session).get_compiled_program(program)
        compiled.call_function("Go")
        assert [m.text for m in compiled.messages] == ["5"]


def test_parameter_defaults():
    source = ("a = Parameter(int, defaultValue=7)\n"
              "b = OptionsParameter(['x', 'y', 'z'], defaultIndex=2)\n"
              "c = Parameter(float, minimum=5)\n"
              "d = Parameter(float, defaultValue=3)\n"
              "e = Parameter(int, defaultValue='wrong type')\n")
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, source)
        Runner(session).get_compiled_program(program)
        assert program.parameter_values == {"a": 7, "b": "z", "c": 5.0, "d": 3.0, "e": 0}
        assert isinstance(program.parameter_values["d"], float)


def test_malformed_project_files_raise_value_error():
    valid = project_file.chip_to_json(Chip(), Path.cwd())
    bad_reference = dict(valid, programs=[{"name": "p", "script": {"path": "x.py"}, "position": [0, 0], "scale": 1,
                                           "show_log": True,
                                           "parameters": {"v": {"value": {"valve": 5}, "visible": True}}}])
    with tempfile.TemporaryDirectory() as d:
        for i, data in enumerate([[], {"format": "uchip"}, bad_reference, dict(valid, valves=[5])]):
            path = Path(d) / ("bad%d.uchip" % i)
            path.write_text(json.dumps(data))
            try:
                project_file.load_chip(path)
                assert False, "expected ValueError for %r" % data
            except ValueError:
                pass


def test_malformed_devices_file_starts_with_no_devices():
    from backend.rig import load_rig_from_file
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "devices.json"
        path.write_text("not json")
        assert load_rig_from_file(path).devices == []
        assert not path.exists() and (Path(d) / "devices.json.bad").read_text() == "not json"
        path.write_text('[{}, {"hwid": "COM9", "start_number": 24}]')
        devices = load_rig_from_file(path).devices
        assert [(device.hwid, device.start_number) for device in devices] == [("COM9", 24)]


def test_a_blocking_command_is_reported_stuck():
    with tempfile.TemporaryDirectory() as d:
        session, program = _session_with_script(d, PWM_SCRIPT)
        runner = Runner(session)
        seen = []
        # A function that doesn't yield runs entirely inside its command, which stuck_function() must cover.
        runner.enqueue_command(lambda: seen.append(runner.stuck_function(0)), program, "Hang")
        runner.tick()
        assert seen == [(program.name, "Hang")] and runner.stuck_function(0) is None


if __name__ == "__main__":
    tests = [f for name, f in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
        print("ok", test.__name__)
