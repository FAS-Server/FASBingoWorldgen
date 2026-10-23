"""1.18.2 placed feature patch: which feature is retuned, and by what.

The counts live in `patch_lib/tuning.py`. 1.18.2 splits the monster room into
the same shallow and deep placed features as 26.x, and both use a `count` entry
plus a `height_range` entry, so the shared implementation applies unchanged.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/1_18_2')

PLACED_FEATURE_DIR = Path('data/minecraft/worldgen/placed_feature')

reference_file, process_single, process_multi = worldgen.placed_feature(
    vanilla_dir=VANILLA_DIR,
    placed_feature_dir=PLACED_FEATURE_DIR,
    rules=tuning.PLACED_FEATURE_RULES,
)
