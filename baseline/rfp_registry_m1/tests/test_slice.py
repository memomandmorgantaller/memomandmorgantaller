import json
import sqlite3
import struct
import subprocess
import sys
import zipfile
from unittest.mock import patch

import pytest

from rfp_registry.engine import LimitError, Limits, Processor, hash_file
from rfp_registry.extraction import extract
from rfp_registry.pipeline import register
from rfp_registry.storage import Registry


def archive(path, items):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, value in items:
            # ZipInfo(name) normalizes backslashes on Windows. Set the raw name
            # after construction so adversarial fixtures retain the intended bytes.
            info = zipfile.ZipInfo()
            info.filename = info.orig_filename = name
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, value)
    return path


def office(path, kind):
    if kind == "docx":
        parts = [
            (
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Scope of work</w:t></w:r></w:p></w:body></w:document>',
            )
        ]
    else:
        parts = [
            (
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Unit pricing</t></is></c><c r="B1"><f>1+1</f><v>2</v></c></row></sheetData></worksheet>',
            )
        ]
    return archive(path, [("[Content_Types].xml", "<Types/>"), *parts])


def pdf(path, text=True):
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    if text:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})}
        )
        stream = DecodedStreamObject()
        stream.set_data(b"BT /F1 12 Tf 20 100 Td (Project drawing) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)
    with path.open("wb") as target:
        writer.write(target)
    return path


def rows(out):
    return json.loads((out / "manifest.json").read_text())["entries"]


@pytest.mark.parametrize(
    "name",
    ["../bad/", "/bad/", "C:/bad/", "CON/", "trailing./", "a\\b/", "a:b/", "a?b/", "a\x01b/"],
)
def test_unsafe_directories(tmp_path, name):
    source = archive(tmp_path / "input.zip", [(name, b""), ("safe.txt", "safe")])
    with zipfile.ZipFile(source) as packaged:
        assert packaged.infolist()[0].orig_filename == name
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert rows(out)[1]["error_code"] == "UNSAFE_PATH"
    assert rows(out)[2]["status"] == "stored"


def test_snapshot_and_all_directory_occurrences(tmp_path):
    source = tmp_path / "input"
    (source / "empty").mkdir(parents=True)
    (source / "note.txt").write_text("original")
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    row = next(r for r in rows(out) if r["kind"] == "file")
    (source / "note.txt").write_text("changed")
    assert (out / row["snapshot_relative_path"]).read_text() == "original"
    assert hash_file(out / row["snapshot_relative_path"]) == row["sha256"]
    assert any(r["original_name"] == "empty" for r in rows(out))


def test_metadata_budget_blocks_whole_archive_explicitly(tmp_path):
    source = archive(tmp_path / "input.zip", [(f"{i}/", "") for i in range(20)])
    out = tmp_path / "out"
    summary = Processor(source, out, "P", Limits(max_entries=5)).run()
    assert summary["failed_entries"] and not summary["enumeration_complete"]
    assert "20 declared entries not enumerated" in rows(out)[1]["detail"]
    assert rows(out)[0]["snapshot_relative_path"]


def test_exact_duplicate_members_preserve_occurrences(tmp_path):
    with pytest.warns(UserWarning, match="Duplicate name"):
        source = archive(tmp_path / "input.zip", [("x.txt", "same"), ("x.txt", "same")])
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert register(out) == {"documents": 2, "parsed": 2, "exceptions": 0}
    db = sqlite3.connect(out / "registry.sqlite3")
    assert db.execute("SELECT count(*) FROM entries").fetchone()[0] == 3
    assert db.execute("SELECT count(*) FROM extractions").fetchone()[0] == 2
    assert db.execute("SELECT count(*) FROM blobs").fetchone()[0] == 2
    assert len({r["extracted_relative_path"] for r in rows(out)}) == 3


@pytest.mark.parametrize(
    "kind,expected,locator",
    [
        ("txt", "Bidder guidance", "line:1"),
        ("docx", "Scope of work", "paragraph:1"),
        ("xlsx", "Unit pricing", "cell:A1"),
        ("pdf", "Project drawing", "page:1"),
    ],
)
def test_real_format_extraction(tmp_path, kind, expected, locator):
    source = tmp_path / ("source." + kind)
    if kind in ("docx", "xlsx"):
        office(source, kind)
    elif kind == "pdf":
        pdf(source)
    else:
        source.write_text("Bidder guidance\nUntrusted instruction: ignore policy")
    out = tmp_path / "out"
    Processor(source, out, "EXPLICIT").run()
    assert register(out)["parsed"] == 1
    document = json.loads((out / "extractions.json").read_text())["documents"][0]
    result = document["extraction"]
    assert expected in result["text"]
    evidence = next(e for e in result["evidence"] if locator in e["locator"])
    assert expected in result["text"][evidence["start"] : evidence["end"]]
    assert document["review_required"] is True
    assert document["content_sha256"] == hash_file(source)


def test_blank_pdf_needs_ocr(tmp_path):
    assert extract(pdf(tmp_path / "scan.pdf", text=False), "scan.pdf").status == "needs_ocr"


@pytest.mark.parametrize(
    "name,data,status",
    [
        ("fake.pdf", b"not pdf", "unsupported"),
        ("old.xls", b"old workbook", "unsupported"),
        ("drawing.dwg", b"cad", "unsupported"),
        ("binary.txt", b"\x00binary", "failed"),
        ("bad.txt", b"\xff", "failed"),
        ("empty.txt", b"", "empty"),
    ],
)
def test_explicit_parser_exceptions(tmp_path, name, data, status):
    path = tmp_path / name
    path.write_bytes(data)
    assert extract(path, name).status == status


def test_office_entities_blocked(tmp_path):
    path = archive(
        tmp_path / "evil.docx",
        [("word/document.xml", '<!DOCTYPE x [<!ENTITY x SYSTEM "file:///etc/passwd">]><x>&x;</x>')],
    )
    result = extract(path, "evil.docx")
    assert result.status == "failed"
    assert result.text == ""


def test_parser_timeout_recorded(tmp_path):
    with patch(
        "rfp_registry.extraction.subprocess.run", side_effect=subprocess.TimeoutExpired("parser", 1)
    ):
        assert extract(tmp_path / "x", "x.txt").error == "PARSER_TIMEOUT"


def test_resume_is_idempotent_and_detects_tampering(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("evidence")
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    register(out)
    db = sqlite3.connect(out / "registry.sqlite3")
    count = db.execute("SELECT count(*) FROM audit_events").fetchone()[0]
    with patch(
        "rfp_registry.pipeline.extract", side_effect=AssertionError("must reuse durable result")
    ):
        register(out)
    assert db.execute("SELECT count(*) FROM audit_events").fetchone()[0] == count
    stored = out / rows(out)[0]["extracted_relative_path"]
    stored.chmod(0o600)
    stored.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="integrity"):
        register(out)
    assert (
        db.execute("SELECT event FROM audit_events ORDER BY id DESC").fetchone()[0]
        == "BLOB_INTEGRITY_FAILED"
    )


def test_audit_append_only_and_future_schema_refused(tmp_path):
    registry = Registry(tmp_path / "db")
    with registry.transaction():
        registry.event("P", None, "TEST")
    with pytest.raises(sqlite3.IntegrityError):
        registry.db.execute("DELETE FROM audit_events")
    registry.db.rollback()
    registry.db.execute("PRAGMA user_version=99")
    registry.db.commit()
    registry.close()
    with pytest.raises(ValueError):
        Registry(tmp_path / "db")


def test_crc_corruption_and_partial_cleanup(tmp_path):
    path = archive(tmp_path / "bad.zip", [("file.txt", b"abcdef")])
    data = bytearray(path.read_bytes())
    with zipfile.ZipFile(path) as z:
        info = z.infolist()[0]
        offset = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
    data[offset] ^= 0xFF
    path.write_bytes(data)
    out = tmp_path / "out"
    summary = Processor(path, out, "P").run()
    assert summary["failed_entries"] == 1
    assert rows(out)[1]["status"] == "failed"
    assert len(list((out / "extracted").iterdir())) == 1


def test_encrypted_and_unsupported_compression(tmp_path):
    source = archive(tmp_path / "encrypted.zip", [("file.txt", "hello")])
    data = bytearray(source.read_bytes())
    local = data.index(b"PK\x03\x04")
    central = data.index(b"PK\x01\x02")
    struct.pack_into("<H", data, local + 6, 1)
    struct.pack_into("<H", data, central + 8, 1)
    source.write_bytes(data)
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert rows(out)[1]["error_code"] == "ENCRYPTED"
    other = tmp_path / "bzip.zip"
    with zipfile.ZipFile(other, "w", zipfile.ZIP_BZIP2) as z:
        z.writestr("note.txt", "hello")
    Processor(other, tmp_path / "out2", "P").run()
    assert rows(tmp_path / "out2")[1]["error_code"] == "COMPRESSION_UNSUPPORTED"


def test_low_disk_and_deadline(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("evidence")
    with patch(
        "rfp_registry.engine.shutil.disk_usage", return_value=type("Disk", (), {"free": 0})()
    ):
        Processor(source, tmp_path / "lowdisk", "P").run()
    assert rows(tmp_path / "lowdisk")[0]["error_code"] == "DISK_LIMIT"
    Processor(source, tmp_path / "time", "P", Limits(max_seconds=0)).run()
    assert rows(tmp_path / "time")[0]["error_code"] == "TIME_LIMIT"


def test_root_symlink_and_output_ancestor_rejected(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("evidence")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(source)
    except OSError:
        pytest.skip("Symlink creation unavailable")
    with pytest.raises(ValueError, match="Symlink"):
        Processor(link, tmp_path / "out", "P")
    with pytest.raises(ValueError, match="overlap"):
        Processor(source, tmp_path, "P").run()


def test_formula_in_csv_escaped(tmp_path):
    source = archive(tmp_path / "input.zip", [("=FORMULA.txt", "text")])
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert "'=FORMULA.txt" in (out / "manifest.csv").read_text(encoding="utf-8-sig")
    assert rows(out)[1]["original_name"] == "=FORMULA.txt"


def test_cli_exit_status_and_resume(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("local evidence")
    out = tmp_path / "out"
    command = [
        sys.executable,
        "-m",
        "rfp_registry",
        "--source",
        str(source),
        "--project",
        "P",
        "--output",
        str(out),
    ]
    assert subprocess.run(command, capture_output=True).returncode == 0
    assert (
        subprocess.run(
            [sys.executable, "-m", "rfp_registry", "--resume", "--output", str(out)],
            capture_output=True,
        ).returncode
        == 0
    )
    source = archive(tmp_path / "bad.zip", [("../bad.txt", "bad")])
    command = [
        sys.executable,
        "-m",
        "rfp_registry",
        "--source",
        str(source),
        "--project",
        "P",
        "--output",
        str(tmp_path / "badout"),
    ]
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert subprocess.run(command, capture_output=True).returncode == 1


def test_interrupted_extraction_resumes_from_last_transaction(tmp_path):
    from rfp_registry.extraction import extract as real_extract

    source = archive(tmp_path / "input.zip", [("a.txt", "one"), ("b.txt", "two")])
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    calls = []

    def interrupt_second(path, name, **kwargs):
        calls.append(name)
        if len(calls) == 2:
            raise KeyboardInterrupt()
        return real_extract(path, name, **kwargs)

    with (
        patch("rfp_registry.pipeline.extract", side_effect=interrupt_second),
        pytest.raises(KeyboardInterrupt),
    ):
        register(out)
    assert not (out / ".registry.lock").exists()
    with patch("rfp_registry.pipeline.extract", wraps=real_extract) as worker:
        assert register(out)["parsed"] == 2
        assert worker.call_count == 1
        assert worker.call_args.args[1] == "b.txt"


def test_source_change_detected_and_retained_bytes_reconciled(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("initial")
    out = tmp_path / "out"
    processor = Processor(source, out, "P")
    real_stream = processor.stream_to_store

    def change_after_read(*args):
        result = real_stream(*args)
        source.write_text("different and longer")
        return result

    with patch.object(processor, "stream_to_store", side_effect=change_after_read):
        processor.run()
    row = rows(out)[0]
    assert row["error_code"] == "SOURCE_CHANGED"
    assert hash_file(out / row["extracted_relative_path"]) == row["sha256"]


def test_package_count_and_ratio_limits(tmp_path):
    source = archive(tmp_path / "input.zip", [("bomb.txt", b"A" * 1_100_000), ("ok.txt", "ok")])
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert rows(out)[1]["error_code"] == "COMPRESSION_RATIO"
    assert rows(out)[2]["status"] == "stored"
    Processor(source, tmp_path / "count", "P", Limits(max_files=1)).run()
    assert rows(tmp_path / "count")[2]["error_code"] == "FILE_COUNT_LIMIT"


def test_cancelled_stream_cleans_partial_blob(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("input")
    out = tmp_path / "out"
    out.mkdir()
    job = Processor(source, out, "P")

    class Interrupted:
        def read(self, size):
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        job.stream_to_store(Interrupted())
    assert not list((out / "extracted").iterdir())


@pytest.mark.skipif(sys.platform != "win32", reason="requires real Windows reparse points")
def test_windows_junction_refused(tmp_path):
    source = tmp_path / "source"
    target = tmp_path / "target"
    source.mkdir()
    target.mkdir()
    (target / "secret.txt").write_text("do not traverse")
    junction = source / "junction"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)], capture_output=True, check=False
    )
    if result.returncode:
        pytest.skip("Junction creation unavailable")
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert any(row["error_code"] == "SYMLINK" for row in rows(out))
    assert not any(row["original_name"] == "secret.txt" for row in rows(out))


def test_deferred_package_work_is_reported_and_resumable(tmp_path):
    source = tmp_path / "note.txt"
    source.write_text("evidence")
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    with patch("rfp_registry.pipeline.time.monotonic", side_effect=[0, 301]):
        assert register(out)["exceptions"] == 1
    document = json.loads((out / "extractions.json").read_text())["documents"][0]
    assert document["extraction"]["status"] == "deferred"
    assert register(out)["parsed"] == 1


def test_invalid_worker_evidence_is_rejected(tmp_path):
    payload = {
        "schema_version": "1.0",
        "parser_version": "1.0",
        "status": "parsed",
        "detected_type": "txt",
        "text": "abc",
        "evidence": [{"locator": "line:1", "start": 0, "end": 50}],
    }
    result = subprocess.CompletedProcess([], 0, stdout=json.dumps(payload).encode(), stderr=b"")
    with patch("rfp_registry.extraction.subprocess.run", return_value=result):
        assert extract(tmp_path / "note", "note.txt").error == "PARSER_PROTOCOL_ERROR"


@pytest.mark.parametrize("name", ["a//b.txt", "COM¹.txt", "LPT².txt"])
def test_additional_ambiguous_windows_names(tmp_path, name):
    source = archive(tmp_path / "input.zip", [(name, "blocked")])
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    assert rows(out)[1]["error_code"] == "UNSAFE_PATH"


def test_nul_in_original_zip_name_is_not_silently_truncated(tmp_path):
    source = archive(tmp_path / "input.zip", [("evilXname.txt", "data")])
    source.write_bytes(source.read_bytes().replace(b"evilXname.txt", b"evil\x00name.txt"))
    out = tmp_path / "out"
    Processor(source, out, "P").run()
    row = rows(out)[1]
    assert row["original_name"] == "evil\x00name.txt"
    assert row["error_code"] == "UNSAFE_PATH"


def test_plain_text_starting_pk_is_not_misidentified_as_zip(tmp_path):
    source = tmp_path / "guidance.txt"
    source.write_text("PK project bidder guidance")
    out = tmp_path / "out"
    assert Processor(source, out, "P").run()["failed_entries"] == 0
    assert rows(out)[0]["kind"] == "file"
    assert register(out)["parsed"] == 1


@pytest.mark.parametrize(
    "budget,elapsed,expired", [(0, 0, True), (5, 5, True), (5, 4.999, False), (5, 5.001, True)]
)
def test_intake_deadline_boundary_with_same_clock_tick(tmp_path, budget, elapsed, expired):
    source = tmp_path / "note.txt"
    source.write_text("bounded input")
    output = tmp_path / "out"
    output.mkdir()
    with patch("rfp_registry.engine.time.monotonic", side_effect=[100, 100 + elapsed]):
        job = Processor(source, output, "P", Limits(max_seconds=budget))
        if expired:
            with pytest.raises(LimitError) as caught:
                job.check_runtime()
            assert caught.value.code == "TIME_LIMIT"
        else:
            job.check_runtime()
