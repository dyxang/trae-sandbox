#!/usr/bin/env python3
"""
Privacy Scanner for Markdown Files
Scans markdown files and flags potential privacy-sensitive content.
Based on regex patterns from privacyfilter.app
"""

import re
import os
import sys
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PrivacySpan:
    """Represents a detected privacy-sensitive span in text."""
    label: str
    text: str
    start: int
    end: int
    source: str
    line_number: int = 0
    file_path: str = ""


@dataclass
class ScanResult:
    """Result of scanning a single file."""
    file_path: str
    total_spans: int
    spans_by_type: dict
    spans: list


PATTERNS = [
    {
        "label": "account_number",
        "source": "iban",
        "regex": r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}(?:[A-Z0-9]?){0,16}\b"
    },
    {
        "label": "secret",
        "source": "ssn",
        "regex": r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
    },
    {
        "label": "secret",
        "source": "mac",
        "regex": r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b"
    },
    {
        "label": "secret",
        "source": "ipv4",
        "regex": r"\b(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\b"
    },
    {
        "label": "secret",
        "source": "ipv6",
        "regex": r"\b(?:[0-9A-Fa-f]{1,4}:){7}[0-9A-Fa-f]{1,4}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,7}:|\b(?:[0-9A-Fa-f]{1,4}:){1,6}:[0-9A-Fa-f]{1,4}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,5}(?::[0-9A-Fa-f]{1,4}){1,2}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,4}(?::[0-9A-Fa-f]{1,4}){1,3}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,3}(?::[0-9A-Fa-f]{1,4}){1,4}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,2}(?::[0-9A-Fa-f]{1,4}){1,5}\b|\b[0-9A-Fa-f]{1,4}:(?::[0-9A-Fa-f]{1,4}){1,6}\b|\b:(?::[0-9A-Fa-f]{1,4}){1,7}\b|\b::(?:[0-9A-Fa-f]{1,4}:){0,5}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b[0-9A-Fa-f]{1,4}::(?:[0-9A-Fa-f]{1,4}:){0,4}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,5}::(?:[0-9A-Fa-f]{1,4}:){0,3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,4}::(?:[0-9A-Fa-f]{1,4}:){0,2}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,3}::(?:[0-9A-Fa-f]{1,4}:){0,1}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b(?:[0-9A-Fa-f]{1,4}:){1,2}::(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b[0-9A-Fa-f]{1,4}::(?:[0-9A-Fa-f]{1,4}:){0,1}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b|\b::(?:[0-9A-Fa-f]{1,4}:){0,2}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}\b"
    },
    {
        "label": "secret",
        "source": "jwt",
        "regex": r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    },
    {
        "label": "secret",
        "source": "api_key",
        "regex": r"\b(?:sk-[A-Za-z0-9]{20,}|sk-live-[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|glpat-[A-Za-z0-9\-]{20,}|xox[bpors]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_\-]{35}|key-[A-Za-z0-9]{20,}|Bearer\s+[A-Za-z0-9\-._~+/]+=*)\b"
    },
    {
        "label": "secret",
        "source": "btc_wallet",
        "regex": r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b|\bbc1[a-zA-HJ-NP-Z0-9]{25,62}\b"
    },
    {
        "label": "secret",
        "source": "eth_wallet",
        "regex": r"\b0x[0-9A-Fa-f]{40}\b"
    },
    {
        "label": "secret",
        "source": "sol_wallet",
        "regex": r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b"
    }
]

PATTERN_DESCRIPTIONS = {
    "iban": "International Bank Account Number",
    "ssn": "US Social Security Number",
    "mac": "MAC Address",
    "ipv4": "IPv4 Address",
    "ipv6": "IPv6 Address",
    "jwt": "JSON Web Token",
    "api_key": "API Key / Token",
    "btc_wallet": "Bitcoin Wallet Address",
    "eth_wallet": "Ethereum Wallet Address",
    "sol_wallet": "Solana Wallet Address"
}

