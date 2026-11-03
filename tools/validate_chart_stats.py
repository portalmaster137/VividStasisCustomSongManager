#!/usr/bin/env python3
"""Audit Vividstasis .stats INI cache files without modifying chart data."""
from __future__ import annotations
import argparse
import collections
import configparser
import hashlib
import json
from pathlib import Path


def validate(root: Path) -> dict:
    records = []
    key_presence = collections.Counter()
    sections = collections.Counter()
    stale = []
    orphan = []
    errors = []
    for path in sorted(root.rglob("*.stats")):
        ini = configparser.ConfigParser(interpolation=None)
        ini.optionxform = str
        try:
            ini.read_string(path.read_text(encoding="utf-8-sig"))
            sections.update(ini.sections())
            values = dict(ini.items("stats"))
            key_presence.update(values.keys())
            # GameMaker quotes string and real INI values.
            checksum = values.get("checksum", "").strip('"')
            sibling = path.with_suffix(".vsb")
            actual = hashlib.sha1(sibling.read_bytes()).hexdigest() if sibling.exists() else None
            row = dict(
                path=str(path.relative_to(root)),
                bytes=path.stat().st_size,
                keys=list(values),
                cached_checksum=checksum,
                chart_sha1=actual,
                status="orphan" if actual is None else "matched" if checksum == actual else "stale",
            )
            records.append(row)
            if row["status"] == "orphan":
                orphan.append(row["path"])
            elif row["status"] == "stale":
                stale.append(row["path"])
        except (OSError, UnicodeError, configparser.Error) as error:
            errors.append(dict(path=str(path.relative_to(root)), error=str(error)))
    missing = [
        str(path.relative_to(root)) for path in sorted(root.rglob("*.vsb"))
        if not path.with_suffix(".stats").exists()
    ]
    return dict(
        method="Parse plain INI [stats]; compare checksum against SHA-1 of the entire sibling .vsb, including signature trailer",
        chart_count=sum(1 for _ in root.rglob("*.vsb")),
        stats_count=len(records),
        counts=dict(collections.Counter(row["status"] for row in records)),
        section_presence=dict(sections),
        key_presence=dict(sorted(key_presence.items())),
        missing_stats_for_charts=missing,
        orphan_stats=orphan,
        stale_stats=stale,
        errors=errors,
        files=records,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("charts", nargs="?", type=Path, default=Path("vividstasis/Charts"))
    parser.add_argument("--output", type=Path, default=Path("analysis/chart_format/stats_validation.json"))
    args = parser.parse_args()
    report = validate(args.charts)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k in ("chart_count", "stats_count", "counts", "key_presence", "missing_stats_for_charts", "orphan_stats", "errors")}, indent=2))
    if report["errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
