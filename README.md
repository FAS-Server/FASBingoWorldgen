# FASBingoWorldgen

World generation datapack for Bingo game.

## Supported Versions

| Pack | Minecraft |
| --- | --- |
| `FASBingoWorldgen_1.16.5` | 1.16.2 – 1.16.5 |
| `FASBingoWorldgen_1.17.1` | 1.17 – 1.17.1 |
| `FASBingoWorldgen_1.18.2` | 1.18 – 1.18.2 |
| `FASBingoWorldgen_1.19` | 1.19 – 1.19.3 |
| `FASBingoWorldgen_1.20` | 1.20 – 1.20.6 |
| `FASBingoWorldgen_1.21` | 1.21 – 1.21.11 |
| `FASBingoWorldgen_26.1` | 26.1 – 26.3 |

Each pack is a zip named after the pack name in its row, followed by the datapack release version. Put the zip in the world's `datapacks/` folder.

Build every pack with `python build.py`; the zips are written to `build/`.

## Changes to Vanilla Worldgen

### Biomes

- Overworld biomes are about 1/7 of their vanilla width. On 1.16.5 and 1.17.1 they are about 1/8.
- Nether biomes are about 1/4 of their vanilla width.

### Terrain

- Land above sea level is multiplied by 0.45, so mountains are about half as tall and their slopes gentler.
- Oceans, coasts and plains keep their vanilla heights, and the sea level does not move.
- Underground biome layers sit slightly closer to the surface.
- Narrower biomes make the terrain stiffen into isolated pillars up to 60 blocks higher than everything around them. The slope factor is averaged over the neighbouring 3x3 quarts to remove them; biomes are unaffected. Reported by Hackerrouter.
- 1.18.2 and later only.

### Structures

The gap between structures shrinks, so the same structure appears more often:

- Overworld: gap ×3/8.
- Nether: gap ×1/2.
- End: gap ×1/3.

A few values are set individually:

- Buried treasure: 3× as common.
- Strongholds: the first ring is much closer to spawn, 6 strongholds instead of 3.
- Ancient cities: smaller footprint, reaching 96 blocks from the centre instead of 116.
- Monster Rooms: 
  - 5× as many attempts near the surface, capped at y=128.
  - The deep variant gets 5× as many attempts too, on 1.18.2 and later.

#### Affected Structures

All vanilla structures except:

- Mineshafts
- Ocean monuments
- Nether fossils

## Changes to Vanilla Loot

- Piglin bartering trades ender pearls as in 1.16.1: weight 20 instead of 10, and 4-8 pearls instead of 2-4. Every other trade stays as the version ships it.
- Endermen always drop at least 1 ender pearl.

## Unchanged

- Caves and ravines generate as in vanilla.
- Ores generate as in vanilla.

## Known limitations

### 1.16.5 / 1.17.1: the world seed does not change terrain or biomes

Every world of a given version generates the same terrain and the same biome layout; only structures, features and loot follow the seed entered at world creation. The layout differs between 1.16.5 and 1.17.1. 1.18.2 and later are not affected.

This is a limit of the version, not of the pack: before 1.19 a dimension carries its own generator seed, and data cannot reference the world seed.

### 1.16.5 / 1.17.1: fewer biomes, vanilla terrain

- Eroded and non-eroded variants merge into one biome, so for example wooded badlands or shattered savanna do not appear.
- Cave biomes can only occupy a point where their surface biome would be.
- Mountains keep their vanilla height on those versions.

## Credits

- Bingo game mode and the original tuning baseline: [Minecraft Bingo by lorgon111](https://www.youtube.com/watch?v=x-udqNYXBJw).
- Factor-smoothing method to reduce terrain pillars from narrowed biomes: Hackerrouter(Minecraft Player ID).