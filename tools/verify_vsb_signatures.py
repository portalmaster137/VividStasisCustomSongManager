#!/usr/bin/env python3
"""Verify VSB RSA trailers using only Python's standard library.

The fixed public modulus comes from the extracted game's rsa_verify wrapper.
This tool does not sign files, alter charts, or require private key material.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path

try:
    from vsb import parse_chart
except ModuleNotFoundError:
    from tools.vsb import parse_chart

PUBLIC_MODULUS = int(
    "4087966337962722934016728373929954736911054268340290529718840403152381802449888346105429852424107746132591382090681618505600090563880520343659326344144081754767820449572095395735609339190867582498239351112700454340174266240306915532865730737700937023273316512201852193092848735659991098335550058987389902744138993370187109674688602220616550429190371617718469944750231838931021340649708625720099359930363371306184708512452382562266870574235957050890058978540898926879156480030954345055309039385471595968562995762819631280551603822874246284493346689033984936977482360320788049616621145392393928330228382874172082440289259049272547327070384017027740526865779790246622942927212687995907573512992024572752906193469726690570592323041441474712576330726229741449831409379198722634050167222736564950170077459202587882952456318580615189706952925518026801158664284712656280067439912216671693199268965961613231362525782754244074362083059"
)
PUBLIC_EXPONENT = 17
SIGNATURE_BYTES = 384
# RSASSA-PKCS1-v1_5 with SHA-1: 00 01 PS 00 DigestInfo(SHA-1, digest).
SHA1_DIGEST_INFO_PREFIX = bytes.fromhex("3021300906052b0e03021a05000414")
ENCODED_PREFIX = b"\x00\x01" + b"\xff" * (
    SIGNATURE_BYTES - 3 - len(SHA1_DIGEST_INFO_PREFIX) - 20
) + b"\x00" + SHA1_DIGEST_INFO_PREFIX


def verify(path: Path, root: Path) -> dict:
    data = path.read_bytes()
    row = {
        "path": str(path.relative_to(root)),
        "file_bytes": len(data),
        "file_sha256": hashlib.sha256(data).hexdigest(),
        "last_byte_is_chart_terminator": data[-1:] == b"\xff",
    }
    chart = parse_chart(data)
    row.update(structural_payload_end=chart["payload_end"], structural_trailer_bytes=chart["trailer_bytes"])
    if chart["trailer_bytes"] == 0:
        row["status"] = "unsigned"
        return row
    if chart["trailer_bytes"] != SIGNATURE_BYTES:
        row["status"] = "unexpected_structural_trailer_length"
        return row
    if len(data) < SIGNATURE_BYTES:
        row["status"] = "too_short_for_signature_candidate"
        return row
    offset = len(data) - SIGNATURE_BYTES
    candidate = int.from_bytes(data[offset:], "big")
    encoded = pow(candidate, PUBLIC_EXPONENT, PUBLIC_MODULUS).to_bytes(SIGNATURE_BYTES, "big")
    digest = hashlib.sha1(data[:offset]).digest()
    row.update(
        candidate_signature_offset=offset,
        candidate_preceded_by_chart_terminator=data[offset - 1:offset] == b"\xff",
        candidate_signature_is_less_than_modulus=candidate < PUBLIC_MODULUS,
        candidate_payload_sha1=digest.hex(),
    )
    if candidate >= PUBLIC_MODULUS or not encoded.startswith(ENCODED_PREFIX):
        row["status"] = "no_valid_rsa_sha1_envelope_at_eof_minus_384"
    elif encoded[-20:] != digest:
        row["status"] = "valid_rsa_envelope_digest_mismatch"
        row["signed_sha1"] = encoded[-20:].hex()
    else:
        row["status"] = "valid"
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("charts", nargs="?", type=Path, default=Path("vividstasis/Charts"))
    parser.add_argument("--output", type=Path, default=Path("analysis/chart_format/crypto_validation.json"))
    args = parser.parse_args()
    paths = sorted(args.charts.rglob("*.vsb")) if args.charts.is_dir() else [args.charts]
    root = args.charts if args.charts.is_dir() else args.charts.parent
    records = [verify(path, root) for path in paths]
    report = {
        "method": "RSA-3072, public exponent 17, big-endian 384-byte candidate trailer, PKCS#1 v1.5 SHA-1",
        "coverage": "Structural VSC parsing locates the final FF terminator. Zero-byte trailers are unsigned; exactly 384-byte trailers are verified cryptographically.",
        "counts": dict(collections.Counter(row["status"] for row in records)),
        "files": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["counts"], indent=2))


if __name__ == "__main__":
    main()
