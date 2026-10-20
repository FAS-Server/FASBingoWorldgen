from pathlib import Path
import typing as ty

from patch_lib import paths

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

# Targets are relative to the pack root, so the same tables work for the main
# pack and for an overlay.
ENDERMAN_TARGET = 'data/minecraft/loot_table/entities/enderman.json'
BARTERING_TARGET = 'data/minecraft/loot_table/gameplay/piglin_bartering.json'

SOURCES = {
    ENDERMAN_TARGET: 'loot_table__enderman.json',
    BARTERING_TARGET: 'loot_table__piglin_bartering.json',
}

# Endermen: vanilla drops 0..1 pearls, the project guarantees at least 1.
MIN_ENDERMAN_PEARL = 1.0

# Bartering pearls: since 1.16.2 vanilla trades 2..4 pearls at weight 10;
# 1.16.1 traded 4..8 at weight 20. Only this entry is restored, so trades
# added by later versions stay in the table.
BARTERING_PEARL = 'minecraft:ender_pearl'
BARTERING_PEARL_WEIGHT = 20
BARTERING_PEARL_MIN = 4.0
BARTERING_PEARL_MAX = 8.0

# Set by reference_file, which is the only place that knows the pack root.
_pack_root = Path()


def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
        -> ty.List[ty.Tuple[str, Path, Path]]:
    global _pack_root
    _pack_root = paths.package_root(patch_path)
    return [
        ('COMMON', VANILLA_DIR / source, _pack_root / relative)
        for relative, source in SOURCES.items()
    ]


def _patch_enderman(relative: Path, json_content: ty.Dict) -> ty.Dict:
    json_content['pools'][0]['entries'][0]['functions'][0]['count']['min'] = MIN_ENDERMAN_PEARL
    return json_content


def _patch_bartering(relative: Path, json_content: ty.Dict) -> ty.Dict:
    entries = json_content['pools'][0]['entries']
    pearls = [entry for entry in entries if entry.get('name') == BARTERING_PEARL]
    if len(pearls) != 1:
        raise KeyError(f'Expected one {BARTERING_PEARL} entry in {relative}, found {len(pearls)}')
    pearl = pearls[0]
    pearl['weight'] = BARTERING_PEARL_WEIGHT
    counts = [
        function for function in pearl.get('functions', [])
        if function.get('function') == 'minecraft:set_count'
    ]
    if len(counts) != 1:
        raise KeyError(f'Expected one set_count on {BARTERING_PEARL} in {relative}, found {len(counts)}')
    counts[0]['count']['min'] = BARTERING_PEARL_MIN
    counts[0]['count']['max'] = BARTERING_PEARL_MAX
    return json_content


RELATIVE_PATCHERS = {
    Path(ENDERMAN_TARGET): _patch_enderman,
    Path(BARTERING_TARGET): _patch_bartering,
}


def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
    result = []
    for target, json_content in content:
        relative = target.relative_to(_pack_root)
        if relative not in RELATIVE_PATCHERS:
            raise KeyError(f'No patcher for: {relative}')
        result.append((target, RELATIVE_PATCHERS[relative](relative, json_content)))
    return result
