#!/usr/bin/env python3
"""Extract text from an HWPX document.

Wraps python-hwpx's TextExtractor for convenient CLI use.

Usage:
    python text_extract.py document.hwpx
    python text_extract.py document.hwpx --format markdown
    python text_extract.py document.hwpx --include-tables
"""

import argparse
import sys
from pathlib import Path

try:
    from hwpx import TextExtractor
except ImportError:
    print("ERROR: python-hwpx not installed. Run: python -m pip install -r .claude/skills/hwpxskill/scripts/requirements.txt", file=sys.stderr)
    sys.exit(1)


def extract_plain(hwpx_path: str, *, include_tables: bool = False) -> str:
    """Extract plain text from HWPX file."""

    object_behavior = "nested" if include_tables else "skip"
    with TextExtractor(hwpx_path) as ext:
        return ext.extract_text(
            include_nested=include_tables,
            object_behavior=object_behavior,
            skip_empty=True,
        )


def extract_markdown(hwpx_path: str) -> str:
    """Extract text as Markdown with section separators."""

    lines: list[str] = []

    with TextExtractor(hwpx_path) as ext:
        for section in ext.iter_sections():
            if lines:
                lines.append("")
                lines.append("---")
                lines.append("")

            for para in ext.iter_paragraphs(section, include_nested=True):
                text = para.text(object_behavior="nested")
                if text.strip():
                    if para.is_nested:
                        # Table cell or nested content - indent
                        lines.append(f"  {text}")
                    else:
                        lines.append(text)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from an HWPX document"
    )
    parser.add_argument("input", help="Path to .hwpx file")
    parser.add_argument(
        "--format", "-f",
        choices=["plain", "markdown"],
        default="plain",
        help="Output format (default: plain)",
    )
    parser.add_argument(
        "--include-tables",
        action="store_true",
        help="(deprecated, now the default) kept so old commands keep working",
    )
    parser.add_argument(
        "--no-tables",
        action="store_true",
        help="Skip tables and nested objects. Korean forms put most of their body "
             "inside tables, so this usually returns almost nothing.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
    )
    args = parser.parse_args()

    if not Path(args.input).is_file():
        print(f"Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    # 표는 기본으로 포함한다. 한글 서식·공문서는 본문이 대부분 표 안에 있어서,
    # 표를 건너뛰면 내용이 가득한 문서가 몇 글자로 나오고 에러는 나지 않는다.
    # (실측 2026-09-01: 같은 서식 1건이 표 제외 11자 / 표 포함 2,057자)
    if args.format == "markdown":
        result = extract_markdown(args.input)
    else:
        result = extract_plain(args.input, include_tables=not args.no_tables)

    if args.no_tables:
        print(
            "주의: --no-tables 로 표를 건너뛰었습니다. "
            "결과가 짧아도 '내용 없음'이 아닐 수 있습니다.",
            file=sys.stderr,
        )

    if args.output:
        Path(args.output).write_text(result, encoding="utf-8")
        print(f"Extracted to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
