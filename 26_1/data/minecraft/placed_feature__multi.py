"""26.1 placed feature patch: which feature is retuned, and by what.

The counts live in `patch_lib/tuning.py` and are shared by every patched
version. Only the target directory belongs to a version.
"""

from pathlib import Path

from patch_lib import tuning, worldgen

TYPE = 'json'

VANILLA_DIR = Path('vanilla/26_1')

PLACED_FEATURE_DIR = Path('data/minecraft/worldgen/placed_feature')

# Targets are relative to the pack root, so the same table works for the main
# pack and for an overlay.
reference_file, process_single, process_multi = worldgen.placed_feature(
    vanilla_dir=VANILLA_DIR,
    placed_feature_dir=PLACED_FEATURE_DIR,
    rules=tuning.PLACED_FEATURE_RULES,
)
