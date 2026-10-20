# 实现指南

> 整体目标见 [DESIGN.md](DESIGN.md)。本文给每项改动的目标值、约束与验收判据；各版本做到哪一步见 [PROGRESS.md](PROGRESS.md)。

## 目标

1. 群系缩小
2. 增加结构密度
3. 调整战利品表，减小风险，增加可能性
4. 尽量保持物品价值的相对顺序不变

## 补丁形态

- 版本目录下的 `.py` 文件是补丁，其余文件作为静态资源原样复制进产物。
- 补丁暴露 `TYPE`、`reference_file` 与 `process_single` 或 `process_multi`。
- 被引用的原版文件放进 `common/vanilla/<版本>/`，扁平命名为 `<类别>__<标识>.json`，内容与目标版本的原版文件相同。
- 目标路径相对包根书写，与 `patch_lib.paths.package_root(patch_path)` 拼接，使同一张表同时适用于本体与 overlay。
- 同类别且同时变化的资源合并为一个 `*__multi.py`，按目标路径显式分派，未登记的目标报错。
- 共享算法在 `patch_lib/`：`dispatch.make` 负责源表、包根与分派，`worldgen_26` 负责 26.x 的地形、结构与已放置特性，`loot_table.make` 负责战利品条目。
- 基线名由目标路径派生：`worldgen/` 之下用 `__` 连接，如 `data/minecraft/worldgen/density_function/overworld/offset.json` 对应 `density_function__overworld__offset.json`；1.18.2 的 `configured_structure_feature/` 保留目录名。战利品表省略子目录，名字由补丁显式给出。
- 新版本只在目标文件与前一版不同时新增基线，其余沿用前一版目录；补丁用 `source_overrides` 指向改动过的文件。
- `pack.mcmeta` 的描述取自 `common/pack.mcmeta`，版本补丁只提供格式字段。

### 参数常量

可调参数集中在 `patch_lib/tuning.py`，取值即当前决策，不是「未配置时的默认值」。版本补丁只写落点并引用它，因此同一旋钮对所有走补丁的版本同时生效，不会因复制到各版本而分叉。

- 参数注释里的 `vanilla` 取值是对照基准，用于换算，不表示关掉后回到该值。
- `1.0` 与 `True` 是「不缩放」的哨兵：对应文件或分支从产物中消失，不输出与原版相同的拷贝。仅当该值为哨兵时，参数才参与源文件清单与分派表的构造，因为需要增减源文件；只改字段内容的参数在补丁函数内判断。
- `XZ_SCALE_*` 的基准是原版 `0.25`，不是 `1.0`。
- 一个参数只在一处取值，被多处使用时引用同一常量。
- 目录名、集合清单与基线文件名不进 `tuning.py`：它们在版本之间会变，属于落点，写在版本补丁里。

## 群系缩小

### 目标值

主世界取 `xz_scale` `1.8`，相对原版 `0.25` 为 `7.2` 倍频率。

| 字段 | 原版形式 | 目标 |
| --- | --- | --- |
| `temperature` | `noise_router` 内联 `shifted_noise`；26.3 起为 `overworld/temperature.json` 的 `noise` | `xz_scale` `1.8` |
| `vegetation` | 同上 | 同上 |
| `continents` | 引用 `overworld/continents` | 命名密度函数 `xz_scale` `1.8` |
| `erosion` | 引用 `overworld/erosion` | 同上 |
| `ridges` | 引用 `overworld/ridges` | 同上 |

下界取原版 4 倍：

| 字段 | 目标值 | 原版值 |
| --- | --- | --- |
| `temperature` | `xz_scale` `1.0` | `0.25` |
| `vegetation` | 同上 | 同上 |

### 约束与理由

