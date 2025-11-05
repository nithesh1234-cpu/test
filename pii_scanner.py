#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Tuple

# Optional import for PDF parsing; we'll handle absence gracefully
try:
    from pypdf import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore


@dataclass
class Finding:
    file_path: str
    pii_type: str
    match_text: str
    start: int
    end: int
    line: int
    context: str


class PIIScanner:
    EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

    PHONE_REGEX = re.compile(
        r"(?<!\d)(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})(?!\d)"
    )

    SSN_REGEX = re.compile(r"(?<!\d)(?:\d{3}-\d{2}-\d{4}|\d{9})(?!\d)")

    DOB_REGEX = re.compile(
        r"(?:(?P<ymd>\b\d{4}[-/.]\d{2}[-/.]\d{2}\b)|(?P<mdy>\b\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b))",
    )

    # Potential credit card candidates (digits with optional separators, 13-19 length)
    CC_CANDIDATE = re.compile(
        r"(?<!\d)(?:\d[ -]?){12,19}\d(?!\d)"
    )

    def __init__(self) -> None:
        pass

    @staticmethod
    def _luhn_checksum_is_valid(number: str) -> bool:
        digits = [int(d) for d in number if d.isdigit()]
        if len(digits) < 13 or len(digits) > 19:
            return False
        checksum = 0
        parity = (len(digits) - 2) % 2
        for i, d in enumerate(digits):
            if i % 2 == parity:
                d = d * 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    @staticmethod
    def _card_brand_plausible(digits: str) -> bool:
        """Heuristic brand/length checks to reduce false positives for credit cards."""
        n = len(digits)
        if n < 13 or n > 19:
            return False

        # Visa: 4, length 13/16/19
        if digits.startswith("4") and n in (13, 16, 19):
            return True

        # MasterCard: 51-55 or 2221-2720, length 16
        if n == 16 and (
            digits.startswith(("51", "52", "53", "54", "55"))
            or (len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720)
        ):
            return True

        # American Express: 34 or 37, length 15
        if n == 15 and digits.startswith(("34", "37")):
            return True

        # Discover: 6011, 65, 644-649, length 16/19
        if n in (16, 19):
            if digits.startswith("6011") or digits.startswith("65"):
                return True
            if len(digits) >= 3:
                p3 = int(digits[:3])
                if 644 <= p3 <= 649:
                    return True

        # JCB: 3528-3589, length 16/19
        if n in (16, 19) and len(digits) >= 4:
            p4 = int(digits[:4])
            if 3528 <= p4 <= 3589:
                return True

        # Diners Club: 300-305, 36, 38-39; length 14
        if n == 14:
            if len(digits) >= 3 and 300 <= int(digits[:3]) <= 305:
                return True
            if digits.startswith("36") or digits.startswith("38") or digits.startswith("39"):
                return True

        return False

    @staticmethod
    def _mask_value(pii_type: str, value: str) -> str:
        if pii_type in {"ssn", "credit_card", "phone"}:
            digits = [c for c in value if c.isdigit()]
            if len(digits) <= 4:
                return value
            masked = "".join(digits[:-4])
            masked = ("*" * len(masked)) + "".join(digits[-4:])
            # reinsert non-digits from original at roughly same positions when possible
            out = []
            di = 0
            for c in value:
                if c.isdigit():
                    out.append(masked[di])
                    di += 1
                else:
                    out.append(c)
            return "".join(out)
        if pii_type == "email":
            try:
                local, domain = value.split("@", 1)
                if len(local) <= 2:
                    masked_local = "*" * len(local)
                else:
                    masked_local = local[0] + ("*" * (len(local) - 2)) + local[-1]
                return f"{masked_local}@{domain}"
            except Exception:
                return value
        return value

    @staticmethod
    def _build_line_index(text: str) -> List[int]:
        # Returns list of starting offsets for each line
        starts = [0]
        for m in re.finditer("\n", text):
            starts.append(m.end())
        return starts

    @staticmethod
    def _offset_to_line(starts: List[int], offset: int) -> int:
        # Binary search for line number (1-based)
        lo, hi = 0, len(starts) - 1
        if not starts:
            return 1
        if offset < starts[0]:
            return 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if starts[mid] <= offset:
                lo = mid + 1
            else:
                hi = mid - 1
        return hi + 1

    def scan_text(self, text: str, source: str) -> List[Finding]:
        results: List[Finding] = []
        line_starts = self._build_line_index(text)

        def add(pii_type: str, m: re.Match[str]) -> None:
            start, end = m.start(), m.end()
            ln = self._offset_to_line(line_starts, start)
            context_start = max(0, start - 40)
            context_end = min(len(text), end + 40)
            context = text[context_start:context_end].replace("\n", " ⏎ ")
            masked = self._mask_value(pii_type, m.group(0))
            results.append(
                Finding(
                    file_path=source,
                    pii_type=pii_type,
                    match_text=masked,
                    start=start,
                    end=end,
                    line=ln,
                    context=context,
                )
            )

        for m in self.EMAIL_REGEX.finditer(text):
            add("email", m)
        for m in self.PHONE_REGEX.finditer(text):
            add("phone", m)
        for m in self.SSN_REGEX.finditer(text):
            # avoid false positives inside longer digit runs
            add("ssn", m)
        for m in self.DOB_REGEX.finditer(text):
            add("date", m)
        for m in self.CC_CANDIDATE.finditer(text):
            raw = m.group(0)
            digits_only = re.sub(r"[^0-9]", "", raw)
            if self._luhn_checksum_is_valid(digits_only) and self._card_brand_plausible(digits_only):
                if not re.match(r"^0+$", digits_only):
                    add("credit_card", m)
        return results


