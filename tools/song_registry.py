#!/usr/bin/env python3
"""Decode Vividstasis VSD v1 song_information.bin without altering game files."""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
try:
    from verify_vsb_signatures import PUBLIC_MODULUS, PUBLIC_EXPONENT, SIGNATURE_BYTES, ENCODED_PREFIX
except ModuleNotFoundError:
    from tools.verify_vsb_signatures import PUBLIC_MODULUS, PUBLIC_EXPONENT, SIGNATURE_BYTES, ENCODED_PREFIX

FIELD_SCHEMA = [
    ("song_id", 0xB2), ("name", 0xB8), ("formatted_name", 0xB8),
    ("artist", 0xB8), ("chart_id", 0xB8), ("bpm_display", 0xB8),
    ("version", 0xB8), ("has_encore", 0xB7), ("is_original", 0xB7),
    ("jacket_artist", 0xB8), ("is_published", 0xB7),
]
VALUE_FORMATS = {0xB0: "B", 0xB1: "b", 0xB2: "I", 0xB3: "i", 0xB5: "e", 0xB6: "f", 0xB7: "?", 0xB8: "string"}
DEFAULTS = dict(song_id=0, name="N/A", formatted_name="N/A", artist="N/A", chart_id="generic", bpm_display="120", version="9.9.9", has_encore=False, is_original=False, is_published=False, jacket_artist="N/A")
for _i in range(1, 5):
    DEFAULTS.update({f"difficulty_constant_{_i}": 0, f"difficulty_display_{_i}": "0", f"note_designer_{_i}": "N/A"})

class RegistryError(ValueError):
    pass

class Reader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
    def take(self, count):
        if self.pos + count > len(self.data):
            raise RegistryError(f"0x{self.pos:X}: truncated {count}-byte value")
        result = self.data[self.pos:self.pos + count]
        self.pos += count
        return result
    def value(self, fmt):
        if fmt == "string":
            end = self.data.find(b"\0", self.pos)
            if end < 0:
                raise RegistryError(f"0x{self.pos:X}: unterminated string")
            return self.take(end - self.pos + 1)[:-1].decode("utf-8", errors="surrogateescape")
        return struct.unpack("<" + fmt, self.take(struct.calcsize("<" + fmt)))[0]
    def byte(self):
        return self.value("B")


def parse_registry(data: bytes) -> dict:
    r = Reader(data)
    if r.take(5) != b"VSD\x01\0":
        raise RegistryError("Expected VSD version1 reserved0 header")
    records = []
    while True:
        offset = r.pos
        tag = r.byte()
        if tag == 0xFF:
            break
        if tag != 0xA0:
            raise RegistryError(f"0x{offset:X}: expected song start A0 or end FF, found {tag:02X}")
        entries = []
        fields = {}
        charts = []
        while True:
            field_at = r.pos
            tag = r.byte()
            if tag == 0xA1:
                break
            if tag == 0xA2:
                kind = r.byte()
                field_id = r.byte()
                if kind not in VALUE_FORMATS or field_id >= len(FIELD_SCHEMA):
                    raise RegistryError(f"0x{field_at:X}: unknown field type or id {kind:02X}/{field_id}")
                value = r.value(VALUE_FORMATS[kind])
                name = FIELD_SCHEMA[field_id][0]
                entries.append(dict(offset=field_at, tag=tag, type=kind, field_id=field_id, name=name, value=value))
                fields[name] = bool(value) if kind == 0xB7 else value
            elif tag == 0xC0:
                chart = dict(stored_difficulty_display=r.value("string"), difficulty_constant=r.value("f"), note_designer=r.value("string"))
                # The game discards stored display and computes floor(constant), adding + when round(constant*10)%10 >= 5.
                constant = chart["difficulty_constant"]
                if math.isfinite(constant):
                    chart["derived_difficulty_display"] = str(math.floor(constant)) + ("+" if math.floor(constant * 10 + 0.5) % 10 >= 5 else "")
                charts.append(chart)
                entries.append(dict(offset=field_at, tag=tag, chart=chart))
            else:
                raise RegistryError(f"0x{field_at:X}: unknown song field tag {tag:02X}")
        effective = dict(DEFAULTS)
        effective.update(fields)
        for i, chart in enumerate(charts, 1):
            effective.update({f"difficulty_constant_{i}": chart["difficulty_constant"], f"difficulty_display_{i}": chart.get("derived_difficulty_display"), f"note_designer_{i}": chart["note_designer"]})
        records.append(dict(offset=offset, fields=fields, charts=charts, entries=entries, effective_fields=effective))
    payload_end = r.pos
    return dict(header="5653440100", songs=records, payload_end=payload_end, trailer_bytes=len(data)-payload_end, trailer_hex=data[payload_end:].hex())


def encode_registry(registry: dict) -> bytes:
    """Losslessly re-encode preserved entries and original signature; does not sign changes."""
    out = bytearray.fromhex(registry["header"])
    def put(fmt, value):
        out.extend(value.encode("utf-8", errors="surrogateescape") + b"\0" if fmt == "string" else struct.pack("<" + fmt, value))
    for song in registry["songs"]:
        out.append(0xA0)
        for entry in song["entries"]:
            out.append(entry["tag"])
            if entry["tag"] == 0xA2:
                out.extend((entry["type"], entry["field_id"]))
                put(VALUE_FORMATS[entry["type"]], entry["value"])
            else:
                chart = entry["chart"]
                put("string", chart["stored_difficulty_display"])
                put("f", chart["difficulty_constant"])
                put("string", chart["note_designer"])
        out.append(0xA1)
    out.append(0xFF)
    out.extend(bytes.fromhex(registry["trailer_hex"]))
    return bytes(out)


