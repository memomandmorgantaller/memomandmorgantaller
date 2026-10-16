import io
import json
import stat
import zipfile

import pytest

from rfp_registry.engine import Limits, Processor


def makezip(path, items):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in items:
            z.writestr(name, content)


def process(tmp_path, source, limits=None):
    out = tmp_path / "output"
    return Processor(source, out, "CS202", limits), out


def test_nested_zip_and_lineage(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as z:
        z.writestr("drawings/M-101.pdf", b"fake pdf data")
    outer = tmp_path / "rfp.zip"
    makezip(outer, [("3.3 Drawings.zip", inner.getvalue()), ("prices.xlsx", b"pricing")])
    job, out = process(tmp_path, outer)
    s = job.run()
    assert s["failed_entries"] == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    rows = manifest["entries"]
    drawing = next(r for r in rows if "M-101.pdf" in r["source_path"])
    assert drawing["depth"] == 2
    assert drawing["parent_id"]
    assert drawing["sha256"]
    assert (out / drawing["extracted_relative_path"]).read_bytes() == b"fake pdf data"
    assert (out / "manifest.csv").exists()


def test_path_traversal_rejected(tmp_path):
    source = tmp_path / "bad.zip"
    makezip(source, [("../../escape.txt", b"bad"), ("good.txt", b"ok"), ("C:/evil", b"no")])
    job, out = process(tmp_path, source)
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert sum(r["error_code"] == "UNSAFE_PATH" for r in rows) == 2
    assert not (tmp_path / "escape.txt").exists()
    assert any(r["original_name"] == "good.txt" and r["status"] == "stored" for r in rows)


def test_duplicate_names_do_not_overwrite(tmp_path):
    source = tmp_path / "duplicate.zip"
    makezip(source, [("one/report.pdf", b"a"), ("two/report.pdf", b"b")])
    job, out = process(tmp_path, source)
    job.run()
    rows = [
        r
        for r in json.loads((out / "manifest.json").read_text())["entries"]
        if r["original_name"].endswith("report.pdf")
    ]
    assert len(rows) == 2
    assert rows[0]["extracted_relative_path"] != rows[1]["extracted_relative_path"]


def test_depth_limit(tmp_path):
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w") as z:
        z.writestr("file.txt", b"hello")
    outer = tmp_path / "root.zip"
    makezip(outer, [("inner.zip", inner.getvalue())])
    job, out = process(tmp_path, outer, Limits(max_depth=1))
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert any(r["error_code"] == "DEPTH_LIMIT" for r in rows)


def test_expansion_size_limit(tmp_path):
    source = tmp_path / "size.zip"
    makezip(source, [("big.txt", b"A" * 5000)])
    job, out = process(tmp_path, source, Limits(max_file_bytes=2000))
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert any(r["error_code"] == "FILE_SIZE_LIMIT" for r in rows)


def test_corrupt_archive_recorded(tmp_path):
    source = tmp_path / "broken.zip"
    source.write_bytes(b"not a zip")
    job, out = process(tmp_path, source)
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert any(r["error_code"] == "INVALID_ARCHIVE" for r in rows)


def test_existing_output_refused(tmp_path):
    source = tmp_path / "a.txt"
    source.write_text("ok")
    job, out = process(tmp_path, source)
    out.mkdir()
    (out / "keep.txt").write_text("safe")
    with pytest.raises(ValueError):
        job.run()
    assert (out / "keep.txt").read_text() == "safe"


def test_output_inside_source_refused(tmp_path):
    source = tmp_path / "inputs"
    source.mkdir()
    (source / "one.txt").write_text("a")
    with pytest.raises(ValueError):
        Processor(source, source / "output", "CS202").run()


def test_source_symlink_refused(tmp_path):
    source = tmp_path / "inputs"
    source.mkdir()
    (source / "original.txt").write_text("abc")
    link = source / "link.txt"
    try:
        link.symlink_to(source / "original.txt")
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not permitted")
    job, out = process(tmp_path, source)
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert any(r["error_code"] == "SYMLINK" for r in rows)


def test_zip_symlink_refused(tmp_path):
    source = tmp_path / "symlink.zip"
    with zipfile.ZipFile(source, "w") as z:
        i = zipfile.ZipInfo("symlink")
        i.create_system = 3
        i.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(i, "target")
    job, out = process(tmp_path, source)
    job.run()
    rows = json.loads((out / "manifest.json").read_text())["entries"]
    assert any(r["error_code"] == "SYMLINK" for r in rows)
