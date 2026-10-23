"""Structure set spacing of the density-function generation.

Placement lives in `worldgen/structure_set/`, one file per set, and a set is
scaled by the factors of its dimension. `DIMENSION_SCALES` cannot express every
field, so a version patch may pin final values per set, and a structure whose
own fields change is patched in `worldgen/structure/`.
"""

from pathlib import Path
import math
import typing as ty

from .. import dispatch
from .sources import resolve


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
    return dispatch.make(resolve(vanilla_dir, targets, source_overrides), patchers)
