"""Shared implementation of the 26.x worldgen patches.

The layout below is verified against 26.1 to 26.3 (data formats 101.1, 107.1 and
121.0); re-scan the vanilla files before reusing it on a later version.

The 26.x data layout puts every target under `data/minecraft/worldgen/<kind>/`
and every vanilla file is flattened under `common/vanilla/<version>/` as
`<kind>__<name>.json`, which is what `source_name` builds. A patch therefore
only lists target paths and the parameters; the scaling and spline logic lives
here.

Both the terrain and the biome source read the same named density functions, so
a frequency set here cannot drift between the two sides.
"""

from pathlib import Path
import math
import typing as ty

from . import dispatch

WORLDGEN_DIR = 'worldgen'

# Density function spellings of the noise node. 26.3 renamed `shifted_noise` to
# `noise`; the node keeps its `xz_scale`, so both are scaled the same way.
NOISE_TYPES = ('minecraft:noise', 'minecraft:shifted_noise')

# Cache wrappers around a noise node. 26.3 renamed `flat_cache` to `cache` and
# its `argument` key to `input`.
CACHE_TYPES = ('minecraft:cache', 'minecraft:flat_cache')


def _noise_node(relative: Path, json_content: ty.Dict) -> ty.Dict:
    '''
    Returns the noise node of a density function.

    Some functions are the noise node itself (`overworld/temperature.json` from
    26.3 on), others wrap it in a cache whose key is `input` from 26.3 and
    `argument` before it.
    '''
    node = json_content
    if node.get('type') in CACHE_TYPES:
        keys = [key for key in ('input', 'argument') if key in node]
        if len(keys) != 1:
            raise TypeError(
                f'Expected one of input/argument in {relative}, got {sorted(node)}'
            )
        node = node[keys[0]]
    if node.get('type') not in NOISE_TYPES:
        raise TypeError(
            f'Expected a noise density function in {relative}, '
            f'got {node.get("type")!r}'
        )
    return node


def source_name(target: Path) -> str:
    '''
    Returns the flattened baseline name of a worldgen target.

    args:
    - target: target path relative to the pack root, e.g.
      `data/minecraft/worldgen/density_function/overworld/offset.json`.

    returns:
    - the name used under `common/vanilla/<version>/`, e.g.
      `density_function__overworld__offset.json`.
    '''
    parts = target.parts
    try:
        index = parts.index(WORLDGEN_DIR)
    except ValueError:
        raise ValueError(f'{target} is not under {WORLDGEN_DIR}/') from None
    return '__'.join(parts[index + 1:])


def _sources(
        vanilla_dir: Path,
        targets: ty.Iterable[Path],
        overrides: ty.Mapping[Path, Path],
    ) -> ty.Dict[Path, Path]:
    return {
        target: overrides.get(target, vanilla_dir / source_name(target))
        for target in targets
    }


def _map_spline(spline: ty.Dict, mapping: ty.Callable[[float], ty.Tuple[float, float]]) -> None:
    '''Maps every leaf value of a spline tree in place.

    mapping takes a leaf value and returns (new value, local slope), where the
    local slope scales the derivative so the curve keeps its shape.
    '''
    for point in spline['points']:
        value = point['value']
        if isinstance(value, dict):
            if 'points' not in value:
                raise TypeError(f'Unexpected spline value: {sorted(value)}')
            _map_spline(value, mapping)
        else:
            point['value'], scale = mapping(value)
            point['derivative'] *= scale


def _map_all_splines(node: ty.Any, mapping: ty.Callable[[float], ty.Tuple[float, float]]) -> int:
    '''Maps every spline in a density function; returns how many it found.'''
    found = 0
    if isinstance(node, dict):
        if node.get('type') == 'minecraft:spline':
            _map_spline(node['spline'], mapping)
            found += 1
        for value in node.values():
            found += _map_all_splines(value, mapping)
    elif isinstance(node, list):
        for value in node:
            found += _map_all_splines(value, mapping)
    return found


def _scale_all_splines(node: ty.Any, factor: float) -> int:
    '''Scales every spline in a density function; returns how many it found.'''
    return _map_all_splines(node, lambda value: (value * factor, factor))


