"""Bounded, local-only evidence extraction. No external resources are resolved."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

from defusedxml import ElementTree as ET

from .safety import zip_metadata

PARSER_VERSION = "1.0"
MAX_INPUT = 32_000_000
MAX_TEXT = 1_000_000
MAX_UNITS = 10000
MAX_XML = 16_000_000
MAX_PAGES = 500


@dataclass(frozen=True)
class Evidence:
    locator: str
    start: int
    end: int


@dataclass
class Extraction:
    schema_version: str = "1.0"
    parser_version: str = PARSER_VERSION
    status: Literal["parsed", "needs_ocr", "unsupported", "failed", "empty", "deferred"] = "failed"
    detected_type: str = "unknown"
    text: str = ""
    evidence: list[Evidence] = field(default_factory=list)
    quality: str = "unavailable"
    error: str | None = None

    def __post_init__(self) -> None:
        if self.schema_version != "1.0" or self.parser_version != PARSER_VERSION:
            raise ValueError("Unexpected extraction version")
        if self.status not in {"parsed", "needs_ocr", "unsupported", "failed", "empty", "deferred"}:
            raise ValueError("Unexpected extraction status")
        if self.quality not in {"unavailable", "no_text", "text_present_unvalidated"}:
            raise ValueError("Unexpected extraction quality")
        if self.error is not None and (not isinstance(self.error, str) or len(self.error) > 300):
            raise ValueError("Invalid extraction error")
        if self.detected_type not in {"unknown", "pdf", "docx", "xlsx", "txt"}:
            raise ValueError("Unexpected content type")
        if (
            not isinstance(self.text, str)
            or len(self.text) > MAX_TEXT
            or len(self.evidence) > MAX_UNITS
        ):
            raise ValueError("Invalid/oversized extraction")
        for ref in self.evidence:
            if (
                type(ref.start) is not int
                or type(ref.end) is not int
                or not 0 <= ref.start <= ref.end <= len(self.text)
                or not isinstance(ref.locator, str)
                or not 0 < len(ref.locator) <= 256
            ):
                raise ValueError("Invalid evidence offsets/locator")


class TextBuilder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.evidence: list[Evidence] = []
        self.size = 0

    def add(self, locator: str, text: str) -> None:
        if len(self.evidence) >= MAX_UNITS or self.size + len(text) + 1 > MAX_TEXT:
            raise ValueError("TEXT_LIMIT: extracted text/units exceed budget")
        self.evidence.append(Evidence(locator, self.size, self.size + len(text)))
        self.parts.append(text + "\n")
        self.size += len(text) + 1

    def result(self, kind: str) -> Extraction:
        text = "".join(self.parts)
        nonblank = bool(text.strip())
        return Extraction(
            status="parsed" if nonblank else ("needs_ocr" if kind == "pdf" else "empty"),
            detected_type=kind,
            text=text,
            evidence=self.evidence,
            quality="text_present_unvalidated" if nonblank else "no_text",
        )


def _office(path: Path, kind: str, builder: TextBuilder) -> None:
    zip_metadata(path, 2000, 2_000_000)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        if sum(i.file_size for i in infos) > MAX_XML:
            raise ValueError("OFFICE_LIMIT: expanded Office package exceeds budget")
        if len({i.filename for i in infos}) != len(infos):
            raise ValueError("OFFICE_DUPLICATE: ambiguous duplicate XML parts")
        if any(i.flag_bits & 1 or i.compress_type not in (0, 8) for i in infos):
            raise ValueError("OFFICE_FEATURE: encrypted/unsupported compression")

        def xml(name: str):
            # Only fixed internal names read; paths are never written or fetched.
            if archive.getinfo(name).file_size > MAX_XML:
                raise ValueError("XML_LIMIT")
            return ET.fromstring(archive.read(name))

        names = set(archive.namelist())
        if kind == "docx":
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            document = xml("word/document.xml")
            for number, paragraph in enumerate(document.findall(".//w:p", ns), 1):
                builder.add(
                    f"paragraph:{number}",
                    "".join(t.text or "" for t in paragraph.findall(".//w:t", ns)),
                )
        else:
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            shared = []
            if "xl/sharedStrings.xml" in names:
                shared = [
                    "".join(t.text or "" for t in item.findall(".//s:t", ns))
                    for item in xml("xl/sharedStrings.xml").findall("s:si", ns)
                ]
            sheets = sorted(n for n in names if re.fullmatch(r"xl/worksheets/sheet[0-9]+\.xml", n))
            if not sheets:
                raise ValueError("No supported worksheet parts")
            for sheet in sheets:
                for index, cell in enumerate(xml(sheet).findall(".//s:sheetData/s:row/s:c", ns), 1):
                    coordinate = cell.get("r", "")
                    if not re.fullmatch(r"[A-Z]{1,3}[1-9][0-9]{0,6}", coordinate):
                        raise ValueError("Invalid/missing cell reference")
                    value = cell.find("s:v", ns)
                    text = value.text or "" if value is not None else ""
                    if cell.get("t") == "s":
                        slot = int(text)
                        if not 0 <= slot < len(shared):
                            raise ValueError("Invalid shared string reference")
                        text = shared[slot]
                    elif cell.get("t") == "inlineStr":
                        text = "".join(t.text or "" for t in cell.findall(".//s:t", ns))
                    # Formulas never evaluated; cached values explicitly marked.
                    suffix = ":cached_formula" if cell.find("s:f", ns) is not None else ""
                    builder.add(f"{sheet}:cell:{coordinate}:occurrence:{index}{suffix}", text)


def parse_local(path: Path, name: str) -> Extraction:
    """Worker entry point: size/signature verification before invoking parsers."""
    if path.stat().st_size > MAX_INPUT:
        return Extraction(status="unsupported", error="PARSER_SIZE_LIMIT")
    with path.open("rb") as source:
        magic = source.read(8)
    suffix = Path(name).suffix.lower()
    builder = TextBuilder()
    try:
        if magic.startswith(b"%PDF-"):
            kind = "pdf"
        elif magic.startswith(b"PK\x03\x04") and suffix in (".docx", ".xlsx"):
            kind = suffix[1:]
        elif suffix == ".txt":
            kind = "txt"
        else:
            return Extraction(status="unsupported", error="UNSUPPORTED_FORMAT")
        if suffix in (".pdf", ".docx", ".xlsx") and suffix != "." + kind:
            return Extraction(status="failed", detected_type=kind, error="TYPE_MISMATCH")
        if kind == "pdf":
            from pypdf import PdfReader

            reader = PdfReader(path, strict=True)
            if reader.is_encrypted:
                raise ValueError("ENCRYPTED_PDF")
            if len(reader.pages) > MAX_PAGES:
                raise ValueError("PDF_PAGE_LIMIT")
            for page, content in enumerate(reader.pages, 1):
                builder.add(f"page:{page}", content.extract_text() or "")
        elif kind in ("docx", "xlsx"):
            _office(path, kind, builder)
        else:
            raw = path.read_bytes()
            if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = raw.decode("utf-16")
            else:
                text = raw.decode("utf-8-sig")
            if any(ord(c) < 32 and c not in "\t\r\n" for c in text):
                raise ValueError("BINARY_TEXT_MISMATCH")
            for number, line in enumerate(text.splitlines(), 1):
                builder.add(f"line:{number}", line)
        return builder.result(kind)
    except Exception as error:
        # Do not log parser exceptions containing document text or secrets.
        return Extraction(
            status="failed",
            detected_type=locals().get("kind", "unknown"),
            error=f"PARSE_ERROR:{type(error).__name__}",
        )


def extract(path: Path, name: str, timeout: float = 20) -> Extraction:
    """One disposable process per document; deadline applies on Windows and Linux.

    This is fault containment, not an OS security sandbox. No tool/network API is
    offered. Windows process memory must additionally be constrained by deployment.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "rfp_registry.extraction", str(path), name],
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode:
            return Extraction(error="PARSER_PROCESS_FAILED")
        payload = json.loads(result.stdout)
        if not isinstance(payload, dict):
            raise ValueError("Invalid worker result root")
        evidence = [Evidence(**row) for row in payload.pop("evidence")]
        return Extraction(**payload, evidence=evidence)
    except subprocess.TimeoutExpired:
        return Extraction(error="PARSER_TIMEOUT")
    except (ValueError, TypeError, KeyError, OSError):
        return Extraction(error="PARSER_PROTOCOL_ERROR")


if __name__ == "__main__":
    import logging

    logging.getLogger("pypdf").disabled = True
    if sys.platform != "win32":
        import resource

        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (15, 15))
    print(json.dumps(asdict(parse_local(Path(sys.argv[1]), sys.argv[2])), ensure_ascii=True))
