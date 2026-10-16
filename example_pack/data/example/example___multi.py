from pathlib import Path
import typing as ty

TYPE = 'json'

# Multi-file patch example: reads several files from `common/example_source/`
# and writes one output file per source, next to this patch.


def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]) \
        -> ty.Union[ty.Tuple[str, Path, Path], ty.List[ty.Tuple[str, Path, Path]], None]:
    source_dir = Path('example_source')

    return [
        ('COMMON', source_dir / 'alpha.json', patch_path.parent / 'alpha.json'),
        ('COMMON', source_dir / 'beta.json', patch_path.parent / 'beta.json'),
    ]


def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
    for new_path, json_content in content:
        json_content['patched_by'] = 'example_pack'
    return content
