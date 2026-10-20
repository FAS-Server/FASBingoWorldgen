"""Shared implementation of the pack.mcmeta patch.

`common/pack.mcmeta` holds the pack description and any other field shared by
every version. A patch supplies only the format fields and, when needed, a
description or overlays of its own.
"""

from pathlib import Path
import typing as ty


def make(
        pack_format: ty.Optional[int] = None,
        supported_formats: ty.Optional[ty.Dict[str, int]] = None,
        overlays: ty.Optional[ty.List[ty.Dict]] = None,
        min_format: ty.Optional[ty.List[int]] = None,
        max_format: ty.Optional[ty.List[int]] = None,
        description: ty.Optional[str] = None
    ) -> ty.Tuple[ty.Callable, ty.Callable]:
    '''
    Creates the functions a pack.mcmeta patch exposes.

    args:
    - pack_format: written into pack/pack_format. When None, pack_format is
      removed from the source; required for the min_format/max_format scheme.
    - supported_formats: written into pack/supported_formats when given.
    - overlays: list of overlay entries, written into overlays/entries when given.
    - min_format: written into pack/min_format when given, e.g. [101, 1].
    - max_format: written into pack/max_format when given, e.g. [101, 1].
    - description: written into pack/description when given, otherwise the
      description of common/pack.mcmeta is kept.

    returns:
    - (reference_file, process_single), to be exposed by the patch module.
    '''
    # the datapack version is only known while reference_file runs
    captured: ty.Dict[str, str] = {}

    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]):
        file_name = patch_path.with_suffix('').with_name(patch_path.stem.replace('___', '.'))
        captured['version'] = patch_version_config['version']
        return ('COMMON', Path('pack.mcmeta'), file_name)

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        new_path, json_content = content
        pack = json_content['pack']
        if pack_format is None:
            pack.pop('pack_format', None)
        else:
            pack['pack_format'] = pack_format
        if supported_formats is not None:
            pack['supported_formats'] = supported_formats
        if min_format is not None:
            pack['min_format'] = min_format
        if max_format is not None:
            pack['max_format'] = max_format
        if description is not None:
            pack['description'] = description
        if overlays is not None:
            json_content['overlays'] = {'entries': overlays}
        pack['version'] = captured['version']
        return (new_path, json_content)

    return reference_file, process_single