def read_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def read_json_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            data = json.load(f)
    except Exception:
        # Fallback: return raw text if not valid JSON
        return read_text_file(path)

    def flatten(obj) -> Iterable[str]:
        if obj is None:
            return []
        if isinstance(obj, (str, int, float, bool)):
            return [str(obj)]
        if isinstance(obj, dict):
            out: List[str] = []
            for k, v in obj.items():
                out.extend([str(k)])
                out.extend(flatten(v))
            return out
        if isinstance(obj, list):
            out: List[str] = []
            for item in obj:
                out.extend(flatten(item))
            return out
        return [str(obj)]

    return "\n".join(flatten(data))


def read_pdf_text(path: str) -> str:
    if PdfReader is None:
        raise RuntimeError(
            "pypdf not available. Install with: python -m pip install pypdf"
        )
    reader = PdfReader(path)
    parts: List[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            # Continue on extraction errors per page
            continue
    return "\n".join(parts)


def detect_loader(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith(".json"):
        return "json"
    return "text"


def load_text_for_path(path: str) -> str:
    loader = detect_loader(path)
    if loader == "pdf":
        return read_pdf_text(path)
    if loader == "json":
        return read_json_text(path)
    return read_text_file(path)


def summarize_findings(findings: List[Finding]) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}
    for f in findings:
        summary.setdefault(f.file_path, {})
        summary[f.file_path][f.pii_type] = summary[f.file_path].get(f.pii_type, 0) + 1
    return summary


def write_reports(
    all_findings: List[Finding],
    out_dir: str,
) -> Tuple[str, str]:
    os.makedirs(out_dir, exist_ok=True)

    # JSON report
    json_path = os.path.join(out_dir, "pii_report.json")
    by_file: Dict[str, List[Dict]] = {}
    for f in all_findings:
        by_file.setdefault(f.file_path, []).append(asdict(f))
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(by_file, jf, indent=2, ensure_ascii=False)

    # Markdown summary
    md_path = os.path.join(out_dir, "pii_report.md")
    summary = summarize_findings(all_findings)
    lines: List[str] = []
    lines.append("# PII/PHI Scan Summary\n")
    if not summary:
        lines.append("No PII/PHI detections.\n")
    else:
        for file_path, counts in summary.items():
            lines.append(f"## {file_path}\n")
            lines.append("| Type | Count |\n|---|---|\n")
            for pii_type, count in sorted(counts.items()):
                lines.append(f"| {pii_type} | {count} |\n")
            lines.append("\n")
        # Sample table
        lines.append("## Sample Findings (masked)\n")
        lines.append("| File | Type | Line | Snippet |\n|---|---|---:|---|\n")
        for f in all_findings[:100]:  # cap samples
            snippet = f.context.replace("|", "\\|")
            lines.append(
                f"| {f.file_path} | {f.pii_type} | {f.line} | `{snippet}` |\n"
            )
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write("".join(lines))

    return json_path, md_path


def default_targets(root: str) -> List[str]:
    candidates = [
        os.path.join(root, "dlp_phi_medium_json.json"),
        os.path.join(root, "dlp_phi_small_documents.txt"),
        os.path.join(root, "dlp_pii_large_pdf_file.pdf"),
    ]
    return [p for p in candidates if os.path.exists(p)]


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description="Scan files for PII/PHI patterns")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Files or directories to scan (defaults to known sample files)",
    )
    parser.add_argument(
        "--out-dir",
        default="reports",
        help="Directory to write reports (default: reports)",
    )
    args = parser.parse_args(argv)

    paths: List[str] = []
    if args.paths:
        for p in args.paths:
            if os.path.isdir(p):
                for root, _dirs, files in os.walk(p):
                    for name in files:
                        paths.append(os.path.join(root, name))
            else:
                paths.append(p)
    else:
        paths = default_targets(os.getcwd())

    if not paths:
        print("No input files found.", file=sys.stderr)
        return 2

    scanner = PIIScanner()
    all_findings: List[Finding] = []

    for path in paths:
        try:
            text = load_text_for_path(path)
        except Exception as e:
            print(f"[warn] Failed to read {path}: {e}", file=sys.stderr)
            continue
        findings = scanner.scan_text(text, os.path.relpath(path))
        all_findings.extend(findings)
        print(f"Scanned {path}: {len(findings)} findings")

    json_path, md_path = write_reports(all_findings, args.out_dir)
    print(f"Reports written to: {json_path} and {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
