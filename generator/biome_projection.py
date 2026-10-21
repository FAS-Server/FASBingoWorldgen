"""Project the 1.18.2 official multi_noise table onto the 4-axis table that the
1.16.5 and 1.17.1 biome sources read.

Unlike `biome_scale.py`, this script is not an estimate: it produces the table
that the legacy-worldgen patches ship. The 1.18+ biome source reads seven axes
with ranges, the legacy one reads four scalars and picks the nearest point, so
the projection has to choose one representative biome per point and, below the
`full` tier, quantise the points to keep the linear scan affordable.

The legacy versions differ in which biomes exist: 1.17.1 already has the two
cave biomes, 1.16.5 does not. The table is therefore generated per target, from
that target's own biome list, so a cave biome is kept where the version has it
and dropped where it would have no registry entry.

Inputs and outputs both live under `common/biome_source/`:

* `source/overworld_1_18_2.json` -- the official table to project.
* `<target>/biomes.json` -- the biome list of that target version.
* `<target>/overworld_<tier>.json` -- the table a patch injects as
  `generator.biome_source.biomes`, together with the axes it was built for.

`generator/biome_projection_report.md` records size and coverage per target and
tier. All of it is data, not build code: the build only reads the JSON through
a patch.
"""

import argparse
import json
import typing as ty
from collections import Counter, defaultdict
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]

# Everything this script needs is tracked under common/, so rerunning it does
# not depend on any local reference material.
DATA_DIR = PROJECT / 'common' / 'biome_source'
SOURCE = DATA_DIR / 'source' / 'overworld_1_18_2.json'
REPORT = PROJECT / 'generator' / 'biome_projection_report.md'

SOURCE_TAG = '1.18.2'

# Target version directory name -> tag recorded in the report. The target's own
# biome list decides what a projection may keep.
TARGETS: ty.Dict[str, str] = {
    '1_16_5': '1.16.5',
    '1_17_1': '1.17.1',
}

# official axis -> legacy axis. `erosion` and `depth` have no legacy
# counterpart: the old source has no erosion concept, and it samples every axis
# at y=0, so depth would be a constant.
AXIS_MAP = {
    'temperature': 'temperature',
    'humidity': 'humidity',
    'continentalness': 'altitude',
    'weirdness': 'weirdness',
}
LEGACY_AXES = ('temperature', 'humidity', 'altitude', 'weirdness')

# Quantisation granularity per tier. `full` keeps every projected point; the
# legacy source scans the list linearly, so the coarse tiers exist to bound the
# per-chunk cost. 0.25 is the coarsest granularity that keeps every required
# biome without patching it back in.
TIERS: ty.Dict[str, float] = {
    'full': 0.0,
    'balanced': 0.25,
    'lite': 0.5,
}

# Biomes the official table treats as a variant of another one. When several
# source entries collapse onto one legacy point, a non-variant candidate wins,
# so the plain biome does not disappear behind its rare variant.
VARIANT_LIKE = {
    'sunflower_plains', 'ice_spikes', 'old_growth_pine_taiga',
    'old_growth_spruce_taiga', 'old_growth_birch_forest', 'sparse_jungle',
    'bamboo_jungle', 'eroded_badlands', 'wooded_badlands', 'meadow',
    'cherry_grove', 'grove', 'snowy_slopes', 'jagged_peaks', 'frozen_peaks',
    'stony_peaks', 'stony_shore', 'windswept_forest',
    'windswept_gravelly_hills', 'windswept_savanna',
}

# Official biomes reached through the depth axis, which the legacy source does
# not read: it samples every axis at y=0. They are kept when the target version
# has them (1.17.1 introduced both) and dropped otherwise. Keeping one costs a
# surface point, since the two-dimensional projection has nowhere else to put
# it; that is the closest a legacy source can come to a cave biome.
CAVE_BIOMES = ('dripstone_caves', 'lush_caves')

# Official name -> legacy name, for biomes renamed or split after 1.16.
NAME_MAP = {
    'snowy_plains': 'snowy_tundra',
    'old_growth_birch_forest': 'tall_birch_forest',
    'old_growth_pine_taiga': 'giant_tree_taiga',
    'old_growth_spruce_taiga': 'giant_spruce_taiga',
    'sparse_jungle': 'jungle_edge',
    'windswept_hills': 'mountains',
    'windswept_forest': 'wooded_mountains',
    'windswept_gravelly_hills': 'gravelly_mountains',
    'windswept_savanna': 'shattered_savanna',
    'wooded_badlands': 'wooded_badlands_plateau',
    'stony_shore': 'stone_shore',
    'meadow': 'plains',
    'grove': 'snowy_taiga',
    'snowy_slopes': 'snowy_mountains',
    'jagged_peaks': 'snowy_mountains',
    'frozen_peaks': 'snowy_mountains',
    'stony_peaks': 'mountains',
}

# Biomes a world must still contain after quantisation. A coarse tier can merge
# a rare biome away entirely; those are patched back from the full projection.
# Entries a target version does not have are ignored for it.
REQUIRED = (
    'ocean', 'deep_ocean', 'cold_ocean', 'deep_cold_ocean', 'lukewarm_ocean',
    'deep_lukewarm_ocean', 'warm_ocean', 'frozen_ocean', 'deep_frozen_ocean',
    'river', 'frozen_river',
    'beach', 'snowy_beach', 'stone_shore', 'mushroom_fields',
    'plains', 'desert', 'forest', 'birch_forest', 'dark_forest', 'taiga',
    'snowy_taiga', 'snowy_tundra', 'savanna', 'jungle', 'swamp', 'badlands',
    'mountains',
    *CAVE_BIOMES,
)


