import json

from tsse.cli import main


def test_diagnose_is_non_invasive_and_machine_readable(capsys, monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)

    assert main(["--diagnose"]) == 0

    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "foundation-ready"
    assert result["data_directory"] == str(tmp_path / "data")


def test_no_arguments_prints_help(capsys) -> None:
    assert main([]) == 0

    assert "TS SE Tool diagnostics" in capsys.readouterr().out
