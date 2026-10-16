"""Create a harmless sample RFP containing nested ZIPs (no real documents)."""

import io
import zipfile
from pathlib import Path


def main():
    dest = Path(__file__).resolve().parent / "synthetic_CS202.zip"
    inner = io.BytesIO()
    with zipfile.ZipFile(inner, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("mechanical/M-104.txt", "SYNTHETIC DRAWING PLACEHOLDER: pump skid")
        z.writestr("piping/P-001.txt", "SYNTHETIC DRAWING PLACEHOLDER: piping")
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("3.3 CS202 Drawings.zip", inner.getvalue())
        z.writestr("01 Commercial/Unit Prices.txt", "SYNTHETIC PRICE SHEET")
        z.writestr("06 Addenda/Addendum-01.txt", "SYNTHETIC ADDENDUM")
        z.writestr("07 Clarifications/QA.txt", "SYNTHETIC CLARIFICATION")
    print(dest)


if __name__ == "__main__":
    main()