COMPILED_PATTERNS = [
    {"label": p["label"], "source": p["source"], "regex": re.compile(p["regex"], re.IGNORECASE)}
    for p in PATTERNS
]

IPV4_IN_IPV6_PATTERN = re.compile(
    r"(?:^|:)(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(?:\.(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)){3}(?:$|:)"
)

IPV4_PATTERN = re.compile(
    r"^(?:(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\.){3}(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)$"
)


def validate_span(span: dict, matched_text: str) -> bool:
    """Validate detected span to reduce false positives."""
    source = span["source"]

    if source == "ipv6":
        if not IPV4_IN_IPV6_PATTERN.search(matched_text):
            if IPV4_PATTERN.match(matched_text):
                return False

    if source == "eth_wallet":
        if re.match(r"^0x[0-9a-f]{1,6}$", matched_text, re.IGNORECASE):
            return False
        if re.match(r"^0x0{40}$", matched_text, re.IGNORECASE):
            return False

    if source == "sol_wallet":
        if len(matched_text) < 32:
            return False

    if source == "btc_wallet":
        if re.match(r"^1[0]{25,34}$", matched_text):
            return False

    return True


def scan_text(text: str, file_path: str = "") -> list[PrivacySpan]:
    """Scan text for privacy-sensitive patterns."""
    spans = []

    lines = text.split('\n')
    line_starts = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1

    for pattern_info in COMPILED_PATTERNS:
        for match in pattern_info["regex"].finditer(text):
            matched_text = match.group(0)

            if not validate_span(pattern_info, matched_text):
                continue

            char_pos = match.start()
            line_number = 0
            for i, start in enumerate(line_starts):
                if start > char_pos:
                    break
                line_number = i

            spans.append(PrivacySpan(
                label=pattern_info["label"],
                text=matched_text,
                start=match.start(),
                end=match.end(),
                source=pattern_info["source"],
                line_number=line_number + 1,
                file_path=file_path
            ))

    return spans


def scan_file(file_path: str, content: Optional[str] = None) -> ScanResult:
    """Scan a single file for privacy-sensitive content."""
    if content is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    spans = scan_text(content, file_path)

    spans_by_type = {}
    for span in spans:
        if span.source not in spans_by_type:
            spans_by_type[span.source] = 0
        spans_by_type[span.source] += 1

    return ScanResult(
        file_path=file_path,
        total_spans=len(spans),
        spans_by_type=spans_by_type,
        spans=spans
    )


def scan_directory(directory: str, pattern: str = "*.md") -> list[ScanResult]:
    """Scan all markdown files in a directory."""
    results = []
    path = Path(directory)

    for md_file in path.rglob(pattern):
        if md_file.is_file():
            try:
                result = scan_file(str(md_file))
                results.append(result)
            except Exception as e:
                print(f"Error scanning {md_file}: {e}", file=sys.stderr)

    return results


def format_span_preview(text: str, span: PrivacySpan, context_chars: int = 30) -> str:
    """Get a preview of the span with surrounding context."""
    start = max(0, span.start - context_chars)
    end = min(len(text), span.end + context_chars)

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""

    return f"{prefix}{text[start:span.start]}[{span.text}]{text[span.end:end]}{suffix}"


