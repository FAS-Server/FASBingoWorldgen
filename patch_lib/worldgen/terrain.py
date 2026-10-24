"""The combined terrain patch of a version with the plain layout.

A version can use this when its vanilla `offset` and `jaggedness` are density
function files of their own, so the relief knobs have something to scale, and
the climate axes are the only fields inlined in `noise_router`.

Versions that need something else assemble their own table from the same
building blocks: one whose relief spline is still inlined has to transcribe the
points first (`relief.terrain_shaper_reference`), and an overlay replaces
individual files rather than the whole set.
"""

from pathlib import Path
import typing as ty

from .. import dispatch
from . import climate as climate_patch
from . import relief as relief_patch
from .sources import resolve


def terrain(
        *,
        vanilla_dir: Path,
        overworld_settings: Path,
        nether_settings: Path,
        offset: Path,
        factor: Path,
        jaggedness: Path,
        density_functions: ty.Iterable[Path],
        climate_functions: ty.Iterable[Path] = (),
        xz_scale_overworld: float,
        inline_climate_fields: ty.Iterable[str],
        xz_scale_nether: float,
        nether_climate_fields: ty.Iterable[str],
        relief_highland: float,
        relief_factor: float,
        relief_jagged: float,
        underground_relief: float,
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the terrain patch: climate frequency, relief splines and the
    underground depth axis.

    `density_functions` are the named functions the biome source and the terrain
    share; `climate_functions` are climate fields that a later version moved
    out of `noise_router` into files of their own, so they are scaled the same
    way instead of being patched inside the settings file.

    A relief parameter of 1.0 drops its file from the pack instead of emitting a
    copy identical to vanilla, so it also decides whether the file is a source.
    '''
    density_functions = tuple(density_functions)
    climate_functions = tuple(climate_functions)

    targets = [overworld_settings, nether_settings]
    if relief_highland != 1.0:
        targets.append(offset)
    if relief_factor != 1.0:
        targets.append(factor)
    if relief_jagged != 1.0:
        targets.append(jaggedness)
    targets.extend(density_functions)
    targets.extend(climate_functions)

    patch_overworld = climate_patch.overworld_climate(
        inline_climate_fields=inline_climate_fields,
        xz_scale=xz_scale_overworld,
        underground_relief=underground_relief,
    )
    patch_nether = climate_patch.nether_climate(
        climate_fields=nether_climate_fields,
        xz_scale=xz_scale_nether,
    )
    patch_noise = climate_patch.noise_frequency(xz_scale=xz_scale_overworld)

    patchers: ty.Dict[Path, dispatch.Patcher] = {
        overworld_settings: patch_overworld,
        nether_settings: patch_nether,
    }
    if relief_highland != 1.0:
        patchers[offset] = relief_patch.relief_positive(relief_highland)
    if relief_factor != 1.0:
        patchers[factor] = relief_patch.relief_above_one(relief_factor)
    if relief_jagged != 1.0:
        patchers[jaggedness] = relief_patch.relief_scale(relief_jagged)
    patchers.update({target: patch_noise for target in density_functions})
    patchers.update({target: patch_noise for target in climate_functions})

    return dispatch.make(
        resolve(vanilla_dir, targets, source_overrides), patchers
    )
