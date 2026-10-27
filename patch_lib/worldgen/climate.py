"""Climate frequency of the density-function generation.

The overworld reads five axes. `temperature` and `vegetation` are noise nodes
inlined in `noise_router`, so they are scaled there; `continents`, `erosion` and
`ridges` are references to named density functions, so each file carries the
frequency for the biome source and the terrain at once, and the two cannot
drift.

Versions spell the nodes differently: 1.18 through 26.2 use `shifted_noise`
wrapped in `flat_cache`, 26.3 renames them to `noise` wrapped in `cache` and
moves the two climate fields into files of their own. 26.3 also renames the
operands of the binary nodes from `argument1`/`argument2` to `left`/`right`.
Each spelling is read back from the document itself, which is why a version
patch only lists its own target paths.
"""

from pathlib import Path
import typing as ty

from .. import dispatch

# Density function spellings of the noise node.
NOISE_TYPES = ('minecraft:noise', 'minecraft:shifted_noise')

# Cache wrappers around a noise node. 26.3 renamed `flat_cache` to `cache` and
# its `argument` key to `input`.
CACHE_TYPES = ('minecraft:cache', 'minecraft:flat_cache')

# Binary operation nodes. 26.3 renamed their operands from
# `argument1`/`argument2` to `left`/`right`.
BINARY_TYPES = (
    'minecraft:add',
    'minecraft:sub',
    'minecraft:mul',
    'minecraft:min',
    'minecraft:max',
)

# Operand key spellings of a binary node, newest first.
OPERAND_KEYS = (
    ('left', 'right'),
    ('argument1', 'argument2'),
)


def noise_node(relative: Path, json_content: ty.Dict) -> ty.Dict:
    '''
    Returns the noise node of a density function.

    Some functions are the noise node itself (`overworld/temperature.json` from
    26.3 on), others wrap it in a cache whose key is `input` from 26.3 and
    `argument` before it.
    '''
    node = json_content
    if node.get('type') in CACHE_TYPES:
        keys = [key for key in ('input', 'argument') if key in node]
        if len(keys) != 1:
            raise TypeError(
                f'Expected one of input/argument in {relative}, got {sorted(node)}'
            )
        node = node[keys[0]]
    if node.get('type') not in NOISE_TYPES:
        raise TypeError(
            f'Expected a noise density function in {relative}, '
            f'got {node.get("type")!r}'
        )
    return node


def _scale_inline_fields(
        relative: Path,
        router: ty.Dict,
        fields: ty.Iterable[str],
        xz_scale: float,
    ) -> None:
    '''Sets `xz_scale` on the noise nodes inlined in a noise router.'''
    for field in fields:
        noise = router[field]
        if noise.get('type') not in NOISE_TYPES:
            raise TypeError(
                f'Expected an inlined noise in {relative} {field}, '
                f'got {noise.get("type")!r}'
            )
        noise['xz_scale'] = xz_scale


def operand_keys(relative: Path, json_content: ty.Dict) -> ty.Tuple[str, str]:
    '''
    Returns the operand key names binary nodes use in this document.

    The version that reads the file decides the spelling, so it is learnt from
    a binary node already present instead of assumed. `overworld/factor.json`
    has no binary node of its own, so the cache wrapper is read instead: it was
    renamed in the same release as the operands, from `flat_cache` to `cache`
    and from `argument1`/`argument2` to `left`/`right`.
    '''
    pending = [json_content]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if node.get('type') in BINARY_TYPES:
                for keys in OPERAND_KEYS:
                    if all(key in node for key in keys):
                        return keys
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    wrapper = _cache_type(relative, json_content)
    return OPERAND_KEYS[0] if wrapper == CACHE_TYPES[0] else OPERAND_KEYS[1]


def _cache_type(relative: Path, json_content: ty.Dict) -> str:
    '''Returns the cache type a document uses, newest spelling first.'''
    pending = [json_content]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            if node.get('type') in CACHE_TYPES:
                return node['type']
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    raise TypeError(
        f'Found neither a binary nor a cache density function in {relative} '
        f'to read the operand keys from'
    )


def binary(
        relative: Path,
        json_content: ty.Dict,
        operator: str,
        first_operand: ty.Any,
        second_operand: ty.Any,
    ) -> ty.Dict:
    '''Builds a binary density function node spelled as the document is.'''
    first, second = operand_keys(relative, json_content)
    return {'type': operator, first: first_operand, second: second_operand}


def overworld_climate(
        *,
        inline_climate_fields: ty.Iterable[str],
        xz_scale: float,
        underground_relief: float,
    ) -> dispatch.Patcher:
    '''
    Patcher for `noise_settings/overworld.json`: scales the inlined climate
    fields and, when asked, rescales the depth axis the biome source samples.

    A climate field is expected to be an inlined noise; the other axes stay as
    references to named density functions, which keeps the biome source and the
    terrain on the same value.

    `underground_relief` wraps `noise_router.depth` in a `mul`, shortening the
    underground biome layers themselves. Only the biome source reads that field,
    so the density and the cave shapes are untouched. The `depth` axis is
    measured down from the surface, so leaving it alone keeps the layers at the
    same relative depth under a lowered mountain.
    '''
    fields = tuple(inline_climate_fields)

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        router = json_content['noise_router']
        _scale_inline_fields(relative, router, fields, xz_scale)
        if underground_relief != 1.0:
            # The biome source samples this field; terrain reads overworld/depth
            # through sloped_cheese. Wrapping the reference therefore rescales
            # the biome depth axis without touching the density.
            if not isinstance(router['depth'], str):
                raise TypeError(
                    f'Expected a reference in {relative} depth, got {router["depth"]!r}'
                )
            router['depth'] = binary(
                relative,
                json_content,
                'minecraft:mul',
                1.0 / underground_relief,
                router['depth'],
            )
        return json_content

    return patch


def nether_climate(
        *,
        climate_fields: ty.Iterable[str],
        xz_scale: float,
    ) -> dispatch.Patcher:
    '''Patcher for `noise_settings/nether.json`: scales the inlined climate fields.'''
    fields = tuple(climate_fields)

    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        _scale_inline_fields(relative, json_content['noise_router'], fields, xz_scale)
        return json_content

    return patch


def noise_frequency(*, xz_scale: float) -> dispatch.Patcher:
    '''
    Patcher for a density function whose noise node carries the frequency.

    The wrapper, if any, only caches; the noise node inside is what the biome
    source and the terrain sample. 26.3 moved the two climate fields
    (`overworld/temperature.json`, `overworld/vegetation.json`) out of
    `noise_router` into files of their own, and this patcher scales them there.
    '''
    def patch(relative: Path, json_content: ty.Dict) -> ty.Dict:
        noise_node(relative, json_content)['xz_scale'] = xz_scale
        return json_content

    return patch