尺度基准以原版世界为 `1`。1.13 前「群系大小」是可选滑块，参数 `1`–`8`、默认 `4`，每加一尺寸翻倍；`large_biomes` 传 `6`。`OverworldBiomeSource` 按群系大小调用 `Layers.getDefaultLayer(seed, legacy, biomeSize, riverSize)`，主世界传 `4`，每次缩放把坐标刻度翻倍；JSON 可直接写 `0`，为原版的 `1/16`。基准目标因此取 `1/8`，即滑块最小档，原 bingo 的 `level.dat` 实测 `biomeSize` 为 `1`。原 bingo 的 `riverSize` 为 `4`，即滑块默认值，说明河流未调整，河流密度无需另设旋钮。

- `firstOctave` 每加一，频率翻倍、线性尺度减半；`xz_scale` 翻倍等价。故 `1/8` 为加三，`1/4` 为加二。
- `1.8` 是实测调参的结果；`1/8` 基准对应 `2.0`。旧版只能用 `firstOctave` 表达频率，取不到 `7.2` 倍，按 `1/8` 取。
- `worldgen/noise/*.json` 保持原版：频率只在密度函数层表达，`firstOctave` 与 `amplitudes` 不动。
- `continents`、`erosion`、`ridges` 同时供给群系源与地形，改这三个函数即同时作用于两侧，不需要另设地形侧落点。把字段内联进 `noise_router` 也能只影响群系，但会让两侧各自取值、靠人工保证相等，任一侧调整都会漂移，因此不采用。
- 旧机制的保真度差异：原版滑块只缩放群系层，海洋与湖泊的形状由独立的层生成，其缩放层数写死为 `6`，不受群系大小影响。改用 `multi_noise` 后，海洋作为表内条目与其余群系一同缩放，没有这个豁免。

新旧两代的噪声取值可直接对应：1.16.5 与 1.18.2 的 `NormalNoise` 输入因子同为 `1.0181268882175227`，归一化同为 `0.16666666666666666 / expectedDeviation(octaveSpan)`，且噪声坐标单位同为四格，因此同一组 `firstOctave` 与 `amplitudes` 在两代产生相同取值。`amplitudes` 决定各倍频的权重，即布局的细节层次，必须照抄目标值，自造成单一 `[1.0, 1.0]` 会改变网格细节。

### 旧机制：四轴投影

1.18 前的主世界群系源读四轴，没有官方主世界参数表。投影的前提是两代群系源结构不同：

| 项目 | 旧版 | 1.18 起 |
| --- | --- | --- |
| 读取的轴 | `temperature`、`humidity`、`altitude`、`weirdness` 四条，各 `[-2, 2]` | 上述四条加 `continentalness`、`erosion`、`depth` 共七条 |
| 轴的值形式 | 单个浮点 | `[min, max]` 区间 |
| 匹配方式 | 最近邻，五项平方和最小 | 区间距离最小 |
| `offset` 作用 | 采样恒传 `0.0`，实际是加性优先级，非独立轴 | 同左 |
| `depth` 采样 | `useY` 硬编码为 `false`，四轴都在 `y=0` 采样，纯二维 | 随高度变化 |

官方主世界 surface 表实际用到五条轴：`temperature`、`humidity`、`continentalness`、`erosion`、`weirdness`，`depth` 恒为 `point(0)`。旧版只有四条，因此投影必须丢一条轴：

| 源轴 | 目标轴 |
| --- | --- |
| `temperature` | `temperature` |
| `humidity` | `humidity` |
| `continentalness` | `altitude` |
| `weirdness` | `weirdness` |
| `erosion` | 丢弃 |
| `depth` | 丢弃 |

- 源表取 1.18.2 的 `dimension/overworld.json` 内联 `biomes`，共 7578 条、50 个群系；源表不可用时按 `OverworldBiomeBuilder` 复现。
- 各轴取源区间中点，`offset` 统一写 `0.0`。
- 丢弃 `erosion` 不构成信息损失：旧版群系没有侵蚀度概念，地形变体由 `altitude` 与 `weirdness` 表达。
- 投影结果为 2058 个唯一点位，其中 598 个点位存在多个源条目，表现为同一气候下的侵蚀度变体塌缩。

冲突消解按两级规则挑选代表群系：

