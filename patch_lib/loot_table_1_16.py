"""Parse vanilla loot tables written in the 1.16 data format.

Only parsing lives here: the result is a version-neutral structure that each
version's patch converts to its own JSON format. Anything the parser does not
recognize raises, so a new table cannot be silently mis-read.
"""

import re
import typing as ty
from dataclasses import dataclass

# 1.16 stores potion data as NBT. Only a single Potion tag is supported.
_POTION_TAG = re.compile(r'^\{Potion:"(?P<potion>[^"]+)"\}$')

_POOL_FIELDS = {'rolls', 'entries'}
_ENTRY_FIELDS = {'type', 'name', 'weight', 'functions'}


@dataclass(frozen=True)
class Count:
    minimum: float
    maximum: float


@dataclass(frozen=True)
class Entry:
    item: str
    weight: int
    count: ty.Optional[Count] = None
    potion: ty.Optional[str] = None
    enchantments: ty.Tuple[str, ...] = ()


@dataclass(frozen=True)
class Pool:
    rolls: float
    entries: ty.Tuple[Entry, ...]


@dataclass(frozen=True)
class Table:
    type: str
    pools: ty.Tuple[Pool, ...]


def parse(table: ty.Dict) -> Table:
    '''Converts a deserialized 1.16 loot table into the neutral structure.'''
    pools = []
    for pool in table.get('pools', []):
        _expect_fields(pool, _POOL_FIELDS, 'pool')
        pools.append(Pool(
            rolls=float(pool.get('rolls', 1)),
            entries=tuple(_parse_entry(entry) for entry in pool.get('entries', [])),
        ))
    return Table(type=table['type'], pools=tuple(pools))


def _parse_entry(entry: ty.Dict) -> Entry:
    _expect_fields(entry, _ENTRY_FIELDS, 'entry')
    if entry.get('type') != 'minecraft:item':
        raise ValueError(f'Unsupported 1.16 entry type: {entry.get("type")!r}')
    fields: ty.Dict[str, ty.Any] = {}
    for function in entry.get('functions', []):
        _parse_function(fields, function)
    return Entry(item=entry['name'], weight=entry['weight'], **fields)


def _parse_function(fields: ty.Dict[str, ty.Any], function: ty.Dict) -> None:
    name = function['function']
    if name == 'minecraft:set_nbt':
        _expect_fields(function, {'function', 'tag'}, 'function')
        tag = function.get('tag', '')
        match = _POTION_TAG.match(tag)
        if match is None:
            raise ValueError(f'Unsupported 1.16 set_nbt tag: {tag!r}')
        fields['potion'] = match.group('potion')
    elif name == 'minecraft:enchant_randomly':
        _expect_fields(function, {'function', 'enchantments'}, 'function')
        enchantments = function.get('enchantments')
        if not enchantments:
            raise ValueError('1.16 enchant_randomly carries no enchantments')
        fields['enchantments'] = tuple(enchantments)
    elif name == 'minecraft:set_count':
        _expect_fields(function, {'function', 'count'}, 'function')
        count = function.get('count')
        if not isinstance(count, dict) or count.get('type') != 'minecraft:uniform':
            raise ValueError(f'Unsupported 1.16 set_count count: {count!r}')
        fields['count'] = Count(float(count['min']), float(count['max']))
    else:
        raise ValueError(f'Unsupported 1.16 loot function: {name!r}')


def _expect_fields(value: ty.Dict, allowed: ty.Set[str], owner: str) -> None:
    unknown = set(value) - allowed
    if unknown:
        raise ValueError(f'Unsupported 1.16 {owner} fields: {sorted(unknown)}')
