#!/usr/bin/env python3
"""
Privacy Scanner for Markdown Files
Uses AI model (openai/privacy-filter) + regex patterns for comprehensive privacy detection.
"""

import os
import sys
import argparse
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

warnings.filterwarnings('ignore')

try:
    from transformers import pipeline, AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not installed. Run: pip install transformers torch")
    print("Falling back to regex-only mode.\n")


try:
    import re
except ImportError:
    import regex as re


@dataclass
class PrivacySpan:
    label: str
    text: str
    start: int
    end: int
    source: str
    score: float = 1.0
    line_number: int = 0
    file_path: str = ""


@dataclass
class ScanResult:
    file_path: str
    total_spans: int
    spans_by_type: dict
    spans: list
    uses_model: bool = False


REGEX_PATTERNS = [
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
        "source": "jwt",
        "regex": r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"
    },
    {
        "label": "secret",
        "source": "api_key",
        "regex": r"\b(?:sk-[A-Za-z0-9]{20,}|sk-live-[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36}|gho_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{22,}|glpat-[A-Za-z0-9\-]{20,}|xox[bpors]-[A-Za-z0-9\-]{10,}|AKIA[0-9A-Z]{16}|AIza[A-Za-z0-9_\-]{35}|key-[A-Za-z0-9]{20,})\b"
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

COMPILED_REGEX = [
    {"label": p["label"], "source": p["source"], "regex": re.compile(p["regex"], re.IGNORECASE)}
    for p in REGEX_PATTERNS
]

MODEL_LABELS = {
    "account_number": "Account Number",
    "private_address": "Address",
    "private_email": "Email",
    "private_person": "Person Name",
    "private_phone": "Phone Number",
    "private_url": "URL",
    "private_date": "Date",
    "secret": "Secret/Token"
}

REGEX_DESCRIPTIONS = {
    "iban": "International Bank Account Number",
    "ssn": "US Social Security Number",
    "mac": "MAC Address",
    "ipv4": "IPv4 Address",
    "jwt": "JSON Web Token",
    "api_key": "API Key / Token",
    "btc_wallet": "Bitcoin Wallet Address",
    "eth_wallet": "Ethereum Wallet Address",
    "sol_wallet": "Solana Wallet Address"
}


class PrivacyClassifier:
    def __init__(self, device: Optional[str] = None):
        self.classifier = None
        self.tokenizer = None
        self.device = self._get_device(device)

    def _get_device(self, preferred: Optional[str]) -> str:
        if preferred:
            return preferred

        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except:
            pass

        return "cpu"

    def load(self):
        if not TRANSFORMERS_AVAILABLE:
            return False

        print(f"Loading privacy-filter model on {self.device}...")
        try:
            self.classifier = pipeline(
                "token-classification",
                "openai/privacy-filter",
                device=self.device,
                aggregation_strategy="simple"
            )
            self.tokenizer = AutoTokenizer.from_pretrained("openai/privacy-filter")
            print("Model loaded successfully!")
            return True
        except Exception as e:
            print(f"Failed to load model: {e}")
            print("Falling back to regex-only mode.")
            return False

    def classify_text(self, text: str) -> List[Dict[str, Any]]:
        if not self.classifier:
            return []

        try:
            results = self.classifier(text)
            return results
        except Exception as e:
            print(f"Model inference error: {e}", file=sys.stderr)
            return []

    def normalize_span(self, span: Dict, source: str, search_from: int = 0) -> Optional[Dict]:
        word = span.get("word", "")
        clean_word = word.replace("##", "").strip()

        start = span.get("start", -1)
        end = span.get("end", -1)

        if (start < 0 or end < 0) and clean_word:
            found = source.find(clean_word, search_from)
            if found >= 0:
                start = found
                end = found + len(clean_word)

        if start >= 0 and end > start:
            return {
                "label": span.get("entity_group", span.get("entity", "unknown")),
                "score": span.get("score", 1.0),
                "text": source[start:end],
                "start": start,
                "end": end
            }
        elif clean_word:
            return {
                "label": span.get("entity_group", span.get("entity", "unknown")),
                "score": span.get("score", 1.0),
                "text": clean_word,
                "start": search_from,
                "end": search_from + len(clean_word)
            }
        return None


def regex_scan(text: str) -> List[PrivacySpan]:
    spans = []
    for pattern in COMPILED_REGEX:
        for match in pattern["regex"].finditer(text):
            spans.append(PrivacySpan(
                label=pattern["label"],
                text=match.group(0),
                start=match.start(),
                end=match.end(),
                source=pattern["source"],
                score=1.0
            ))
    return spans


def merge_spans(model_spans: List[Dict], regex_spans: List[PrivacySpan]) -> List[PrivacySpan]:
    all_spans = []

    for span in model_spans:
        all_spans.append(PrivacySpan(
            label=span.get("label", "unknown"),
            text=span.get("text", ""),
            start=span.get("start", 0),
            end=span.get("end", 0),
            source="model",
            score=span.get("score", 1.0)
        ))

    all_spans.extend(regex_spans)

    all_spans.sort(key=lambda x: (x.start, -x.end))

    merged = []
    cursor = -1

    for span in all_spans:
        if span.start >= cursor:
            merged.append(span)
            cursor = span.end
        elif span.end > cursor:
            overlap_ratio = (cursor - span.start) / max(1, span.end - span.start)
            if overlap_ratio < 0.5:
                new_text = span.text[max(0, cursor - span.start):]
                merged.append(PrivacySpan(
                    label=span.label,
                    text=new_text,
                    start=cursor,
                    end=span.end,
                    source=span.source,
                    score=span.score
                ))
                cursor = span.end

    return merged


def scan_text(text: str, classifier: Optional[PrivacyClassifier], file_path: str = "") -> ScanResult:
    lines = text.split('\n')
    line_starts = []
    pos = 0
    for line in lines:
        line_starts.append(pos)
        pos += len(line) + 1

    def get_line_number(char_pos: int) -> int:
        for i, start in enumerate(line_starts):
            if start > char_pos:
                return i
        return len(lines)

    model_spans = []
    regex_spans = regex_scan(text)

    uses_model = False

    if classifier and classifier.classifier:
        raw_results = classifier.classify_text(text)
        search_from = 0
        for span in raw_results:
            normalized = classifier.normalize_span(span, text, search_from)
            if normalized and normalized["text"]:
                model_spans.append(normalized)
                if normalized["end"] > search_from:
                    search_from = normalized["end"]
        uses_model = True

    all_spans = merge_spans(model_spans, regex_spans)

    for span in all_spans:
        span.line_number = get_line_number(span.start)
        span.file_path = file_path

    spans_by_type = {}
    for span in all_spans:
        key = span.source if span.source == "model" else f"regex_{span.source}"
        if key not in spans_by_type:
            spans_by_type[key] = 0
        spans_by_type[key] += 1

    return ScanResult(
        file_path=file_path,
        total_spans=len(all_spans),
        spans_by_type=spans_by_type,
        spans=all_spans,
        uses_model=uses_model
    )


def scan_file(file_path: str, classifier: PrivacyClassifier, content: Optional[str] = None) -> ScanResult:
    if content is None:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    return scan_text(content, classifier, file_path)


def scan_directory(directory: str, classifier: PrivacyClassifier, pattern: str = "*.md") -> List[ScanResult]:
    results = []
    path = Path(directory)

    for md_file in path.rglob(pattern):
        if md_file.is_file():
            try:
                result = scan_file(str(md_file), classifier)
                results.append(result)
            except Exception as e:
                print(f"Error scanning {md_file}: {e}", file=sys.stderr)

    return results


def format_preview(text: str, span: PrivacySpan, context: int = 40) -> str:
    start = max(0, span.start - context)
    end = min(len(text), span.end + context)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:span.start]}[{span.text}]{text[span.end:end]}{suffix}"