1. 候选中的非变体群系优先。
2. 仍有多个时取出现次数最多者。

变体群系指 `sunflower_plains`、`ice_spikes`、`old_growth_*`、`sparse_jungle`、`bamboo_jungle`、`eroded_badlands`、`wooded_badlands`、`meadow`、`cherry_grove`、`grove`、`snowy_slopes`、`*_peaks`、`stony_shore`、`windswept_*`。

官方表中部分群系在旧版没有同名对应，按下表降级：

| 官方 | 旧版 |
| --- | --- |
| `snowy_plains` | `snowy_tundra` |
| `old_growth_birch_forest` | `tall_birch_forest` |
| `old_growth_pine_taiga` | `giant_tree_taiga` |
| `old_growth_spruce_taiga` | `giant_spruce_taiga` |
| `sparse_jungle` | `jungle_edge` |
| `windswept_hills` | `mountains` |
| `windswept_forest` | `wooded_mountains` |
| `windswept_gravelly_hills` | `gravelly_mountains` |
| `windswept_savanna` | `shattered_savanna` |
| `wooded_badlands` | `wooded_badlands_plateau` |
| `stony_shore` | `stone_shore` |
| `meadow` | `plains` |
| `grove` | `snowy_taiga` |
| `snowy_slopes` | `snowy_mountains` |
| `jagged_peaks`、`frozen_peaks` | `snowy_mountains` |
| `stony_peaks` | `mountains` |

旧版群系查找是线性扫描，条目数直接决定区块生成开销；1.18 起用 `Climate.ParameterList` 内的 R-tree，对数级，不敏感。因此只有旧版需要控制规模，按档位出产物：

| 档位 | 量化粒度 | 条目数 | 群系数 | 缺失的必备群系 |
| --- | --- | --- | --- | --- |
| `full` | 不量化 | 2058 | 47 | 无 |
| `balanced` | `0.25` | 1046 | 42 | 无 |
| `lite` | `0.5` | 130 | 25 | `river`、`swamp`，需按必备群系保底补回 |

量化粒度 `0.25` 是不损失必备群系的前提下能达到的最粗粒度；`1/3` 起即丢失 `river`，538 条、37 个群系，因此不作档位。必备群系指海洋、河流、海岸、蘑菇岛与各基础陆地群系。三档的产物结构相同，只是条目集合不同，可整套替换。

旧版的噪声参数用 `firstOctave` 表达频率，下界等效为加二：

| 轴 | 目标 `firstOctave` | 目标 `amplitudes` |
| --- | --- | --- |
| `temperature` | `-7` | `[1.5, 0.0, 1.0, 0.0, 0.0, 0.0]` |
| `humidity` | `-5` | `[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]` |
| `altitude` | `-6` | `[1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0]` |
| `weirdness` | `-4` | `[1.0, 2.0, 1.0, 0.0, 0.0, 0.0]` |

群系噪声内联在 `biome_source`，与 `noise_settings` 的地形噪声互不相干，改频率不影响地形。`seed` 同时写 `generator.seed` 与 `generator.biome_source.seed`，两处取值相同。

### 验收

- `noise_router` 的 `continents`、`erosion`、`ridges` 仍是字符串引用，三个命名密度函数的噪声节点 `xz_scale` 均为 `1.8`；26.3 的节点在 `input` 下。
- `temperature` 与 `vegetation` 的 `xz_scale` 均为 `1.8`，26.3 起为独立密度函数文件。
- `worldgen/noise/*.json` 的 `firstOctave` 与 `amplitudes` 等于基线。
- 旧版：`biome_source.type` 为 `minecraft:multi_noise`，四轴噪声的 `firstOctave` 与 `amplitudes` 等于上表，条目数与所选档位一致。

## 地形调整

### 目标值

