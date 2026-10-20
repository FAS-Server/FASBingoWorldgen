from pathlib import Path
import typing as ty

from patch_lib import paths

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

# Targets are relative to the pack root, so the same table works for the main
# pack and for an overlay.
#
# `count` is how many times a chunk attempts to place a room; vanilla 10 shallow,
# 4 deep. `max_y` caps the top of the vertical range a room may pick, leaving the
# rest of the range at the vanilla bounds; the vanilla shallow bound is
# `below_top 0`.
RELATIVE_TARGETS = {
    Path('data/minecraft/worldgen/placed_feature/monster_room.json'): {'count': 50, 'max_y': 128},
    Path('data/minecraft/worldgen/placed_feature/monster_room_deep.json'): {'count': 20},
}

# Set by reference_file, which is the only place that knows the pack root.
_pack_root = Path()


def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
        -> ty.List[ty.Tuple[str, Path, Path]]:
    global _pack_root
    _pack_root = paths.package_root(patch_path)
    return [
        ('COMMON', VANILLA_DIR / f'placed_feature__{relative.stem}.json', _pack_root / relative)
        for relative in RELATIVE_TARGETS
    ]


def _placement_entry(relative: Path, json_content: ty.Dict, placement_type: str) -> ty.Dict:
    '''Placement is an ordered list, so entries are looked up by type.'''
    for entry in json_content['placement']:
        if entry['type'] == placement_type:
            return entry
    raise ValueError(f'{relative}: no {placement_type} entry')


def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
    for target, json_content in content:
        relative = target.relative_to(_pack_root)
        rules = RELATIVE_TARGETS[relative]
        _placement_entry(relative, json_content, 'minecraft:count')['count'] = rules['count']
        if 'max_y' in rules:
            height = _placement_entry(relative, json_content, 'minecraft:height_range')['height']
            height['max_inclusive'] = {'absolute': rules['max_y']}
    return content
