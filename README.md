# FASBingoWorldgen

World generation datapack for Bingo game.


## Changes to Vanilla worldgen

- Made biomes in overworld and the nether a lot smaller to keep up with the fast pace of Bingo game.
- Made mountains lower and valleys shallower.
- Made structures generate more in overworld, the nether and the end, see [Modified Features](##Modified%20Structures).


## Known limitations

### 1.16.5 / 1.17.1: the world seed does not change terrain or biomes

Before 1.19, a dimension definition carries its own generator seed, and a data pack dimension overrides the dimension of the world preset together with that seed. Data cannot reference the world seed, so the seed is a constant baked into each version's `dimension/overworld.json` and `dimension/the_nether.json`: every world of a given version generates the same terrain and the same biome layout, and only structures, features and loot follow the seed entered at world creation. The constant differs per version, so 1.16.5 and 1.17.1 still generate different worlds from each other. 1.18.2 and later are not affected: 1.19 removed the field and always uses the world seed.


## Changes to Vanilla Loot Table

- Replaced loot table of piglin bartering with 1.16.1 one.
- Enderman drops at leat 1 ender pearl.


## Modified Features

### Placed Features

- monster_room
- monster_room_deep

### Structure Set

- ancient_city (size & density)
- buried_treasures
- desert_pyramids
- igloos
- jungle_temples
- ocean_ruins
- ruined_portals
- shipwrecks
- villages
- woodland_mansions
- strongholds
- nether_complexes
- end_cities