| 项目 | 取值 | 原版 | 落点 |
| --- | --- | --- | --- |
| 高地高度 | `offset` 正值叶乘 `0.45` | 地表 `25..256` | `density_function/overworld/offset.json` |
| 峰顶细节 | `jaggedness` 全部叶乘 `0.45` | 最大叶值 `0.63` | `density_function/overworld/jaggedness.json` |
| 陡坡 | 系数 `1.0`，该文件不进产物 | `0.625..6.3` | `density_function/overworld/factor.json` |
| 地下群系带 | `depth` 引用包一层 `×1/0.9` 的 `mul` | 深暗之域在地表下 141 格 | `noise_settings/overworld.json` 的 `depth` |

各项系数按同一比例取，使峰顶细节与山体高度同步缩小。系数取哨兵值时该文件不进产物，可直接与原版对照。

### 约束与理由

群系频率提高后，同样的垂直振幅分布在更短的水平距离上，坡变得陡而碎，峰顶成尖。本节把高地压低，并保证不改变以 `depth` 为输入的地形与地下机制。

地表高度只能经 `offset` 与 `jaggedness` 调整，`depth` 不动：

$$y_0 = 128 + 128 \cdot (offset_{const} + offset_{spline})$$

- 压正值叶等价于压低陆地并把坡度同步压缓，两个效果出自同一个乘法。负值叶是海洋深度，保持原版使海深、海岸线与沙滩位置不变。
- 海平面以上的地表越低降得越多，海平面处是不动点。依赖地表高度的结构，村庄、神殿、废弃传送门的 y 坐标，随之移动，这是预期结果。
- `jaggedness` 只加在低侵蚀、高脊的峰顶，值为零的叶覆盖海洋、海岸、平原与湿地，缩放后仍为零。
- `factor` 不参与地表求解，改它改变的是地形与 `base_3d_noise` 的相对比重，不是坡度。
- 导数的局部斜率跟着叶值同乘，曲线形状保持，不会在分段处出现折角。
- `depth` 被三处使用，改它会静默移动地下群系：
  - 地形密度经 `overworld/sloped_cheese` 读它。
  - 群系源的第五轴直接取 `noise_router.depth`，`dripstone_caves` 与 `lush_caves` 取 `0.2..0.9`，`deep_dark` 取 `1.1`。
  - 深暗之域另有一处硬编码判定，条件为 `erosion` 低且 `depth` 大于 `0.9`。
  - 三处都以斜率为每单位 `128` 格、零点在地表为前提，改区间或端值会同时改变斜率与零点。
- 1.18.2 的起伏 spline 在 `noise.terrain_shaper`，1.19 起才是独立文件。
- 1.17 及以前没有独立的密度函数文件，该改动不适用。1.16.5 的 `noise.bottom_slide` 属旧机制，该版初始密度公式未重写，把它改为与新版配套的值只会把底部若干格强制实心，压掉该区间的洞穴与矿脉，应保持原版。

### 地下群系带

地下群系的层位由 `depth` 轴给出，零点跟地表走，所以山地被压低后山下的带随之下移，平原与海洋处逐值不变。若要连层带本身一起压短，只包装 `noise_router` 的 `depth`，不改命名密度函数：地形仍经 `sloped_cheese` 读原版函数，密度与洞穴形状不变，只有群系采样器取到放大后的值。

| 相对深度 | 原版 | 压缩到 `0.9` |
| --- | --- | --- |
| 洞穴带 `0.2` | 26 格 | 23 格 |
| 洞穴带 `0.9` | 115 格 | 104 格 |
| 深暗之域 `1.1` | 141 格 | 127 格 |

参数为 `UNDERGROUND_RELIEF`，当前 `0.9`。代价是平坦地面的地下带同步上移：平原可用深度为 `127` 格，压缩比低于约 `0.9` 时深暗之域会进入世界底部，当前取值贴近该临界。该阈值由 `offset` 的基准常量决定，换版本需重算。

### 验收

