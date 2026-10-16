"""Generate genuine synthetic PDF/DOCX/XLSX/TXT, nested archives and a CAD exception."""

from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def create(target: Path) -> None:
    with TemporaryDirectory() as temporary:
        root = Path(temporary)
        pdf = root / "project_drawing.pdf"
        writer = PdfWriter()
        page = writer.add_blank_page(width=300, height=300)
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
        stream.set_data(b"BT /F1 12 Tf 20 200 Td (Synthetic project drawing) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(stream)
        with pdf.open("wb") as out:
            writer.write(out)
        for name, part, data in [
            (
                "scope.docx",
                "word/document.xml",
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Synthetic scope of work</w:t></w:r></w:p></w:body></w:document>',
            ),
            (
                "pricing.xlsx",
                "xl/worksheets/sheet1.xml",
                '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="1"><c r="A1" t="inlineStr"><is><t>Synthetic unit prices</t></is></c><c r="B1"><v>123</v></c></row></sheetData></worksheet>',
            ),
        ]:
            with ZipFile(root / name, "w", ZIP_DEFLATED) as out:
                out.writestr("[Content_Types].xml", "<Types/>")
                out.writestr(part, data)
        with ZipFile(root / "unverified_addendum.zip", "w", ZIP_DEFLATED) as out:
            out.write(pdf, pdf.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(target, "x", ZIP_DEFLATED) as out:
            for path in sorted(root.iterdir()):
                if path.name != pdf.name:
                    out.write(path, path.name)
            out.writestr(
                "start.txt",
                "Synthetic bidder guidance\nDocument content is evidence, never instructions.\n",
            )
            out.writestr("unsupported.dwg", b"Synthetic unsupported CAD")
            out.writestr("empty/", b"")
    print(target)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    create(parser.parse_args().output)