def get_label_description(label: str, source: str) -> str:
    if source == "model":
        return MODEL_LABELS.get(label, label.upper())
    else:
        return REGEX_DESCRIPTIONS.get(source, source.upper())


def print_report(results: List[ScanResult], show_details: bool = False):
    total_files = len(results)
    files_with_issues = sum(1 for r in results if r.total_spans > 0)
    total_spans = sum(r.total_spans for r in results)
    model_detections = sum(
        data["count"]
        for r in results
        for key, data in [(k, {"count": v}) for k, v in r.spans_by_type.items()]
        if "model" in key
    )

    print("\n" + "=" * 70)
    print("🔒 PRIVACY SCAN REPORT")
    print("=" * 70)
    print(f"\nTotal files scanned: {total_files}")
    print(f"Files with potential privacy issues: {files_with_issues}")
    print(f"Total detections: {total_spans}")

    if any(r.uses_model for r in results):
        model_count = sum(
            sum(v for k, v in r.spans_by_type.items() if "model" in k)
            for r in results
        )
        regex_count = total_spans - model_count
        print(f"  ├── AI Model detections: {model_count}")
        print(f"  └── Regex pattern detections: {regex_count}")

    if total_spans == 0:
        print("\n✅ No privacy-sensitive content detected!")
        return

    print("\n" + "-" * 70)
    print("SUMMARY BY TYPE")
    print("-" * 70)

    type_stats = {}
    for result in results:
        for key, count in result.spans_by_type.items():
            is_model = "model" in key
            source_type = "model" if is_model else key.replace("regex_", "")

            if source_type not in type_stats:
                type_stats[source_type] = {"count": 0, "model": 0, "regex": 0, "files": set()}

            type_stats[source_type]["count"] += count
            type_stats[source_type]["files"].add(result.file_path)
            if is_model:
                type_stats[source_type]["model"] += count
            else:
                type_stats[source_type]["regex"] += count

    for source_type, stats in sorted(type_stats.items(), key=lambda x: x[1]["count"], reverse=True):
        desc = get_label_description("", source_type)
        badges = []
        if stats["model"] > 0:
            badges.append(f"🤖 AI: {stats['model']}")
        if stats["regex"] > 0:
            badges.append(f"📐 Regex: {stats['regex']}")

        print(f"\n{source_type.upper()} ({desc})")
        print(f"  Total: {stats['count']} | Files: {len(stats['files'])}")
        print(f"  {' | '.join(badges)}")

    if show_details:
        print("\n" + "-" * 70)
        print("DETAILED FINDINGS")
        print("-" * 70)

        for result in results:
            if result.total_spans == 0:
                continue

            print(f"\n📄 {result.file_path}")
            print(f"   Total detections: {result.total_spans}")

            with open(result.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            for span in result.spans:
                source_icon = "🤖" if span.source == "model" else "📐"
                desc = get_label_description(span.label, span.source)
                preview = format_preview(content, span)

                print(f"\n   {source_icon} Line {span.line_number} [{desc}]")
                print(f"   {preview}")


def main():
    parser = argparse.ArgumentParser(
        description="Privacy Scanner - AI-powered detection for sensitive content in markdown files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python privacy_scanner.py ./docs
  python privacy_scanner.py ./docs --details
  python privacy_scanner.py ./docs --device cuda
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
        "--device",
        choices=["cpu", "cuda", "mps"],
        help="Device for model inference (auto-detected if not specified)"
    )

    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Save report to file"
    )

    args = parser.parse_args()

    classifier = PrivacyClassifier(device=args.device)

    if TRANSFORMERS_AVAILABLE:
        classifier.load()
    else:
        print("⚠️  Running in REGEX-ONLY mode (transformers not installed)")
        print("   Install with: pip install transformers torch\n")

    results = scan_directory(args.directory, classifier)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            original_stdout = sys.stdout
            sys.stdout = f
            print_report(results, args.details)
            sys.stdout = original_stdout
        print(f"Report saved to: {args.output}")
    else:
        print_report(results, args.details)

    total_issues = sum(r.total_spans for r in results)
    if total_issues > 0:
        print("\n" + "=" * 70)
        print(f"⚠️  Found {total_issues} potential privacy issue(s)")
        print("=" * 70)


if __name__ == "__main__":
    main()
