#!/usr/bin/env python3
"""Convert a 6K osu!mania .osu beatmap into an unsigned VSC v1 .vsb."""
import argparse
import math
from pathlib import Path
import sys
from vsb import encode_chart


def convert(text, bumper_holds='reject'):
    sections = {}
    section = None
    lines = text.lstrip('\ufeff').splitlines()
    if not lines or not lines[0].startswith('osu file format v'):
        raise ValueError('Expected an osu file format header')
    for number, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('//'):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
        elif section:
            sections.setdefault(section, []).append((number, line))
    def settings(name):
        return dict(line.split(':', 1) for _, line in sections.get(name, []) if ':' in line)
    if settings('General').get('Mode', '').strip() != '3':
        raise ValueError('Only osu!mania (Mode: 3) is supported')
    if float(settings('Difficulty').get('CircleSize', '0')) != 6:
        raise ValueError('Expected exactly six keys (CircleSize: 6)')
    notes = []
    def finite(value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError('Nonfinite timestamp or timing value')
        return value
    def add(kind, lane, time, extra=None):
        fields = [dict(tag=0xA2, value=kind), dict(tag=0xA3, value=lane),
                  dict(tag=0xA4, value=time)]
        if extra is not None:
            fields.append(dict(tag=0xA6, entries=[dict(tag=0xB6, id=1, value=extra)]))
        notes.append(dict(fields=fields))
    bpms = []
    for number, line in sections.get('TimingPoints', []):
        try:
            fields = line.split(',')
            time, length = finite(fields[0]), finite(fields[1])
            if len(fields) < 7 or int(fields[6]) == 1:
                if length <= 0:
                    raise ValueError('Uninherited beat length must be positive')
                bpm = 60000 / length
                bpms.append((time, bpm))
                add(3, 0, time, bpm)
        except (ValueError, IndexError) as exc:
            raise ValueError(f'Line {number}: {exc}') from exc
    if not bpms:
        raise ValueError('No uninherited BPM timing points found')
    for number, line in sections.get('HitObjects', []):
        try:
            fields = line.split(',')
            x, time, flags = int(fields[0]), finite(fields[2]), int(fields[3])
            if not 0 <= x <= 512:
                raise ValueError('X coordinate must be between 0 and 512')
            column = min(5, x * 6 // 512)
            hold = bool(flags & 128)
            if not hold and not flags & 1:
                raise ValueError('Unsupported hit object type')
            end = finite(fields[5].split(':')[0]) if hold else None
            if hold and end < time:
                raise ValueError('Hold end precedes start')
            if column in (0, 5):
                if hold and bumper_holds == 'reject':
                    raise ValueError('Bumper hold: select --bump-start or --bump-both')
                lane = 0 if column == 0 else 2
                add(1, lane, time)
                if hold and bumper_holds == 'both':
                    add(1, lane, end)
            else:
                add(2 if hold else 0, column - 1, time, end)
        except (ValueError, IndexError) as exc:
            raise ValueError(f'Line {number}: {exc}') from exc
    if not sections.get('HitObjects'):
        raise ValueError('No hit objects found')
    notes.sort(key=lambda note: (note['fields'][2]['value'], note['fields'][0]['value'] != 3))
    data = encode_chart(dict(header='5653430100', blocks=[dict(tag=0xC0, notes=notes)], trailer_hex=''))
    return data, sorted(bpms)[0][1], len(notes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--bump-start', dest='bumper_holds', action='store_const', const='start', help='Convert bumper holds to start taps')
    group.add_argument('--bump-both', dest='bumper_holds', action='store_const', const='both', help='Convert bumper holds to start and end taps')
    group.add_argument('--reject-bump-holds', dest='bumper_holds', action='store_const', const='reject', help='Reject bumper holds (default)')
    parser.set_defaults(bumper_holds='reject')
    parser.add_argument('--force', action='store_true', help='Overwrite an existing output')
    args = parser.parse_args()
    try:
        data, bpm, count = convert(args.input.read_text(encoding='utf-8-sig'), args.bumper_holds)
        with args.output.open('wb' if args.force else 'xb') as output:
            output.write(data)
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(f'Wrote {args.output}: {count} records, unsigned. Initial source BPM: {bpm:g}')
    print('Register the chart separately; set catalog bpm_display to half the source BPM to match this build’s initial BPM convention.')


if __name__ == '__main__':
    main()