- 海洋与海岸：`offset` 负值叶逐字段等于原版，海平面附近的地表高度不变。
- 平原：`jaggedness` 叶值为零处的地形逐块等于原版。
- 地下：`final_density`、`preliminary_surface_level`、`surface_rule` 与基线逐字段相同；`noise_router` 的 `depth` 是引用外加一层 `mul`，命名密度函数 `overworld/depth` 本身不变。
- 分段映射：`offset` 的负值叶、`factor` 不大于 `1.0` 的叶逐字段等于基线，零值处保持零。
- 不出现硬截断：高度上限仍为 `320`，峰顶不被削平，且峰顶高度低于原版上限 `256`。

## 增加结构密度

### 目标值

密度按维度整体缩放，只对个别结构集合单独覆盖，不逐集合给终值。每个维度一组系数，作用在该版本原版的 `spacing` 与 `separation` 上：

| 维度 | `spacing` | `separation` |
| --- | --- | --- |
| 主世界 | `×3/8` | `×1/4` |
| 下界 | `×1/2` | `×1/2` |
| 末地 | `×1/3` | `×1/3` |

- 缩放结果四舍五入，`spacing` 最小 `1`、`separation` 最小 `0`，写回前校验 `separation < spacing`。
- 只处理 `random_spread` 与 `concentric_rings`；其他分布类型报错，不静默跳过。
- 该维度下全部原版集合都参与，不逐个挑选。

系数无法表达的字段单独覆盖：

| 集合 | 覆盖值 | 原版值 |
| --- | --- | --- |
| `buried_treasures` | `frequency` `0.03` | `0.01` |
| `strongholds` | `distance` `10`、`spread` `6` | `distance` `32`、`spread` `3` |
| `ancient_cities` | `ancient_city` 的 `max_distance_from_center` 改 `96` | `116` |

排除项：

| 集合 | 原版 | 原因 |
| --- | --- | --- |
| `mineshafts` | `1/0`，`frequency` `0.004` | 密度由 `frequency` 决定，缩放 `spacing` 无意义 |
| `ocean_monuments` | `32/5` | 按设计保持原版 |
| `nether_fossils` | `2/1` | 缩放后 `separation` 会顶到 `spacing` |

怪物房数量取浅层 `50`、深层 `20`，浅层高度上界压到 `128`。

### 约束与理由

- 结构间距以该版本原版的 `spacing`、`separation` 为基准，不以当前文件里的现值作基准。
- `ruined_portals` 在原版是单一集合，主世界与下界变体共用 `placement`，维度由各结构定义的群系标签过滤，因此按主世界系数缩放。1.18 前的结构表按维度分开，可分别缩放。
- 怪物房的 `50`、`20` 与高度上界 `128` 属测试期参数，实机验证后可能调整；调整只改数值，不改本节其余规则。
- 旧版的结构表在 `noise_settings/<维度>.json` 的 `structures.structures`，每维度一份表，1.16.5 含主世界与下界、1.17.1 另含末地，改动需同步；要塞另在 `structures.stronghold`。
- 埋藏宝藏的落点随版本不同：1.18.2 在 `configured_structure_feature/buried_treasure.json` 的 `config.probability`，1.20 起在 `structure_set/buried_treasures.json` 的 `placement.frequency`。
- 怪物房的落点：1.16.5 与 1.17.1 在 `configured_feature/monster_room.json` 的 `decorator.config.count`，旧版无深层变种，1.17.1 的高度上界由 `range` 的 `below_top` 给出；1.18 起在 `placed_feature/monster_room.json` 与 `monster_room_deep.json`。

### 验收

- 逐集合对照原版 `spacing`、`separation`，结果等于按系数缩放后再应用覆盖项的值。
- 全部集合满足 `separation < spacing`。
- 排除项逐字段等于原版。
- 怪物房 `count` 为 `50` 与 `20`，浅层高度上界为 `128`，深层高度范围等于原版。
- 远古城市 `max_distance_from_center` 为 `96`。

## 调整战利品表

### 目标值

1. 猪灵以物易物的珍珠条目回调到 1.16.1 的权重与数量，其余条目保留本版原版。
2. 末影人的珍珠掉落率设置保底 `1`，减少运气成分。

