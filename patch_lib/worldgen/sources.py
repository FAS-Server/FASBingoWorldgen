"""Target path -> baseline name for the density-function generation.

Every target sits under `data/minecraft/worldgen/<kind>/` and its vanilla copy is
flattened under `common/vanilla/<version>/` as `<kind>__<name>.json`, which is
what `source_name` builds. A patch therefore only lists target paths; the
baseline name is derived.
"""

from pathlib import Path
import typing as ty

WORLDGEN_DIR = 'worldgen'


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


def resolve(
        vanilla_dir: Path,
        targets: ty.Iterable[Path],
        overrides: ty.Mapping[Path, Path],
    ) -> ty.Dict[Path, Path]:
    '''
    Maps every target to its baseline, letting `overrides` win.

    A patch whose sources are not vanilla files (a transcribed spline, for
    example) passes them through `overrides`, so the table stays one lookup.
    '''
    return {
        target: overrides.get(target, vanilla_dir / source_name(target))
        for target in targets
    }
