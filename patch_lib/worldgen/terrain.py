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
from . import smoothing as smoothing_patch
from .sources import resolve


def terrain(
        *,
        vanilla_dir: Path,
        overworld_settings: Path,
        nether_settings: ty.Optional[Path] = None,
        offset: Path,
        factor: Path,
        jaggedness: Path,
        density_functions: ty.Iterable[Path],
        climate_functions: ty.Iterable[Path] = (),
        xz_scale_overworld: float,
        inline_climate_fields: ty.Iterable[str],
        xz_scale_nether: ty.Optional[float] = None,
        nether_climate_fields: ty.Iterable[str] = (),
        relief_highland: float,
        relief_factor: float,
        relief_jagged: float,
        underground_relief: float,
        factor_smoothing_radius: int = 0,
        ridges_folded: ty.Optional[Path] = None,
        smoothing_sources: ty.Mapping[str, Path] = {},
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

    A `factor_smoothing_radius` above 0 adds the smoothed `factor` and one
    shifted copy of each climate axis per surrounding quart; the copies are new
    files under their own namespace, and their baselines default to the axes
    the version already patches. `ridges_folded` is the vanilla folded file the
    spline reads, or None when the version has none of its own (1.18.2 spells
    the folded value inside `terrain_shaper_spline`); `smoothing_sources`
    overrides a copy's baseline when it does not come from `vanilla_dir`.

    An overlay that replaces only the overworld passes `nether_settings=None`;
    the nether target and its knobs are then left out, so the main pack keeps
    providing the nether.
    '''
    density_functions = tuple(density_functions)
    climate_functions = tuple(climate_functions)
    smoothing_sources = dict(smoothing_sources)
    source_overrides = dict(source_overrides)
    smoothing = factor_smoothing_radius > 0
    if factor_smoothing_radius < 0:
        raise ValueError(
            f'factor_smoothing_radius must not be negative, '
            f'got {factor_smoothing_radius}'
        )

    if nether_settings is None:
        if xz_scale_nether is not None or nether_climate_fields:
            raise ValueError(
                'nether_settings is None, so xz_scale_nether and '
                'nether_climate_fields must be omitted'
            )
    elif xz_scale_nether is None:
        raise ValueError('nether_settings needs xz_scale_nether')

    targets = [overworld_settings]
    if nether_settings is not None:
        targets.append(nether_settings)
    if relief_highland != 1.0:
        targets.append(offset)
    if relief_factor != 1.0 and not smoothing:
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
    patch_noise = climate_patch.noise_frequency(xz_scale=xz_scale_overworld)

    patchers: ty.Dict[Path, dispatch.Patcher] = {
        overworld_settings: patch_overworld,
    }
    if nether_settings is not None:
        patchers[nether_settings] = climate_patch.nether_climate(
            climate_fields=nether_climate_fields,
            xz_scale=xz_scale_nether,
        )
    if relief_highland != 1.0:
        patchers[offset] = relief_patch.relief_positive(relief_highland)
    if relief_factor != 1.0 and not smoothing:
        patchers[factor] = relief_patch.relief_above_one(relief_factor)
    if relief_jagged != 1.0:
        patchers[jaggedness] = relief_patch.relief_scale(relief_jagged)
    patchers.update({target: patch_noise for target in density_functions})
    patchers.update({target: patch_noise for target in climate_functions})

    if smoothing:
        targets.append(factor)
        patchers[factor] = smoothing_patch.smoothed_factor(
            radius=factor_smoothing_radius,
            relief_factor=relief_factor,
        )
        copies = smoothing_patch.smoothing_targets(
            radius=factor_smoothing_radius,
            include_ridges_folded=ridges_folded is not None,
        )
        for target, (axis, name, dx, dz) in copies.items():
            targets.append(target)
            if axis == smoothing_patch.FOLDED:
                patchers[target] = smoothing_patch.shifted_ridges_folded(name=name)
            else:
                patchers[target] = smoothing_patch.shifted_axis(
                    xz_scale=xz_scale_overworld, dx=dx, dz=dz)
            source_overrides[target] = smoothing_sources.get(
                axis, vanilla_dir / smoothing_patch.baseline_name(axis))

    return dispatch.make(
        resolve(vanilla_dir, targets, source_overrides), patchers
    )