def inventory(path: Path, assets: Path | None = None) -> dict:
    raw = path.read_bytes()
    registry = parse_registry(raw)
    if encode_registry(registry) != raw:
        raise RegistryError("Registry byte-for-byte round-trip failed")
    signature_status = "unsigned"
    if registry["trailer_bytes"] == SIGNATURE_BYTES:
        signed = int.from_bytes(raw[registry["payload_end"]:], "big")
        encoded = pow(signed, PUBLIC_EXPONENT, PUBLIC_MODULUS).to_bytes(SIGNATURE_BYTES, "big")
        signature_status = "valid" if signed < PUBLIC_MODULUS and encoded == ENCODED_PREFIX + hashlib.sha1(raw[:registry["payload_end"]]).digest() else "invalid"
    elif registry["trailer_bytes"]:
        signature_status = "unexpected_trailer_size"
    ids = [s["effective_fields"]["song_id"] for s in registry["songs"]]
    chart_ids = [s["effective_fields"]["chart_id"] for s in registry["songs"]]
    if assets and assets.exists():
        with assets.open() as f:
            asset_rows = list(csv.DictReader(f))
        asset_sets = {category: {row["name"] for row in asset_rows if row["category"] == category} for category in ("Sprites", "Sounds")}
        for song in registry["songs"]:
            chart_id = song["effective_fields"]["chart_id"]
            song["expected_assets"] = {
                kind: dict(name=name, exists=name in asset_sets[category])
                for kind, name, category in [
                    ("audio", "music_chart_" + chart_id, "Sounds"),
                    ("jacket", "song_" + chart_id, "Sprites"),
                    ("preview", "preview_" + chart_id, "Sounds"),
                ]
            }
    registry.update(source=str(path), source_bytes=len(raw), source_sha256=hashlib.sha256(raw).hexdigest(), byte_identical_roundtrip=True, signature_status=signature_status, song_count=len(ids), minimum_song_id=min(ids), maximum_song_id=max(ids), duplicate_song_ids={str(k):v for k,v in collections.Counter(ids).items() if v>1}, duplicate_chart_ids={str(k):v for k,v in collections.Counter(chart_ids).items() if v>1}, chart_record_counts=dict(collections.Counter(len(s["charts"]) for s in registry["songs"])), field_presence=dict(collections.Counter(k for s in registry["songs"] for k in s["fields"])), published_count=sum(bool(s["effective_fields"]["is_published"]) for s in registry["songs"]), schema=[dict(id=i,name=name,type=kind,encoding=VALUE_FORMATS[kind]) for i,(name,kind) in enumerate(FIELD_SCHEMA)])
    registry["generic_defaults"] = DEFAULTS
    registry["chart_slot_filenames"] = {"1":"OPENING.vsb","2":"MIDDLE.vsb","3":"FINALE.vsb","4":"ENCORE.vsb"}
    registry["registration_notes"] = [
        "Registry reader starts each record from getGenericSong(0); fields can be absent, but adding a song safely needs a unique song_id and chart_id with matching assets/charts.",
        "All existing records have all 11 schema fields and four chart records. The writer emits four chart records; the reader accepts a variable number.",
        "Stored difficulty_display is read but replaced by floor(constant), adding + if round(constant*10)%10>=5. The decoder derived display is corpus-equivalent; synthetic exact rounding ties are not established by static inspection.",
        "Main song audio resolves an embedded GameMaker asset named music_chart_<chart_id>; a missing asset stays -1. Jacket and preview use song_<chart_id> and preview_<chart_id>, with generic fallback.",
        "All Songs is a union of configured song packs, not an automatic registry scan. A new registry record needs pack inclusion to appear normally.",
        "IDs3..183 are initially added to global.valid_song_ids. Hardcoded unlock registration adds others; a new ID outside these lists needs additional integration for daily/valid-song selection.",
        "Only the current build's rsa_verify wrapper bypasses verification; changed unsigned registries should not be assumed portable to builds enforcing signatures.",
        "Reencoding preserves original signatures and is useful for roundtrip validation; changing content invalidates an existing signature. This tool does not sign or modify game files.",
    ]
    registry["evidence"] = [
        "extraction/main/CodeEntries/gml_GlobalScript_vsd_enums.gml:1",
        "extraction/main/CodeEntries/gml_GlobalScript_v1_vsd_reader.gml:22",
        "extraction/main/CodeEntries/gml_GlobalScript_v1_vsd_writer.gml:23",
        "extraction/main/CodeEntries/gml_GlobalScript_load_song_information.gml:133",
        "extraction/main/CodeEntries/gml_GlobalScript_create_song_packs.gml:360",
        "extraction/main/CodeEntries/gml_GlobalScript_chart_sign.gml:44",
    ]
    return registry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", nargs="?", type=Path, default=Path("vividstasis/song_information.bin"))
    parser.add_argument("--assets", type=Path, default=Path("extraction/main/metadata/asset_index.csv"))
    parser.add_argument("--output", type=Path, default=Path("analysis/chart_registration/registry_inventory.json"))
    args = parser.parse_args()
    report = inventory(args.registry, args.assets)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n")
    print(json.dumps({k:report[k] for k in ("song_count","minimum_song_id","maximum_song_id","duplicate_song_ids","duplicate_chart_ids","chart_record_counts","signature_status","byte_identical_roundtrip")}, indent=2))

if __name__ == "__main__":
    main()
