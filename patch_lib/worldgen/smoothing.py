"""Neighbourhood smoothing of the `factor` spline.

The terrain density above the surface reduces to `factor * depth +
base_3d_noise`, and `depth` falls by 1/128 per block, so a column rises by about
`128 * base_3d_noise / factor` blocks. `factor` comes from the climate splines
and is sampled once per quart, four blocks: with the climate frequency raised
by this pack, a quart can fall from about 3.95 to about 0.63 while both
neighbours stay high, and that one quart is lifted 40 to 60 blocks above
everything around it.

The fix is a box average over the surrounding quarts. A climate axis is a noise
node whose coordinate is `block * xz_scale + shift`, so adding a constant to
`shift` moves the sample point by that constant divided by `xz_scale`; shifting
by `4 * d` blocks therefore means adding `4 * d * xz_scale`. `factor` is
replaced by the mean of `(2r+1)^2` copies of its spline, each one reading the
shifted axes. No frequency changes, and the biome source never reads `factor`,
so the biome layout is untouched cell for cell.

Each shifted axis is a named density function, never an inlined copy: a spline
re-evaluates its coordinate at every level of its tree, and an inlined copy is a
separate object that would be evaluated dozens of times. Named references share
one cached instance per target.
"""

from pathlib import Path
import copy
import typing as ty

from .. import dispatch
from . import climate as climate_patch
from . import relief as relief_patch
from .sources import source_name

# Namespace and directory of the shifted copies. They are new files, not
# replacements of a vanilla one, so they stay out of `data/minecraft/`.
NAMESPACE = 'fasbingo'
DIRECTORY = 'factor_smoothing'

# The climate axes the factor spline reads, and the folded ridge value derived
# from the third one.
AXES = ('continents', 'erosion', 'ridges')
FOLDED = 'ridges_folded'

# One quart is four blocks.
QUART = 4

# The spline spellings of `factor`: its own node from 1.19 on, the terrain
# shaper from 1.18.2 (which folds the ridge noise internally).
SPLINE_TYPES = ('minecraft:spline', 'minecraft:terrain_shaper_spline')

# Every string a spline copy may read from the shared axes.
REFERENCES = tuple(
    f'minecraft:overworld/{name}' for name in (*AXES, FOLDED)
)


def _sign(value: int) -> str:
    '''`p1` for a positive offset, `m1` for a negative one, `0` for none.'''
    if value > 0:
        return f'p{value}'
    if value < 0:
        return f'm{abs(value)}'
    return '0'


def tag(dx: int, dz: int) -> str:
    '''The `<dx>_<dz>` suffix of the shifted copy at that offset.'''
    return f'{_sign(dx)}_{_sign(dz)}'


def target(stem: str) -> Path:
    '''Target path of a shifted copy, relative to the pack root.'''
    return (
        Path('data') / NAMESPACE / 'worldgen' / 'density_function'
        / DIRECTORY / f'{stem}.json'
    )


def reference(stem: str) -> str:
    '''Density function id of a shifted copy.'''
    return f'{NAMESPACE}:{DIRECTORY}/{stem}'


def baseline_name(axis: str) -> str:
    '''Baseline file name of a vanilla axis, as `sources.source_name` builds it.'''
    declared = Path('data/minecraft/worldgen/density_function/overworld')
    return source_name(declared / f'{axis}.json')


def offsets(radius: int) -> ty.Tuple[ty.Tuple[int, int], ...]:
    '''
    The box of offsets, `dx` outermost and `dz` innermost.

    The order is part of the output: the spline copies are summed in it.
    '''
    if radius < 0:
        raise ValueError(f'radius must not be negative, got {radius}')
    return tuple(
        (dx, dz)
        for dx in range(-radius, radius + 1)
        for dz in range(-radius, radius + 1)
    )


def smoothing_targets(
        *, radius: int, include_ridges_folded: bool,
    ) -> ty.Dict[Path, ty.Tuple[str, str, int, int]]:
    '''
    Maps every shifted copy to `(axis, tag, dx, dz)`.

    The centre of the box is left out: `factor` keeps referring to the vanilla
    axes there, so no copy is emitted for it. 1.18.2 has no `ridges_folded`
    file, because its terrain shaper spline folds the ridge noise itself, so
    `include_ridges_folded` is False there and 24 copies are emitted instead of
    32.
    '''
    names = (*AXES, FOLDED) if include_ridges_folded else AXES
    targets = {}
    for dx, dz in offsets(radius):
        if dx == 0 and dz == 0:
            continue
        name = tag(dx, dz)
        for axis in names:
            targets[target(f'{axis}_{name}')] = (axis, name, dx, dz)
    return targets


def _shift(
        relative: Path,
        json_content: ty.Dict,
        noise: ty.Dict,
        key: str,
        blocks: int,
        xz_scale: float,
    ) -> None:
    '''
    Moves the sample of a noise node by `blocks` along one horizontal axis.

    A zero offset leaves the node untouched: the copy still has to be readable,
    but there is nothing to shift, and an `add` of zero would only add a node.

    The vanilla value is kept as the first operand, whatever it is: a reference
    before 26.3, and a reference or omitted before it. An omitted shift means
    zero, so the constant alone is the shifted value.
    '''
    if blocks == 0:
        return
    if key in noise:
        noise[key] = climate_patch.binary(
            relative, json_content, 'minecraft:add', noise[key],
            blocks * xz_scale,
        )
    else:
        noise[key] = blocks * xz_scale


