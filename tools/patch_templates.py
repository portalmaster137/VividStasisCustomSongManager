"""Load patch source relative to this module, independent of the working directory."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent / 'patches'
INCLUDE = re.compile(r'@@include_cs:([a-zA-Z_0-9/.-]+)@@')
TOKEN = re.compile(r'@@([a-zA-Z_][a-zA-Z_0-9]*)@@')


def render_patch(name, **values):
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise ValueError(f'Missing or unsafe patch template: {name}')
    source = path.read_text(encoding='utf-8')
    source = INCLUDE.sub(lambda match: '@"' + render_patch(match[1]).replace('"', '""') + '"', source)
    required = set(TOKEN.findall(source))
    if required != set(values):
        raise ValueError(f'Patch {name}: missing {required - set(values)}, unexpected {set(values) - required}')
    return TOKEN.sub(lambda match: str(values[match[1]]), source)
