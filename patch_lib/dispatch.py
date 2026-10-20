"""Turn two target-keyed tables into the entry points a patch must expose.

A patch declares:

- sources: target path relative to the pack root -> source path relative to
  COMMON_PATH. Targets are relative to the pack root, so one table serves both
  the main pack and an overlay.
- patchers: target path relative to the pack root -> patcher. A target with no
  patcher raises instead of being emitted unchanged.

The pack root is only known while `reference_file` runs, so it is captured
there and used later to turn a collected target back into a relative key.
"""

from pathlib import Path
import typing as ty

from . import paths

Patcher = ty.Callable[[Path, ty.Dict], ty.Dict]


def make(
        sources: ty.Mapping[Path, Path],
        patchers: ty.Mapping[Path, Patcher],
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the functions a multi-file JSON patch exposes.

    args:
    - sources: target path relative to the pack root -> source path relative to
      COMMON_PATH.
    - patchers: target path relative to the pack root -> patcher.

    returns:
    - (reference_file, process_single, process_multi). process_single covers the
      case where the framework collects a single source and therefore calls it
      instead of process_multi.
    '''
    pack_root = Path()

    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
            -> ty.List[ty.Tuple[str, Path, Path]]:
        nonlocal pack_root
        pack_root = paths.package_root(patch_path)
        return [
            ('COMMON', source, pack_root / target)
            for target, source in sources.items()
        ]

    def apply(target: Path, json_content: ty.Dict) -> ty.Tuple[Path, ty.Dict]:
        relative = target.relative_to(pack_root)
        if relative not in patchers:
            raise KeyError(f'No patcher for: {relative}')
        return target, patchers[relative](relative, json_content)

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        return apply(*content)

    def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) \
            -> ty.List[ty.Tuple[Path, ty.Dict]]:
        return [apply(target, json_content) for target, json_content in content]

    return reference_file, process_single, process_multi