def shifted_axis(*, xz_scale: float, dx: int, dz: int) -> dispatch.Patcher:
    '''
    Patcher for a shifted copy of `continents`, `erosion` or `ridges`.

    `xz_scale` is set to the same value the main file carries, so the copy is
    the same axis sampled `4 * dx` and `4 * dz` blocks away.
    '''
    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        noise = climate_patch.noise_node(relative, json_content)
        noise['xz_scale'] = xz_scale
        _shift(relative, json_content, noise, 'shift_x', dx * QUART, xz_scale)
        _shift(relative, json_content, noise, 'shift_z', dz * QUART, xz_scale)
        return json_content

    return patch


def shifted_ridges_folded(*, name: str) -> dispatch.Patcher:
    '''
    Patcher for a shifted copy of `ridges_folded`.

    The folded value is a plain expression over the ridge noise, so it only has
    to point at the shifted `ridges` copy of the same offset.
    '''
    shifted = reference(f'ridges_{name}')

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        _, replaced = _rewrite(json_content, {'minecraft:overworld/ridges': shifted})
        if replaced != 1:
            raise KeyError(
                f'Expected one ridge reference in {relative}, found {replaced}'
            )
        return json_content

    return patch


def _rewrite(node: ty.Any, mapping: ty.Mapping[str, str]) -> ty.Tuple[ty.Any, int]:
    '''Replaces the strings of `mapping` in place; returns how many it replaced.'''
    if isinstance(node, str):
        replacement = mapping.get(node)
        return (node, 0) if replacement is None else (replacement, 1)
    count = 0
    if isinstance(node, dict):
        for key, value in node.items():
            node[key], found = _rewrite(value, mapping)
            count += found
    elif isinstance(node, list):
        for index, value in enumerate(node):
            node[index], found = _rewrite(value, mapping)
            count += found
    return node, count


def _count(node: ty.Any, mapping: ty.Mapping[str, str]) -> int:
    '''Counts the strings of `mapping` still present in `node`.'''
    if isinstance(node, str):
        return 1 if node in mapping else 0
    if isinstance(node, dict):
        return sum(_count(value, mapping) for value in node.values())
    if isinstance(node, list):
        return sum(_count(value, mapping) for value in node)
    return 0


def _find_splines(node: ty.Any, path: ty.Tuple = ()) -> ty.List[ty.Tuple[ty.Tuple, ty.Dict]]:
    '''
    Returns every `factor` spline node with its path.

    A spline does not nest inside another one, so a hit is not descended into.
    '''
    found: ty.List[ty.Tuple[ty.Tuple, ty.Dict]] = []
    if isinstance(node, dict):
        if node.get('type') in SPLINE_TYPES:
            return [(path, node)]
        for key, value in node.items():
            found.extend(_find_splines(value, path + (key,)))
    elif isinstance(node, list):
        for index, value in enumerate(node):
            found.extend(_find_splines(value, path + (index,)))
    return found


def _replace(root: ty.Dict, path: ty.Tuple, new: ty.Any) -> None:
    '''Puts `new` where `path` points, in place.'''
    parent = root
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = new


def smoothed_factor(
        *,
        radius: int,
        relief_factor: float,
        binary_keys: ty.Optional[ty.Tuple[str, str]] = None,
    ) -> dispatch.Patcher:
    '''
    Patcher for `overworld/factor.json`: the box average of its spline.

    The relief knob, when enabled, is applied first, so the average is taken
    over the compression this pack ships rather than over the vanilla curve.
    Both sentinels off (no radius, `relief_factor` 1.0) means the file is not a
    target at all.

    The centre copy is the untouched spline, so the average keeps the vanilla
    curve as one of its terms and cannot drift away from it.

    `binary_keys` is only needed when the document carries neither a binary nor
    a cache node to read the spelling from. That happens on 1.18.2, whose
    `factor` source with the relief knob on is the transcribed spline tree
    rather than a vanilla document.
    '''
    scale_leaves = (
        relief_patch.relief_above_one(relief_factor)
        if relief_factor != 1.0 else None
    )
    box = offsets(radius)
    weight = 1.0 / len(box)

    def build_op(relative: Path, json_content: ty.Dict, operator: str,
                 first: ty.Any, second: ty.Any) -> ty.Dict:
        if binary_keys is None:
            return climate_patch.binary(
                relative, json_content, operator, first, second)
        return {'type': operator, binary_keys[0]: first, binary_keys[1]: second}

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        if scale_leaves is not None:
            json_content = scale_leaves(relative, json_content)

        found = _find_splines(json_content)
        if len(found) != 1:
            raise TypeError(
                f'Expected one factor spline in {relative}, found {len(found)}'
            )
        path, spline = found[0]

        terms = []
        for dx, dz in box:
            term = copy.deepcopy(spline)
            if (dx, dz) != (0, 0):
                name = tag(dx, dz)
                mapping = {
                    f'minecraft:overworld/{axis}': reference(f'{axis}_{name}')
                    for axis in AXES
                }
                mapping['minecraft:overworld/' + FOLDED] = reference(
                    f'{FOLDED}_{name}')
                _, replaced = _rewrite(term, mapping)
                if replaced == 0:
                    raise KeyError(
                        f'Replaced no axis reference in the {name} copy of '
                        f'{relative}'
                    )
                leftover = _count(term, mapping)
                if leftover:
                    raise KeyError(
                        f'{leftover} unshifted reference(s) left in the {name} '
                        f'copy of {relative}'
                    )
            terms.append(term)

        total = terms[0]
        for term in terms[1:]:
            total = build_op(
                relative, json_content, 'minecraft:add', total, term)
        boxed = build_op(
            relative, json_content, 'minecraft:mul', weight, total)
        if not path:
            # The transcribed 1.18.2 tree is the whole document.
            return boxed
        _replace(json_content, path, boxed)
        return json_content

    return patch
