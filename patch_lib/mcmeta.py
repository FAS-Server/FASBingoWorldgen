"""Shared implementation of the pack.mcmeta patch.

The structure of pack.mcmeta changes between MC versions, so the code that writes
it lives here and the per-version data stays in the patch. A version that changes
the structure only needs this file to be updated.
"""

from pathlib import Path
import typing as ty


def make(
        pack_format: int,
        supported_formats: ty.Optional[ty.Dict[str, int]] = None,
        overlays: ty.Optional[ty.List[ty.Dict]] = None
    ) -> ty.Tuple[ty.Callable, ty.Callable]:
    '''
    Creates the functions a pack.mcmeta patch exposes.

    args:
    - pack_format: written into pack/pack_format.
    - supported_formats: written into pack/supported_formats when given.
    - overlays: list of overlay entries, written into overlays/entries when given.

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
        json_content['pack']['pack_format'] = pack_format
        if supported_formats is not None:
            json_content['pack']['supported_formats'] = supported_formats
        if overlays is not None:
            json_content['overlays'] = {'entries': overlays}
        json_content['pack']['version'] = captured['version']
        return (new_path, json_content)

    return reference_file, process_single