def legacy_biomes(target: str) -> ty.Set[str]:
    '''Biome names that exist in the target version.'''
    path = DATA_DIR / target / 'biomes.json'
    content = json.loads(path.read_text(encoding='utf-8'))
    return set(content['biomes'])


def midpoint(value: ty.Any) -> float:
    '''A parameter is either a scalar or a [min, max] pair.'''
    if isinstance(value, list):
        return (float(value[0]) + float(value[1])) / 2.0
    return float(value)


def quantise(value: float, granularity: float) -> float:
    if not granularity:
        return round(value, 4)
    return round(round(value / granularity) * granularity, 6)


def representative(votes: ty.List[str]) -> str:
    '''Non-variant candidate first, then the most frequent one.'''
    plain = [name for name in votes if name not in VARIANT_LIKE]
    return Counter(plain or votes).most_common(1)[0][0]


def project(entries: ty.List[ty.Dict], existing: ty.Set[str]) -> ty.Tuple[ty.Dict, ty.List[str]]:
    '''
    Projects the official entries onto legacy points.

    returns (cells, dropped): cells maps a 4-axis point to the list of candidate
    legacy biome names that collapsed onto it; dropped lists the cave biomes the
    target version does not have.
    '''
    unknown, dropped = [], []
    cells: ty.Dict[ty.Tuple[float, ...], ty.List[str]] = defaultdict(list)
    for entry in entries:
        name = entry['biome'].split(':', 1)[-1]
        if name in CAVE_BIOMES and name not in existing:
            dropped.append(name)
            continue
        name = NAME_MAP.get(name, name)
        if name not in existing:
            unknown.append(name)
            continue
        parameters = entry['parameters']
        key = tuple(
            round(midpoint(parameters[axis]), 4)
            for axis in AXIS_MAP
        )
        cells[key].append(name)
    if unknown:
        raise KeyError(f'no legacy biome for: {sorted(set(unknown))}')
    return cells, dropped


def build_tier(
        cells: ty.Dict[ty.Tuple[float, ...], ty.List[str]],
        granularity: float,
        required: ty.Iterable[str],
    ) -> ty.Tuple[ty.Dict[ty.Tuple[float, ...], str], ty.List[str]]:
    '''
    Quantises the points and resolves the collisions.

    returns (table, restored): restored lists the required biomes that
    quantisation merged away and that were patched back in.
    '''
    merged: ty.Dict[ty.Tuple[float, ...], ty.List[str]] = defaultdict(list)
    for key, votes in cells.items():
        merged[tuple(quantise(value, granularity) for value in key)].extend(votes)
    table = {key: representative(votes) for key, votes in merged.items()}

    # Patch back any required biome the quantisation merged away. The point
    # chosen is the one where that biome is most common in the full
    # projection, so the restored biome lands where it belongs. A cave biome
    # only ever occurs once, so restoring it takes over that one surface point.
    missing = [name for name in required if name not in set(table.values())]
    for name in missing:
        points = [key for key, votes in cells.items() if name in votes]
        if not points:
            raise KeyError(f'{name} does not occur in the projection')
        counts = Counter(points)
        best = max(counts, key=lambda point: (counts[point], point))
        table[tuple(quantise(value, granularity) for value in best)] = name
    return table, missing


def write_table(
        target: str,
        tier: str,
        granularity: float,
        table: ty.Dict[ty.Tuple[float, ...], str],
    ) -> Path:
    entries = [
        {
            'biome': 'minecraft:' + table[key],
            'parameters': dict(zip(LEGACY_AXES, key), offset=0.0),
        }
        for key in sorted(table)
    ]
    output_dir = DATA_DIR / target
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / f'overworld_{tier}.json'
    payload = {
        'source': SOURCE_TAG,
        'target': target,
        'axes': list(LEGACY_AXES),
        'granularity': granularity,
        'biomes': entries,
    }
    destination.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8'
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--target', choices=[*TARGETS, 'all'], default='all',
        help='target version directory to write; default writes every target',
    )
    parser.add_argument(
        '--tier', choices=[*TIERS, 'all'], default='all',
        help='tier to write; default writes every tier',
    )
    args = parser.parse_args()

    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    entries = source['generator']['biome_source']['biomes']
    tiers = list(TIERS) if args.tier == 'all' else [args.tier]
    targets = list(TARGETS) if args.target == 'all' else [args.target]

    lines = [
        '# 四轴投影表\n',
        f'- 源：`{SOURCE_TAG}` 官方表，{len(entries)} 条目',
        '- 每个目标版本按自己的群系清单生成，版本没有的群系即丢弃。',
    ]
    for target in targets:
        existing = legacy_biomes(target)
        cells, dropped = project(entries, existing)
        required = tuple(name for name in REQUIRED if name in existing)
        conflicts = sum(1 for votes in cells.values() if len(set(votes)) > 1)

        lines += [
            '',
            f'## `{target}`\n',
            f'- 目标群系清单：`{TARGETS[target]}`',
            f'- 投影点位：{len(cells)}，冲突点位：{conflicts}',
            f'- 版本没有而丢弃：{", ".join(f"`{n}`" for n in sorted(set(dropped))) or "-"}',
            '',
            '| 档位 | 量化 | 条目 | 群系 | 补回的必备群系 |',
            '| --- | --- | --- | --- | --- |',
        ]
        for tier in tiers:
            granularity = TIERS[tier]
            table, restored = build_tier(cells, granularity, required)
            used = set(table.values())
            destination = write_table(target, tier, granularity, table)
            print(f'{target}/{tier}: {len(table)} entries, {len(used)} biomes -> {destination}')
            lines.append(
                f'| `{tier}` | {granularity or "-"} | {len(table)} | {len(used)} | '
                f'{", ".join(f"`{n}`" for n in restored) or "-"} |'
            )

    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'report -> {REPORT}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
