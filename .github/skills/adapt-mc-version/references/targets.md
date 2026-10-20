# 目标文件与版本差异

1.18 起各版本改动的是同一批文件，差异在目录名与字段落点。路径均相对 `data/minecraft/`。

路径、字段与版本列适用至 26.2（数据格式 107.1）；更晚版本的原版结构可能不同，迁移前先用版本差异扫描复核。

## 目标清单

| 目标 | 改动 | 旋钮 |
| --- | --- | --- |
| `worldgen/noise_settings/overworld.json` | `temperature`、`vegetation` 的 `xz_scale`；`depth` 引用包一层 `mul` | `XZ_SCALE_OVERWORLD`、`INLINE_CLIMATE_FIELDS`、`UNDERGROUND_RELIEF` |
| `worldgen/noise_settings/nether.json` | `temperature`、`vegetation` 的 `xz_scale` | `XZ_SCALE_NETHER`、`NETHER_CLIMATE_FIELDS` |
| `worldgen/density_function/overworld/{continents,erosion,ridges}.json` | `argument.xz_scale` | `XZ_SCALE_OVERWORLD` |
| `worldgen/density_function/overworld/{offset,factor,jaggedness}.json` | spline 叶值，按正值或阈值缩放；1.19 起才有这三张文件 | `RELIEF_HIGHLAND`、`RELIEF_FACTOR`、`RELIEF_JAGGED` |
| `worldgen/structure_set/<集合>.json` | `placement.spacing`、`separation` 按维度缩放；`frequency`、`distance`、`spread` 单独覆盖 | `DIMENSION_SCALES`、`SPECIAL_FIELD_OVERRIDES` |
| `worldgen/structure/ancient_city.json` | `max_distance_from_center` | `STRUCTURE_FIELD_OVERRIDES` |
| `worldgen/placed_feature/monster_room.json` | `count`、`height_range.max_inclusive` | `PLACED_FEATURE_RULES` |
| `worldgen/placed_feature/monster_room_deep.json` | `count` | `PLACED_FEATURE_RULES` |
| `loot_table/entities/enderman.json` | `count.min` | `ENDERMAN_PEARL_MIN` |
| `loot_table/gameplay/piglin_bartering.json` | 珍珠条目 `weight` 与 `count` | `BARTERING_PEARL*` |

`worldgen/structure_set/` 只缩放任一版本实际存在的集合：集合名单差异是版本事实，写在版本补丁的 `DIMENSION_SETS`；缩放系数与字段覆盖写在 `tuning.py`。

## 版本的落点差异

下表适用至 26.2；新版本先确认这些路径仍存在、字段仍在同一层。

| | 1.18.2 | 1.20 | 26.1 起 |
| --- | --- | --- | --- |
| 地形起伏 spline | `noise_settings/overworld.json` 的 `noise.terrain_shaper.{offset,factor,jaggedness}` | `worldgen/density_function/overworld/<键>.json` | 同左 |
| 结构定义目录 | `worldgen/configured_structure_feature/` | `worldgen/structure/` | 同左 |
| 远古城市 | 无此结构 | `worldgen/structure/ancient_city.json` | 同左 |
| 埋藏宝藏概率 | `worldgen/configured_structure_feature/buried_treasure.json` 的 `config.probability` | `worldgen/structure_set/buried_treasures.json` 的 `placement.frequency` | 同左 |
| 战利品目录 | `loot_tables/` | `loot_tables/` | `loot_table/` |
| 包格式 | `pack_format` | `pack_format` | `min_format` 与 `max_format` |
| 战利品表默认值字段 | 显式写出 | 显式写出 | 26.2 起省略（`bonus_rolls`、`add`） |

气候字段、三个命名密度函数、结构集合、已放置特性的落点在 1.18 起的各版本中相同。

## 基线命名

- `worldgen/` 之下：去掉 `data/minecraft/worldgen/` 前缀，其余路径用 `__` 连接，如 `density_function__overworld__offset.json`、`structure_set__villages.json`、`structure__ancient_city.json`。
- 战利品表：省略子目录，名字在补丁里显式给出，沿用现有形式 `loot_table__enderman.json`、`loot_table__piglin_bartering.json`。
- 1.18.2 的 `configured_structure_feature/` 文件同样按路径扁平化，目录名保留，如 `configured_structure_feature__buried_treasure.json`。
- 只把与复用基线字节不同的文件放进新版本目录；其余文件继续用前一版的目录。