def overworld_climate(
        *,
        inline_climate_fields: ty.Iterable[str],
        xz_scale: float,
        underground_relief: float,
    ) -> dispatch.Patcher:
    '''
    Patcher for `noise_settings/overworld.json`: scales the inlined climate
    fields and, when asked, rescales the depth axis the biome source samples.

    A climate field is expected to be an inlined shifted_noise; the other three
    axes stay as references to named density functions, which keeps the biome
    source and the terrain on the same value.
    '''
    fields = tuple(inline_climate_fields)

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        router = json_content['noise_router']
        for field in fields:
            noise = router[field]
            if noise.get('type') not in NOISE_TYPES:
                raise TypeError(
                    f'Expected an inlined noise in {relative} {field}, '
                    f'got {noise.get("type")!r}'
                )
            noise['xz_scale'] = xz_scale
        if underground_relief != 1.0:
            # The biome source samples this field; terrain reads overworld/depth
            # through sloped_cheese. Wrapping the reference therefore rescales
            # the biome depth axis without touching the density.
            if not isinstance(router['depth'], str):
                raise TypeError(
                    f'Expected a reference in {relative} depth, got {router["depth"]!r}'
                )
            router['depth'] = {
                'type': 'minecraft:mul',
                'argument1': 1.0 / underground_relief,
                'argument2': router['depth'],
            }
        return json_content

    return patch


def nether_climate(
        *,
        climate_fields: ty.Iterable[str],
        xz_scale: float,
    ) -> dispatch.Patcher:
    '''Patcher for `noise_settings/nether.json`: scales the inlined climate fields.'''
    fields = tuple(climate_fields)

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        router = json_content['noise_router']
        for field in fields:
            noise = router[field]
            if noise.get('type') not in NOISE_TYPES:
                raise TypeError(
                    f'Expected an inlined noise in {relative} {field}, '
                    f'got {noise.get("type")!r}'
                )
            noise['xz_scale'] = xz_scale
        return json_content

    return patch


def noise_frequency(*, xz_scale: float) -> dispatch.Patcher:
    '''
    Patcher for a density function whose noise node carries the frequency.

    The wrapper, if any, only caches; the noise node inside is what the biome
    source and the terrain sample. 26.3 moved the two climate fields
    (`overworld/temperature.json`, `overworld/vegetation.json`) out of
    `noise_router` into files of their own, and this patcher scales them there.
    '''
    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        _noise_node(relative, json_content)['xz_scale'] = xz_scale
        return json_content

    return patch


def relief_positive(scale: float) -> dispatch.Patcher:
    '''Patcher for `overworld/offset.json`: scales the positive leaves only.'''
    def mapping(value: float) -> ty.Tuple[float, float]:
        if value > 0.0:
            return value * scale, scale
        return value, 1.0

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        if _map_all_splines(json_content, mapping) == 0:
            raise KeyError(f'No spline to map in {relative}')
        return json_content

    return patch


def relief_above_one(scale: float) -> dispatch.Patcher:
    '''Patcher for `overworld/factor.json`: scales the leaves above 1.0 only.'''
    def mapping(value: float) -> ty.Tuple[float, float]:
        if value > 1.0:
            return 1.0 + (value - 1.0) * scale, scale
        return value, 1.0

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        if _map_all_splines(json_content, mapping) == 0:
            raise KeyError(f'No spline to map in {relative}')
        return json_content

    return patch


def relief_scale(scale: float) -> dispatch.Patcher:
    '''Patcher for `overworld/jaggedness.json`: scales every spline leaf.'''
    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        # Scaling the amplitude lowers the spikes smoothly; clamping the density
        # instead would shave them flat.
        if _scale_all_splines(json_content, scale) == 0:
            raise KeyError(f'No spline to scale in {relative}')
        return json_content

    return patch


