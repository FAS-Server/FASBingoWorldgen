from pathlib import Path
import math
import typing as ty

from patch_lib import paths

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

STRUCTURE_DIR = Path('data/minecraft/worldgen/structure')
STRUCTURE_SET_DIR = Path('data/minecraft/worldgen/structure_set')

# Targets are relative to the pack root, so the same tables work for the main
# pack and for an overlay.

# Factors applied to the vanilla spacing/separation of every structure set in a
# dimension. Sets pinned in SPECIAL_FIELD_OVERRIDES keep the values given there.
DIMENSION_SCALES = {
    'overworld': {'spacing': 3/8, 'separation': 1/4},
    'nether': {'spacing': 1/2, 'separation': 1/2},
    'end': {'spacing': 1/3, 'separation': 1/3},
}

# Every vanilla structure set of each dimension, so scaling covers the whole
# dimension instead of a hand-picked list. Uncomment a name to include that set
# in the scaling pass again.
DIMENSION_SETS = {
    'overworld': [
        'ancient_cities',
        'buried_treasures',
        'desert_pyramids',
        'igloos',
        'jungle_temples',
        # 'mineshafts',             # 0.004 frequency with a 1-chunk spacing; scaling the spacing is a no-op.
        # 'ocean_monuments',        # Vanilla 32/5; uncomment to include it.
        'ocean_ruins',
        'pillager_outposts',
        'ruined_portals',
        'shipwrecks',
        'strongholds',
        'swamp_huts',
        'trail_ruins',
        'trial_chambers',
        'villages',
        'woodland_mansions',
    ],
    'nether': [
        'nether_complexes',
        # 'nether_fossils',         # spacing 2 / separation 1; scaling floors separation onto spacing.
    ],
    'end': [
        'end_cities',
    ],
}

# `ruined_portals` stays one set serving both dimensions: the structure
# definitions filter by biome tag, so the nether variants only match in the
# nether. It is scaled with the overworld factors, and the nether portals in it
# follow that result.
TARGET_DIMENSION = {
    STRUCTURE_SET_DIR / f'{name}.json': dimension
    for dimension, names in DIMENSION_SETS.items()
    for name in names
}

# Final values for placement fields the dimension factors cannot express, such
# as the frequency of a structure that fires without a grid. An entry wins over
# the scaled spacing/separation. Vanilla: frequency 0.01 for buried_treasures;
# distance 32 and spread 3 for strongholds.
SPECIAL_FIELD_OVERRIDES = {
    STRUCTURE_SET_DIR / 'buried_treasures.json': {'frequency': 0.03},
    STRUCTURE_SET_DIR / 'strongholds.json': {'distance': 10, 'spread': 6},
}

# Same table for the sets excluded above. Uncomment an entry, then uncomment the
# matching name in DIMENSION_SETS, to pin its special fields when enabling it.
# The values are the vanilla ones, so an entry only restores what scaling would
# replace.
# SPECIAL_FIELD_OVERRIDES.update({
#     STRUCTURE_SET_DIR / 'mineshafts.json': {'frequency': 0.004},
#     STRUCTURE_SET_DIR / 'ocean_monuments.json': {'spacing': 32, 'separation': 5},
#     STRUCTURE_SET_DIR / 'nether_fossils.json': {'spacing': 2, 'separation': 1},
# })

# Structure definitions whose own fields change. Vanilla
# max_distance_from_center is 116.
STRUCTURE_TARGETS = {
    STRUCTURE_DIR / 'ancient_city.json': {'max_distance_from_center': 96},
}

# Common source file name for each target; the flattened names do not follow a
# single rule, so they are stated explicitly.
SOURCES = {
    STRUCTURE_DIR / 'ancient_city.json': 'structure__ancient_city.json',
}
SOURCES.update({
    relative: f'structure_set__{relative.stem}.json'
    for relative in TARGET_DIMENSION
})

# Set by reference_file, which is the only place that knows the pack root.
_pack_root = Path()


def _scale(value: int, factor: float, minimum: int) -> int:
    '''Rounds half up and clamps to `minimum`; round() is banker's rounding.'''
    return max(minimum, int(math.floor(value * factor + 0.5)))


def _validate_placement(relative: Path, placement: ty.Dict) -> None:
    spacing = placement.get('spacing')
    separation = placement.get('separation')
    if spacing is None or separation is None:
        return
    if separation >= spacing:
        raise ValueError(
            f'{relative}: separation {separation} must be less than spacing {spacing}'
        )


def _patch_structure(relative: Path, json_content: ty.Dict) -> ty.Dict:
    json_content.update(STRUCTURE_TARGETS[relative])
    return json_content


def _patch_structure_set(relative: Path, json_content: ty.Dict) -> ty.Dict:
    placement = json_content['placement']
    placement_type = placement.get('type')
    if placement_type == 'minecraft:random_spread':
        scales = DIMENSION_SCALES[TARGET_DIMENSION[relative]]
        # Vanilla has separation 0 with spacing 1, so only spacing is floored to 1.
        placement['spacing'] = _scale(placement['spacing'], scales['spacing'], minimum=1)
        placement['separation'] = _scale(
            placement['separation'], scales['separation'], minimum=0
        )
    elif placement_type != 'minecraft:concentric_rings':
        raise ValueError(f'{relative}: unsupported placement type {placement_type}')
    placement.update(SPECIAL_FIELD_OVERRIDES.get(relative, {}))
    _validate_placement(relative, placement)
    return json_content


RELATIVE_PATCHERS = {
    relative: _patch_structure for relative in STRUCTURE_TARGETS
}
RELATIVE_PATCHERS.update({
    relative: _patch_structure_set for relative in TARGET_DIMENSION
})


def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
        -> ty.List[ty.Tuple[str, Path, Path]]:
    global _pack_root
    _pack_root = paths.package_root(patch_path)
    return [
        ('COMMON', VANILLA_DIR / source, _pack_root / relative)
        for relative, source in SOURCES.items()
    ]


def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
    result = []
    for target, json_content in content:
        relative = target.relative_to(_pack_root)
        result.append((target, RELATIVE_PATCHERS[relative](relative, json_content)))
    return result