def print_report(results: list[ScanResult], show_details: bool = False, show_preview: bool = True):
    """Print a formatted report of scan results."""
    total_files = len(results)
    files_with_issues = sum(1 for r in results if r.total_spans > 0)
    total_spans = sum(r.total_spans for r in results)

    print("\n" + "=" * 70)
    print("PRIVACY SCAN REPORT")
    print("=" * 70)
    print(f"\nTotal files scanned: {total_files}")
    print(f"Files with potential privacy issues: {files_with_issues}")
    print(f"Total detections: {total_spans}")

    if total_spans == 0:
        print("\nNo privacy-sensitive content detected. ✓")
        return

    print("\n" + "-" * 70)
    print("SUMMARY BY TYPE")
    print("-" * 70)

    all_types = {}
    for result in results:
        for source, count in result.spans_by_type.items():
            if source not in all_types:
                all_types[source] = {"count": 0, "files": set()}
            all_types[source]["count"] += count
            all_types[source]["files"].add(result.file_path)

    for source, info in sorted(all_types.items(), key=lambda x: x[1]["count"], reverse=True):
        desc = PATTERN_DESCRIPTIONS.get(source, source)
        print(f"\n{source.upper()} ({desc})")
        print(f"  Detections: {info['count']}")
        print(f"  Files: {len(info['files'])}")

    if show_details:
        print("\n" + "-" * 70)
        print("DETAILED FINDINGS")
        print("-" * 70)

        for result in results:
            if result.total_spans == 0:
                continue

            print(f"\n📄 {result.file_path}")
            print(f"   Total detections: {result.total_spans}")

            if show_preview:
                with open(result.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                for span in result.spans:
                    preview = format_span_preview(content, span)
                    print(f"\n   Line {span.line_number} [{span.source}]:")
                    print(f"   {preview}")


def mark_in_file(result: ScanResult, output_suffix: str = "_marked.md"):
    """Create a copy of the file with privacy content marked."""
    if result.total_spans == 0:
        return

    input_path = Path(result.file_path)
    output_path = input_path.parent / f"{input_path.stem}{output_suffix}"

    with open(result.file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    marked_lines = []

    for line_num, line in enumerate(lines, 1):
        line_spans = [s for s in result.spans if s.line_number == line_num]

        if not line_spans:
            marked_lines.append(line)
            continue

        line_spans.sort(key=lambda x: x.start)

        new_line = ""
        last_end = 0

        for span in line_spans:
            local_start = span.start - sum(len(l) + 1 for l in lines[:line_num - 1])
            local_end = span.end - sum(len(l) + 1 for l in lines[:line_num - 1])

            local_start = max(0, local_start)
            local_end = min(len(line), local_end)

            if local_start < last_end:
                local_start = last_end

            new_line += line[last_end:local_start]
            marker = f"<!-- PRIVACY: {span.source} -->"
            new_line += f"{marker}{line[local_start:local_end]}{marker}"
            last_end = local_end

        new_line += line[last_end:]
        marked_lines.append(new_line)

    marked_content = '\n'.join(marked_lines)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(marked_content)

    print(f"Marked file saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Scan markdown files for privacy-sensitive content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python privacy_scanner.py ./docs
  python privacy_scanner.py ./docs --details
  python privacy_scanner.py ./docs --mark
  python privacy_scanner.py ./docs -o report.txt
        """
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="Directory to scan (default: current directory)"
    )

    parser.add_argument(
        "-d", "--details",
        action="store_true",
        help="Show detailed findings with line numbers"
    )

    parser.add_argument(
        "-p", "--no-preview",
        action="store_true",
        help="Hide context preview in detailed output"
    )

    parser.add_argument(
        "-m", "--mark",
        action="store_true",
        help="Create marked copies of files with privacy content"
    )

    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save report to file"
    )

    parser.add_argument(
        "-s", "--suffix",
        default="_marked.md",
        help="Suffix for marked files (default: _marked.md)"
    )

    args = parser.parse_args()

    results = scan_directory(args.directory)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            original_stdout = sys.stdout
            sys.stdout = f
            print_report(results, args.details, not args.no_preview)
            sys.stdout = original_stdout
        print(f"Report saved to: {args.output}")
    else:
        print_report(results, args.details, not args.no_preview)

    if args.mark:
        for result in results:
            if result.total_spans > 0:
                mark_in_file(result, args.suffix)

    total_issues = sum(r.total_spans for r in results)
    if total_issues > 0 and not args.mark:
        print("\n" + "=" * 70)
        print(f"⚠️  Found {total_issues} potential privacy issue(s)")
        print("   Use --mark to create marked copies or review details above")
        print("=" * 70)


if __name__ == "__main__":
    main()
