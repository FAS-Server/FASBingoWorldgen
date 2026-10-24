"""1.21 placed feature patch: which feature is retuned, and by what.

The counts live in `patch_lib/tuning.py` and are shared by every patched
version. 1.21 places the monster room with the same `count` and `height_range`
entries as 1.18.2, and the two files did not change, so they keep the 1.18.2
baseline. Only the target directory belongs to a version.
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
