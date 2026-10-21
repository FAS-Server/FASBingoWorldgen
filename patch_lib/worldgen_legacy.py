"""Shared implementation of the pre-1.18 worldgen patches.

Before 1.18 the data format differs from the one `worldgen_26` handles:

* the overworld biome source is either `vanilla_layered` (1.16, 1.17 vanilla) or
  an inline four-axis `multi_noise` table; there is no `worldgen/biome`-less
  parameter list to reference, so the projected table has to be injected into
  `dimension/overworld.json`;
* climate frequency is `firstOctave` on four inline noise parameters, not
  `xz_scale` on density functions, and the octave weights are spelled out;
* structure placement lives in `noise_settings/<dimension>.json` under
  `structures`, one copy per dimension, not in `structure_set/`;
* the monster room is a decorated feature nested in `configured_feature/`.

Everything that is a value lives in `patch_lib/tuning.py`; the target paths and
the lists of entries stay in the version patch.
"""

from pathlib import Path
import math
import typing as ty

from . import dispatch, paths


def _strip_namespace(name: str) -> str:
    return name.split(':', 1)[-1]


def _noise(axis: str, parameters: ty.Tuple[int, ty.Iterable[float]]) -> ty.Dict:
    first_octave, amplitudes = parameters
    amplitudes = list(amplitudes)
    highest = first_octave + len(amplitudes) - 1
    if highest > 0:
        # 1.16.5 silently drops these levels, 1.17.1 raises; both mean the
        # parameters are not doing what they say.
        raise ValueError(
            f'{axis} noise reaches octave {highest}; the pre-1.18 source only '
            f'supports octaves <= 0'
        )
    return {'firstOctave': first_octave, 'amplitudes': amplitudes}


def octave_shift(xz_scale: float, vanilla_scale: float = 0.25) -> int:
    '''
    Converts an `xz_scale` multiple into a `firstOctave` shift.

    The old noise parameters have no scale, only an octave: one octave doubles
    the frequency. A target that is not a power of two cannot be expressed, so
    it raises instead of silently rounding to a different density.
    '''
    ratio = xz_scale / vanilla_scale
    shift = math.log2(ratio)
    rounded = round(shift)
    if abs(shift - rounded) > 1e-9:
        raise ValueError(f'{ratio:g}x is not a power of two; use explicit octaves')
    return int(rounded)


# Tiers the projection generator writes; a patch picks one through `tuning`.
BIOME_TABLE_TIERS = ('full', 'balanced', 'lite')


