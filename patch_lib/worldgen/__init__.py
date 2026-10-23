"""Shared implementation of the density-function generation of worldgen.

This is the data model 1.18 introduced and every later version keeps: the
climate axes are noise nodes referenced from `noise_router`, the relief is a
set of cubic splines, and structures and placed features live in their own
directories. Versions differ in spelling and in which files exist, not in the
model, so the same functions serve 1.18.2 through 26.3.

A version patch only lists target paths and passes the values from
`patch_lib/tuning.py`, so it imports the flat names re-exported here:

    from patch_lib import worldgen

    worldgen.structure(...)

The modules behind them:

- `sources`: target path -> baseline name under `common/vanilla/<version>/`.
- `climate`: frequency of the climate axes.
- `relief`: the offset, factor and jaggedness splines.
- `structure`: structure set spacing and separation.
- `placed_feature`: the monster room count and height cap.
- `terrain`: the climate and relief patch the main 26.x pack assembles.

The pre-1.18 layout is different enough to live in `patch_lib/worldgen_legacy`.
"""

from .climate import nether_climate, noise_frequency, overworld_climate
from .placed_feature import placed_feature
from .relief import (
    relief_above_one,
    relief_positive,
    relief_scale,
    terrain_shaper_reference,
    unchanged,
)
from .sources import source_name
from .structure import structure
from .terrain import terrain

__all__ = [
    'nether_climate',
    'noise_frequency',
    'overworld_climate',
    'placed_feature',
    'relief_above_one',
    'relief_positive',
    'relief_scale',
    'source_name',
    'structure',
    'terrain',
    'terrain_shaper_reference',
    'unchanged',
]

