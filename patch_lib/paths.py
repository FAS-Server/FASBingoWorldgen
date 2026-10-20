"""Pack root of a patch, for packs that also ship overlay directories.

Every patch lives at `<pack_root>/data/<namespace>/...`:

- the main pack has `<pack_root>` = `.`, e.g. `data/minecraft/loot_table__multi.py`;
- an overlay has `<pack_root>` = the overlay directory, e.g.
  `26_2_noise/data/minecraft/terrain__multi.py`.

Targets returned by `reference_file` are relative to the version build root, so
a patch declares them relative to its own pack root and joins them with the
root from this module. One table then serves the main pack and an overlay.
"""

from pathlib import Path

DATA_DIR_NAME = 'data'


def package_root(patch_path: Path) -> Path:
    '''
    Returns the pack root of a patch, relative to the version root.

    args:
    - patch_path: patch path relative to the version source directory.

    returns:
    - `Path()` for a patch in the main pack, or the overlay directory for a
      patch inside an overlay, e.g. `Path('26_2_noise')`.
    '''
    parts = patch_path.parts
    try:
        depth = parts.index(DATA_DIR_NAME)
    except ValueError:
        raise ValueError(f'{patch_path} is not inside a {DATA_DIR_NAME}/ directory') from None
    return Path(*parts[:depth])