def overworld_biome_source(
        *,
        dimension_target: Path,
        vanilla_source: Path,
        table_dir: Path,
        tier: str,
        climate: ty.Mapping[str, ty.Tuple[int, ty.Iterable[float]]],
        octave_shift: int,
        seed: int,
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the patch that replaces the overworld biome source.

    args:
    - dimension_target: `data/minecraft/dimension/overworld.json`, relative to
      the pack root.
    - vanilla_source: the vanilla dimension file under COMMON_PATH. It keeps
      everything but the biome source (generator seed, settings, type).
    - table_dir: directory under COMMON_PATH holding the projected tables of
      this target version, e.g. `biome_source/1_16_5`. Each target has its own
      because its biome list decides which biomes the projection may keep.
    - tier: which table in `table_dir` to inject; it is read as an auxiliary
      source and never written to the pack.
    - climate: legacy axis -> (firstOctave, amplitudes) of the base noise, in
      the order the table spells its axes.
    - octave_shift: octaves added to every axis of `climate`. One octave doubles
      the frequency; the old parameters have no scale, so this is the only way
      to raise it.
    - seed: written to `generator.seed` and to the biome source's `seed`. A
      datapack dimension replaces the preset dimension together with its seed
      before 1.19, and data cannot reference the world seed, so this constant
      is what the noise is actually built from.

    The vanilla file is expected to use `vanilla_layered`; an already patched
    file raises instead of being patched twice.
    '''
    if tier not in BIOME_TABLE_TIERS:
        raise ValueError(f'Unknown biome table tier: {tier!r}')
    table_source = Path(table_dir) / f'overworld_{tier}.json'
    table_target = dimension_target.with_name(f'__{dimension_target.name}')
    root = Path()

    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]):
        nonlocal root
        root = paths.package_root(patch_path)
        return [
            ('COMMON', vanilla_source, root / dimension_target),
            ('COMMON', table_source, root / table_target),
        ]

    def process_multi(content: ty.List[ty.Tuple[Path, ty.Dict]]) -> ty.List[ty.Tuple[Path, ty.Dict]]:
        contents = dict(content)
        relative = dimension_target
        dimension = contents[root / dimension_target]
        table = contents[root / table_target]

        generator = dimension['generator']
        biome_source = generator['biome_source']
        if biome_source.get('type') != 'minecraft:vanilla_layered':
            raise TypeError(
                f'Expected vanilla_layered in {relative}, '
                f'got {biome_source.get("type")!r}'
            )
        axes = tuple(table['axes'])
        if axes != tuple(climate):
            raise TypeError(f'Table in {table_source} is keyed by {axes}, expected {tuple(climate)}')

        patched: ty.Dict[str, ty.Any] = {
            'type': 'minecraft:multi_noise',
            # pre-1.18 data cannot reference the world seed, and the dimension
            # file replaces the preset one including its seed, so the noise is
            # built from this constant; keep both entries equal
            'seed': seed,
        }
        patched.update({
            f'{axis}_noise': _noise(axis, (first_octave + octave_shift, amplitudes))
            for axis, (first_octave, amplitudes) in climate.items()
        })
        patched['biomes'] = table['biomes']
        generator['seed'] = seed
        generator['biome_source'] = patched
        return [(root / relative, dimension)]

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        return process_multi([content])[0]

    return reference_file, process_single, process_multi


def nether_climate(
        *,
        dimension_target: Path,
        vanilla_source: Path,
        fields: ty.Iterable[str],
        octave_shift: int,
        seed: int,
    ) -> ty.Tuple[ty.Callable, ty.Callable]:
    '''
    Patcher for `dimension/the_nether.json`: raises the climate frequency by
    shifting `firstOctave`.

    One octave doubles the frequency, so a 4x target is a shift of 2. The
    fields listed are the ones the nether preset entries actually vary on; the
    other two carry no information for it. `seed` is written to both
    `generator.seed` and the biome source's `seed`, for the reason given in
    `overworld_biome_source`.
    '''
    fields = tuple(fields)

    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]):
        return ('COMMON', vanilla_source, paths.package_root(patch_path) / dimension_target)

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        target, dimension = content
        generator = dimension['generator']
        biome_source = generator['biome_source']
        if biome_source.get('type') != 'minecraft:multi_noise':
            raise TypeError(
                f'Expected multi_noise in {dimension_target}, '
                f'got {biome_source.get("type")!r}'
            )
        for field in fields:
            noise = biome_source.get(f'{field}_noise')
            if noise is None:
                raise KeyError(f'{dimension_target} has no {field}_noise')
            noise['firstOctave'] = noise['firstOctave'] + octave_shift
        generator['seed'] = seed
        biome_source['seed'] = seed
        return (target, dimension)

    return reference_file, process_single


def structure(
        *,
        vanilla_dir: Path,
        settings: ty.Mapping[str, Path],
        dimension_scales: ty.Mapping[str, ty.Mapping[str, float]],
        excluded: ty.Iterable[str],
        stronghold_fields: ty.Optional[ty.Dict[str, ty.Any]] = None,
        source_overrides: ty.Mapping[Path, Path] = {},
    ) -> ty.Tuple[ty.Callable, ty.Callable, ty.Callable]:
    '''
    Builds the structure patch for the pre-1.18 layout.

    Each dimension carries a full copy of the structure table in its
    `noise_settings` file, so the same set is scaled with its own dimension's
    factors. `excluded` names the sets a version keeps at their vanilla values
    (`mineshaft`, `monument`, `nether_fossil`); the name has no namespace.
    `stronghold_fields` replaces the ring parameters, which live outside the
    per-structure table.
    '''
    excluded = frozenset(excluded)
    unknown = set(settings) - set(dimension_scales)
    if unknown:
        raise KeyError(f'No scale for dimension(s): {sorted(unknown)}')

    def patch_for(dimension: str) -> dispatch.Patcher:
        scales = dimension_scales[dimension]

        def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
            structures = json_content['structures']
            table = structures['structures']
            for name, fields in table.items():
                if _strip_namespace(name) in excluded:
                    continue
                fields['spacing'] = _scale(fields['spacing'], scales['spacing'], minimum=1)
                fields['separation'] = _scale(
                    fields['separation'], scales['separation'], minimum=0
                )
                _validate_placement(relative, name, fields)
            if stronghold_fields is not None and 'stronghold' in structures:
                structures['stronghold'].update(stronghold_fields)
            return json_content

        return patch

    targets = list(settings.values())
    patchers = {
        target: patch_for(dimension)
        for dimension, target in settings.items()
    }
    resolved = {
        target: source_overrides.get(target, vanilla_dir / f'noise_settings__{dimension}.json')
        for dimension, target in settings.items()
    }
    return dispatch.make(resolved, patchers)


def _scale(value: int, factor: float, minimum: int) -> int:
    '''Rounds half up and clamps to `minimum`; round() is banker's rounding.'''
    return max(minimum, int(math.floor(value * factor + 0.5)))


def _validate_placement(relative: Path, name: str, fields: ty.Dict) -> None:
    if fields['separation'] >= fields['spacing']:
        raise ValueError(
            f'{relative}: {name} separation {fields["separation"]} must be less '
            f'than spacing {fields["spacing"]}'
        )


def _find_type(node: ty.Any, kind: str) -> ty.Optional[ty.Dict]:
    '''Returns the first dict of the given type anywhere below `node`.'''
    if isinstance(node, dict):
        if node.get('type') == kind:
            return node
        for value in node.values():
            found = _find_type(value, kind)
            if found is not None:
                return found
    elif isinstance(node, list):
        for value in node:
            found = _find_type(value, kind)
            if found is not None:
                return found
    return None


def monster_room(
        *,
        vanilla_source: Path,
        target: Path,
        count: int,
        max_y: int,
    ) -> ty.Tuple[ty.Callable, ty.Callable]:
    '''
    Builds the monster room patch for the decorated-feature layout.

    `count` is the outer count decorator (how many times a chunk attempts the
    feature); `max_y` caps the height range. The feature nests decorators at
    several depths (count, square, range, decorated), so the range is located by
    type. 1.16 spells the range as a plain `maximum`, while 1.17 uses a
    `height` descriptor whose upper end is `below_top` by default.
    '''
    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]):
        return ('COMMON', vanilla_source, paths.package_root(patch_path) / target)

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        target_path, json_content = content
        if _find_type(json_content, 'minecraft:monster_room') is None:
            raise TypeError(f'No monster_room feature in {target}')
        outer = json_content['config']['decorator']
        if outer.get('type') != 'minecraft:count':
            raise TypeError(f'Expected a count decorator in {target}, got {outer.get("type")!r}')
        outer['config']['count'] = count
        height = _find_type(json_content, 'minecraft:range')
        if height is None:
            raise TypeError(f'No range decorator in {target}')
        config = height['config']
        if 'maximum' in config:
            config['maximum'] = max_y
        elif 'height' in config:
            config['height']['max_inclusive'] = {'absolute': max_y}
        else:
            raise TypeError(f'Unrecognized range in {target}: {sorted(config)}')
        return (target_path, json_content)

    return reference_file, process_single


def probability(
        *,
        vanilla_source: Path,
        target: Path,
        value: float,
    ) -> ty.Tuple[ty.Callable, ty.Callable]:
    '''Patcher for a configured structure feature's `config.probability`.'''
    def reference_file(patch_path: Path, patch_version_config: ty.Dict[str, str]):
        return ('COMMON', vanilla_source, paths.package_root(patch_path) / target)

    def process_single(content: ty.Tuple[Path, ty.Dict]) -> ty.Tuple[Path, ty.Dict]:
        target_path, json_content = content
        config = json_content['config']
        if 'probability' not in config:
            raise KeyError(f'No probability in {target}')
        config['probability'] = value
        return (target_path, json_content)

    return reference_file, process_single