def terrain(
        *,
        vanilla_dir: Path,
        overworld_settings: Path,
        nether_settings: Path,
        offset: Path,
        factor: Path,
        jaggedness: Path,
        density_functions: ty.Iterable[Path],
        climate_functions: ty.Iterable[Path] = (),
        xz_scale_overworld: float,
        inline_climate_fields: ty.Iterable[str],
        xz_scale_nether: float,
        nether_climate_fields: ty.Iterable[str],
        relief_highland: float,
        relief_factor: float,
        relief_jagged: float,
        underground_relief: float,
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the terrain patch: climate frequency, relief splines and the
    underground depth axis.

    `density_functions` are the named functions the biome source and the terrain
    share; `climate_functions` are climate fields that a later version moved
    out of `noise_router` into files of their own, so they are scaled the same
    way instead of being patched inside the settings file.

    A relief parameter of 1.0 drops its file from the pack instead of emitting a
    copy identical to vanilla, so it also decides whether the file is a source.
    '''
    density_functions = tuple(density_functions)
    climate_functions = tuple(climate_functions)

    targets = [overworld_settings, nether_settings]
    if relief_highland != 1.0:
        targets.append(offset)
    if relief_factor != 1.0:
        targets.append(factor)
    if relief_jagged != 1.0:
        targets.append(jaggedness)
    targets.extend(density_functions)
    targets.extend(climate_functions)

    patch_overworld = overworld_climate(
        inline_climate_fields=inline_climate_fields,
        xz_scale=xz_scale_overworld,
        underground_relief=underground_relief,
    )
    patch_nether = nether_climate(
        climate_fields=nether_climate_fields,
        xz_scale=xz_scale_nether,
    )
    patch_noise = noise_frequency(xz_scale=xz_scale_overworld)

    patchers: ty.Dict[Path, dispatch.Patcher] = {
        overworld_settings: patch_overworld,
        nether_settings: patch_nether,
    }
    if relief_highland != 1.0:
        patchers[offset] = relief_positive(relief_highland)
    if relief_factor != 1.0:
        patchers[factor] = relief_above_one(relief_factor)
    if relief_jagged != 1.0:
        patchers[jaggedness] = relief_scale(relief_jagged)
    patchers.update({target: patch_noise for target in density_functions})
    patchers.update({target: patch_noise for target in climate_functions})

    return dispatch.make(_sources(vanilla_dir, targets, source_overrides), patchers)


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


def structure(
        *,
        vanilla_dir: Path,
        dimension_sets: ty.Mapping[str, ty.Iterable[str]],
        dimension_scales: ty.Mapping[str, ty.Mapping[str, float]],
        special_field_overrides: ty.Mapping[str, ty.Dict],
        structure_field_overrides: ty.Mapping[str, ty.Dict],
        structure_dir: Path = Path('data/minecraft/worldgen/structure'),
        structure_set_dir: Path = Path('data/minecraft/worldgen/structure_set'),
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the structure patch: every listed set is scaled by the factors of its
    dimension, then the pinned fields are applied.

    dimension_sets lists the vanilla sets of each dimension, so scaling covers
    the whole dimension instead of a hand-picked list of values. The override
    tables are keyed by plain name (`strongholds`, `ancient_city`) so a version
    patch only contributes the directories, which differ between versions.
    '''
    unknown_dimensions = set(dimension_sets) - set(dimension_scales)
    if unknown_dimensions:
        raise KeyError(f'No scale for dimension(s): {sorted(unknown_dimensions)}')

    target_dimension = {
        structure_set_dir / f'{name}.json': dimension
        for dimension, names in dimension_sets.items()
        for name in names
    }
    pinned_fields = {
        structure_set_dir / f'{name}.json': fields
        for name, fields in special_field_overrides.items()
    }
    structure_fields = {
        structure_dir / f'{name}.json': fields
        for name, fields in structure_field_overrides.items()
    }

    def patch_structure(relative: Path, json_content: ty.Dict) -> ty.Dict:
        json_content.update(structure_fields[relative])
        return json_content

    def patch_structure_set(relative: Path, json_content: ty.Dict) -> ty.Dict:
        placement = json_content['placement']
        placement_type = placement.get('type')
        if placement_type == 'minecraft:random_spread':
            scales = dimension_scales[target_dimension[relative]]
            # Vanilla has separation 0 with spacing 1, so only spacing is floored to 1.
            placement['spacing'] = _scale(placement['spacing'], scales['spacing'], minimum=1)
            placement['separation'] = _scale(
                placement['separation'], scales['separation'], minimum=0
            )
        elif placement_type != 'minecraft:concentric_rings':
            raise ValueError(f'{relative}: unsupported placement type {placement_type}')
        placement.update(pinned_fields.get(relative, {}))
        _validate_placement(relative, placement)
        return json_content

    targets = list(structure_fields) + list(target_dimension)
    patchers: ty.Dict[Path, dispatch.Patcher] = {
        relative: patch_structure for relative in structure_fields
    }
    patchers.update({
        relative: patch_structure_set for relative in target_dimension
    })
    return dispatch.make(_sources(vanilla_dir, targets, source_overrides), patchers)


def _placement_entry(relative: Path, json_content: ty.Dict, placement_type: str) -> ty.Dict:
    '''Placement is an ordered list, so entries are looked up by type.'''
    for entry in json_content['placement']:
        if entry['type'] == placement_type:
            return entry
    raise ValueError(f'{relative}: no {placement_type} entry')


def placed_feature(
        *,
        vanilla_dir: Path,
        rules: ty.Mapping[str, ty.Mapping[str, ty.Any]],
        placed_feature_dir: Path = Path('data/minecraft/worldgen/placed_feature'),
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the placed feature patch.

    Each rule is keyed by placed feature name and maps to `count` and, when the
    vertical range must be capped, to `max_y`. `count` is how many times a chunk
    attempts the placement.
    '''
    targets = {
        placed_feature_dir / f'{name}.json': fields
        for name, fields in rules.items()
    }

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        fields = targets[relative]
        _placement_entry(relative, json_content, 'minecraft:count')['count'] = fields['count']
        if 'max_y' in fields:
            height = _placement_entry(
                relative, json_content, 'minecraft:height_range'
            )['height']
            height['max_inclusive'] = {'absolute': fields['max_y']}
        return json_content

    patchers: ty.Dict[Path, dispatch.Patcher] = {target: patch for target in targets}
    return dispatch.make(_sources(vanilla_dir, targets, source_overrides), patchers)

