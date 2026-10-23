"""Placed features of the density-function generation.

The monster room is a `placed_feature` here, split into a shallow and a deep
variant; 1.16 and 1.17 nest a decorated feature inside `configured_feature`
instead, which `patch_lib/worldgen_legacy` handles.
"""

from pathlib import Path
import typing as ty

from .. import dispatch
from .sources import resolve


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
    return dispatch.make(resolve(vanilla_dir, targets, source_overrides), patchers)
