from meetai.instances import is_meetai_cli, other_instances


def test_recognises_module_and_console_script_invocations():
    assert is_meetai_cli(["python", "-m", "meetai.cli", "--show-latency"])
    assert is_meetai_cli(["/home/x/.venv/bin/meetai", "--list-devices"])
    assert not is_meetai_cli(["python", "scripts/bench_asr.py"])
    assert not is_meetai_cli([])


def test_finds_other_instances_but_not_itself(tmp_path):
    def proc(pid, *args):
        d = tmp_path / str(pid)
        d.mkdir()
        (d / "cmdline").write_bytes(b"\0".join(a.encode() for a in args) + b"\0")

    proc(10, "python", "-m", "meetai.cli")
    proc(11, "python", "-m", "meetai.cli")  # "own" process
    proc(12, "zsh")
    (tmp_path / "self").mkdir()  # non-numeric entries are ignored
    assert other_instances(str(tmp_path), own_pid=11) == [10]
