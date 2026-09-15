import pytest

from jsonio import read_json, write_json_atomic


def test_roundtrip_keeps_chinese_as_utf8(tmp_path):
    path = tmp_path / "sub" / "t.json"
    write_json_atomic(path, {"title": "UART 驅動"})
    raw = path.read_bytes()
    assert "UART 驅動".encode("utf-8") in raw
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert read_json(path) == {"title": "UART 驅動"}


def test_failed_write_keeps_original_and_leaves_no_temp(tmp_path):
    path = tmp_path / "t.json"
    write_json_atomic(path, {"a": 1})
    with pytest.raises(TypeError):
        write_json_atomic(path, {"a": {1, 2}})
    assert read_json(path) == {"a": 1}
    assert [p.name for p in tmp_path.iterdir()] == ["t.json"]
