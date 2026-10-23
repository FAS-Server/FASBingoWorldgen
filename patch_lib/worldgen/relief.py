"""Relief splines of the density-function generation.

Three cubic splines shape the terrain: `offset` sets the mean surface height,
`factor` the slope, and `jaggedness` the peak noise added on low-erosion
ridges. Each is exposed as its own density function file from 1.19 on; 1.18.2
spells `offset` and `jaggedness` as `terrain_shaper_spline` inside
`depth.json` and `sloped_cheese.json`, with the points in code, so a version
patch that has to move them first substitutes a transcribed tree and then
points the inline node at it (`terrain_shaper_reference`).
"""

from pathlib import Path
import typing as ty

from .. import dispatch


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


def _swap_terrain_shaper(node: ty.Any, spline: str, reference: str) \
        -> ty.Tuple[ty.Any, int]:
    '''Replaces every `terrain_shaper_spline` of `spline` with `reference`.'''
    count = 0
    if isinstance(node, dict):
        if node.get('type') == 'minecraft:terrain_shaper_spline' \
                and node.get('spline') == spline:
            return reference, 1
        for key, value in list(node.items()):
            new_value, found = _swap_terrain_shaper(value, spline, reference)
            if found:
                node[key] = new_value
            count += found
    elif isinstance(node, list):
        for index, value in enumerate(node):
            new_value, found = _swap_terrain_shaper(value, spline, reference)
            if found:
                node[index] = new_value
            count += found
    return node, count


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


def unchanged(relative: Path, json_content: ty.Dict) -> ty.Dict:
    '''Patcher for a source that is emitted as is, e.g. a transcribed spline.'''
    return json_content


def terrain_shaper_reference(*, spline: str, reference: str) -> dispatch.Patcher:
    '''
    Patcher for a density function that inlines a `terrain_shaper_spline`.

    Before 1.19 the three relief splines had no files: `offset` and `jaggedness`
    were spelled as `minecraft:terrain_shaper_spline` inside `depth.json` and
    `sloped_cheese.json`, and the points lived in `TerrainShaper`. This replaces
    such a node with a reference to a file that carries the transcribed points,
    so the relief knobs have something to scale.

    The node's `min_value`/`max_value` are dropped with it. They clamped the
    shaper output, and the substituted tree never leaves that range, so the
    substitution is value-identical.
    '''
    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        _, found = _swap_terrain_shaper(json_content, spline, reference)
        if found != 1:
            raise KeyError(
                f'Expected one {spline} terrain_shaper_spline in {relative}, '
                f'found {found}'
            )
        return json_content

    return patch
