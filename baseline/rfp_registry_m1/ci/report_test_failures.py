"""Expose synthetic CI test failures as annotations when raw logs require sign-in."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def escape(value: str) -> str:
    return value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def main(path: Path) -> None:
    if not path.is_file():
        print("::warning::Pytest did not produce a JUnit report; inspect the test step.")
        return
    for case in ET.parse(path).iter("testcase"):
        for tag in ("failure", "error"):
            for failure in case.findall(tag):
                name = case.get("name", "unknown test")
                detail = (failure.text or failure.get("message") or "")[-12000:]
                print(f"::error::{escape(name + chr(10) + detail)}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