| 项目 | 目标值 | 原版值 |
| --- | --- | --- |
| 珍珠条目 `weight` | `20` | `10` |
| 珍珠条目 `count` | `4..8` | `2..4` |
| 其余条目 | 本版原版 | 本版原版 |
| 末影珍珠 `count.min` | `1` | `0` |

### 约束与理由

- 1.16.2 起原版把珍珠条目由 `weight` `20`、数量 `4..8` 降为 `weight` `10`、数量 `2..4`，单次期望由 `0.284` 降到 `0.065`。本项目只回调这一条，不碰表内其余条目。
- 不改条目集合：新版新增的交易属于内容广度，删掉无收益；珍珠供应已由末影人保底解决，以物易物只需保住这条捷径。
- 下界合金锄仅存在于 `20w09a` 至 `20w20a` 的快照，1.16 正式版发布前已移除以物易物，因此任何正式版的原版表都不含该工具。
- 以物易物的落点：1.20 及以前为 `loot_tables/gameplay/piglin_bartering.json`，26.1 起为 `loot_table/gameplay/piglin_bartering.json`。末影人对应 `entities/enderman.json`，1.16.5 起有这份文件，实体掉落走战利品表。

### 验收

- 以物易物表相对基线的差异只有珍珠条目的 `weight` 与 `count` 的 `min`、`max`。
- 末影人相对基线的差异只有 `count.min`，`random_sequence` 保留。

## 离线工具

`generator/` 放不参与构建的分析脚本，与 `tools/` 的构建框架分开，因为后者是外部子模块。

- `generator/biome_scale.py`：按下界气候噪声重建群系场，输出各群系面积占比、斑块尺寸与「探全五个群系」所需的半径。
- 用于调尺度时先估算手感，不必反复开局。参数 `--multiplier` 取相对原版的频率倍率，与补丁里的 `xz_scale` 对应：`0.25 × 倍率`。
- 依赖 `numpy` 与 `scipy`。
- 参考值：倍率 `1` 时覆盖半径中位数约 `300` 格，`4` 时约 `75` 格，`8` 时约 `37` 格。瓶颈通常是诡异森林与灵魂沙峡谷。

## 校验

- 运行 `python build.py`，确认全部版本成功。产物只含改动过的文件与 `pack.mcmeta`，文件集合与改动清单一致。
- 运行 `python tools/clean.py`，确认仓库内没有 `__pycache__`。
- 单文件比对：`python tools/json_diff.py <基线文件> <产物文件>`。每个文件的差异应恰好等于该改动项的字段，生成后与基线相同说明补丁未生效或方向错误。
- 格式：`pack.mcmeta` 的格式字段与 overlay 登记能覆盖目标版本区间，且不含过期字段。
- 旋钮：改动 `patch_lib/tuning.py` 的一个值后重建，所有走补丁的版本产物应同步变化，静态文件的版本不应变化。

## 参考来源

原版类路径均以 `net/minecraft/` 开头，数据包内资源路径均以 `data/minecraft/` 开头。

- 群系大小与河流大小滑块、怪物房与矿石项的滑块范围：[Old Customized - Minecraft Wiki](https://minecraft.wiki/w/Old_Customized)
- 原 bingo 的设置实测值与出处：见 [DESIGN.md](DESIGN.md) 的「原 bingo 基线」
- 缩放层数：1.16.4 的 `net/minecraft/world/level/newbiome/layer/Layers.java` 与 `net/minecraft/world/level/biome/OverworldBiomeSource.java`
- 旧版群系源与匹配规则：1.16.4 的 `net/minecraft/world/level/biome/MultiNoiseBiomeSource.java` 与 `net/minecraft/world/level/biome/Biome.java`；1.17.1 的同名文件结构相同
- 噪声归一化：1.16.4 与 1.18.2 的 `net/minecraft/world/level/levelgen/synth/NormalNoise.java`
- 群系查表的空间索引：`net/minecraft/world/level/biome/Climate.java` 的 `ParameterList` 与 `RTree`
- 官方参数表：1.18.2 的 `data/minecraft/dimension/overworld.json`
