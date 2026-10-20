"""Shared implementation of the loot table patches.

Only two entries are touched, so the tables are never rewritten as a whole:

- the enderman pearl, whose minimum count is raised to remove the luck;
- the bartering pearl, whose weight and count are restored to the 1.16.1 values
  while every other trade stays as the target version ships it.

Entries are located by item name, so trades added by later versions do not move
the target, and a missing or duplicated entry raises instead of silently
patching the wrong one.
"""

from pathlib import Path
import typing as ty

from . import dispatch


def _entry(relative: Path, json_content: ty.Dict, item: str) -> ty.Dict:
    entries = [
        entry for pool in json_content['pools'] for entry in pool['entries']
        if entry.get('name') == item
    ]
    if len(entries) != 1:
        raise KeyError(f'Expected one {item} entry in {relative}, found {len(entries)}')
    return entries[0]


def _function(relative: Path, entry: ty.Dict, function: str, item: str) -> ty.Dict:
    '''
    Returns the one operation named `function` on an entry.

    26.1 and 26.2 spell the operations as a `functions` list whose entries are
    named by `function`; 26.3 renames the field to `modifier`, allows a single
    object instead of a list, and names the operation by `type`.
    '''
    if 'modifier' in entry:
        modifier = entry['modifier']
        if isinstance(modifier, dict):
            operations = [modifier]
        elif isinstance(modifier, list):
            operations = modifier
        else:
            raise TypeError(
                f'Unexpected modifier in {relative} on {item}: {modifier!r}'
            )
    else:
        operations = entry.get('functions', [])
    functions = [
        candidate for candidate in operations
        if candidate.get('function', candidate.get('type')) == function
    ]
    if len(functions) != 1:
        raise KeyError(
            f'Expected one {function} on {item} in {relative}, found {len(functions)}'
        )
    return functions[0]


def make(
        *,
        vanilla_dir: Path,
        sources: ty.Mapping[Path, str],
        enderman_target: Path,
        bartering_target: Path,
        min_enderman_pearl: float,
        pearl_item: str,
        pearl_weight: int,
        pearl_min: float,
        pearl_max: float,
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the loot table patch.

    args:
    - sources: target path relative to the pack root -> baseline file name under
      `common/vanilla/<version>/`. Loot table names drop their sub-directory, so
      they cannot be derived from the target path and are stated by the patch.
    - min_enderman_pearl: vanilla drops 0..1 pearls; the project guarantees this
      many.
    - pearl_item, pearl_weight, pearl_min, pearl_max: the bartering entry and the
      1.16.1 values restored on it.
    '''
    def patch_enderman(relative: Path, json_content: ty.Dict) -> ty.Dict:
        entry = _entry(relative, json_content, pearl_item)
        count = _function(relative, entry, 'minecraft:set_count', pearl_item)['count']
        if count['min'] != min_enderman_pearl:
            count['min'] = min_enderman_pearl
        return json_content

    def patch_bartering(relative: Path, json_content: ty.Dict) -> ty.Dict:
        entry = _entry(relative, json_content, pearl_item)
        # Assign only when the value differs, so a table whose numbers already
        # match keeps its own int/float spelling.
        if entry['weight'] != pearl_weight:
            entry['weight'] = pearl_weight
        count = _function(relative, entry, 'minecraft:set_count', pearl_item)['count']
        if count['min'] != pearl_min:
            count['min'] = pearl_min
        if count['max'] != pearl_max:
            count['max'] = pearl_max
        return json_content

    patchers: ty.Dict[Path, dispatch.Patcher] = {
        enderman_target: patch_enderman,
        bartering_target: patch_bartering,
    }
    resolved: ty.Dict[Path, Path] = {
        target: source_overrides.get(target, vanilla_dir / name)
        for target, name in sources.items()
    }
    return dispatch.make(resolved, patchers)

