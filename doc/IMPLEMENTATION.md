# 实现指南

> 整体目标与取舍见 [DESIGN.md](DESIGN.md)。本文描述实现方案，以及各版本可预见的实现差异。方案文本在实现前已定，后续非必要不作改动。

## 目标

1. 群系缩小
2. 增加结构密度
3. 调整战利品表，减小风险，增加可能性
4. 尽量保持物品价值的相对顺序不变

明确不改：洞穴生成、矿石分布、矿井分布。理由见 [DESIGN.md](DESIGN.md) 的「职责边界」。

同一改动在各目标版本上取相同目标值。

## 约定

- 每项改动的目标值只在一处取值，所有落点共享同一常量；版本补丁只写落点，不复制数值。改一个值即对所有目标版本同时生效。
- 目录名、集合清单与产物文件名随版本变化，不进参数表，留在版本补丁里。
- `1.0` 与 `True` 是「不缩放」的哨兵：对应文件或分支不进入产物，而不是输出一份与原版相同的拷贝。
- 原版值是换算基准，不是关掉旋钮后的回退值。
- 补丁形态、包根与基线命名见 `AGENTS.md`。

## 群系缩小

### 目标值

主世界的五条气候轴 `xz_scale` 取 `1.8`，即原版 `0.25` 的 `7.2` 倍；下界的两条取 `1.0`，即原版 4 倍。

| 轴 | 主世界 | 下界 |
| --- | --- | --- |
| `temperature` | `1.8` | `1.0` |
| `vegetation` | `1.8` | `1.0` |
| `continents` | `1.8` | — |
| `erosion` | `1.8` | — |
| `ridges` | `1.8` | — |

### 约束与理由

尺度以原版世界为 `1`。1.13 前的群系大小滑块参数 `1`–`8`、默认 `4`，每加一档频率翻倍；原 bingo 取最小档 `1`，即原版 `1/8`，对应 `xz_scale` `2.0`。本项目取 `7.2` 倍，是在 `1/8` 基准上实测调参得到的取值，略低于该基准。

- `firstOctave` 每加一，频率翻倍、线性尺度减半；`xz_scale` 翻倍等价。故 `1/8` 为加三，`1/4` 为加二。旧版只能用 `firstOctave` 表达频率，取不到 `7.2` 倍，按 `1/8` 取。
- 原 bingo 的 `riverSize` 为 `4`，即滑块默认值，说明河流未调整，河流密度无需另设旋钮。
- `continents`、`erosion`、`ridges` 必须保持为命名密度函数的引用。这三个函数同时供给群系源与地形，一处取值即同时作用于两侧；内联进 `noise_router` 也能只影响群系，但会让两侧各自取值、靠人工保证相等，任一侧调整都会漂移。
- `worldgen/noise/*.json` 保持原版：频率只在密度函数层表达，`firstOctave` 与 `amplitudes` 不动。
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

- 源表取 1.18.2 的 `dimension/overworld.json` 内联 `biomes`；源表不可用时按 `OverworldBiomeBuilder` 复现。
- 各轴取源区间中点，`offset` 统一写 `0.0`。
- 丢弃 `erosion` 不构成信息损失：旧版群系没有侵蚀度概念，地形变体由 `altitude` 与 `weirdness` 表达。

多个源条目落到同一气候点位时，投影会塌缩掉侵蚀度变体。消解按两级规则挑选代表群系：

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

| 档位 | 量化粒度 | 含义 |
| --- | --- | --- |
| `full` | 不量化 | 官方表全部条目，最准 |
| `balanced` | `0.25` | 不损失必备群系前提下能达到的最粗粒度 |
| `lite` | `0.5` | 最省，需按必备群系保底补回 |

当前取 `balanced`。量化粒度 `0.25` 是边界：`1/3` 起即丢失 `river`，因此不作档位。必备群系指海洋、河流、海岸、蘑菇岛与各基础陆地群系。三档的产物结构相同，只是条目集合不同，可整套替换；条目数由量化粒度与目标版本的群系清单共同决定。

旧版的噪声参数用 `firstOctave` 表达频率，取 1.18 噪声文件的基准各减 `3`，即 `8` 倍：

| 轴 | 目标 `firstOctave` | 目标 `amplitudes` |
| --- | --- | --- |
| `temperature` | `-7` | `[1.5, 0.0, 1.0, 0.0, 0.0, 0.0]` |
| `humidity` | `-5` | `[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]` |
| `altitude` | `-6` | `[1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0]` |
| `weirdness` | `-4` | `[1.0, 2.0, 1.0, 0.0, 0.0]` |

`firstOctave + len(amplitudes) - 1` 必须 `<= 0`。旧实现只为 octave `<= 0` 的层分配噪声对象：1.16.5 静默丢弃正 octave 的层，1.17.1 抛 `Positive octaves are temporarily disabled`。截掉的都是最细的倍频，区域划分不变；列表长度参与归一化系数，幅度因此有小幅偏移。

群系噪声内联在 `biome_source`，与 `noise_settings` 的地形噪声互不相干，改频率不影响地形。`seed` 同时写 `generator.seed` 与 `generator.biome_source.seed`，两处取值相同。

`seed` 取各版的历史常量，不随世界种子变化：1.19 前维度定义自带生成器种子，数据包的维度文件会覆盖世界预设里的维度（含其种子），而数据无法引用世界种子，因此旧版的地形噪声与群系布局固定，只有结构、特征与战利品跟随世界种子。1.19 起该字段移除，世界种子始终生效，本节不适用。两版取同一个种子会让布局重合（气候参数与表本来就是共享的），所以该值按版本、按维度分别给出。

### 数据生成

官方表按目标版本投影，每版一套，写在 `common/biome_source/<目标版本>/`，三档结构相同、可整套替换。输入是 1.18.2 的官方主世界表与目标版本的群系清单，两者均入库，投影不依赖本机参考资源。

- 档位只在一处取值，所有旧版共用，当前 `balanced`。
- 投影依赖目标版本的群系清单：版本有的群系才保留，没有的才丢弃，因此各旧版各有一套表，不共用。
- 量化会抹掉低频群系，必须按必备群系保底补回。
- 洞穴群系经 `depth` 轴到达，而旧版采样 `y=0`，所以只能占一个地表点位（`dripstone_caves` 在高海拔，`lush_caves` 在湿润带）。这是旧机制能做到的上限，不是误差。
- 洞穴群系只有一条官方条目，在多候选点位会被多数票挤掉，因此也列为必备群系强制补回。
- 降级映射、变体清单与必备群系只用于投影，不进参数表，不能用于其他机制。

### 版本差异

- 1.18 起是七轴 `multi_noise`，本节不适用；1.18 前是四轴最近邻，需要投影。
- 26.3 起 `temperature` 与 `vegetation` 独立成密度函数文件，不再内联进 `noise_router`。

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

### 地下群系带

地下群系的层位由 `depth` 轴给出，零点跟地表走，所以山地被压低后山下的带随之下移，平原与海洋处逐值不变。若要连层带本身一起压短，只包装 `noise_router` 的 `depth`，不改命名密度函数：地形仍经 `sloped_cheese` 读原版函数，密度与洞穴形状不变，只有群系采样器取到放大后的值。

| 相对深度 | 原版 | 压缩到 `0.9` |
| --- | --- | --- |
| 洞穴带 `0.2` | 26 格 | 23 格 |
| 洞穴带 `0.9` | 115 格 | 104 格 |
| 深暗之域 `1.1` | 141 格 | 127 格 |

地下群系的压缩比取 `0.9`。代价是平坦地面的地下带同步上移：平原可用深度为 `127` 格，压缩比低于约 `0.9` 时深暗之域会进入世界底部，当前取值贴近该临界。该阈值由 `offset` 的基准常量决定，换版本需重算。

### 版本差异

- 1.18.2 的起伏 spline 内嵌在噪声参数里，1.19 起才是独立的密度函数文件。
- 1.17 及以前没有独立的密度函数文件，本项不适用。1.16.5 的 `bottom_slide` 属旧机制，该版初始密度公式未重写，把它改为与新版配套的值只会把底部若干格强制实心，压掉该区间的洞穴与矿脉，应保持原版。

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
- `ruined_portals` 在原版是单一集合，主世界与下界变体共用 `placement`，维度由各结构定义的群系标签过滤，因此按主世界系数缩放。
- 怪物房的 `50`、`20` 与高度上界 `128` 属测试期参数，实机验证后可能调整；调整只改数值，不改本节其余规则。
- 旧版的排除项按短名匹配（`mineshaft`、`monument`、`nether_fossil`），在版本补丁里列出；其余集合整表缩放。

### 版本差异

- 1.18 前没有结构集合文件，结构表按维度分开，1.16.5 含主世界、下界与末地，改动需同步；要塞另在独立的 `stronghold` 段。
- 埋藏宝藏的落点：1.18.2 在 `configured_structure_feature/buried_treasure.json` 的 `config.probability`，1.20 起在 `structure_set/buried_treasures.json` 的 `placement.frequency`。
- 怪物房：1.16.5 与 1.17.1 在 `configured_feature/monster_room.json` 的 `decorator.config.count`，旧版无深层变种，1.17.1 的高度上界由 `range` 的 `below_top` 给出；1.18 起拆成 `placed_feature/monster_room.json` 与 `monster_room_deep.json`。

### 验收

- 逐集合对照原版 `spacing`、`separation`，结果等于按系数缩放后再应用覆盖项的值。
- 全部集合满足 `separation < spacing`。
- 排除项逐字段等于原版。
- 怪物房 `count` 为 `50` 与 `20`，浅层高度上界为 `128`，深层高度范围等于原版。
- 远古城市 `max_distance_from_center` 为 `96`。

## 调整战利品表

### 目标值

1. 猪灵以物易物的珍珠条目取 1.16.1 的权重与数量，其余条目保留本版原版。
2. 末影人的珍珠掉落率设保底 `1`，减少运气成分。

| 项目 | 目标值 | 原版值 |
| --- | --- | --- |
| 珍珠条目 `weight` | `20` | `10` |
| 珍珠条目 `count` | `4..8` | `2..4` |
| 其余条目 | 本版原版 | 本版原版 |
| 末影珍珠 `count.min` | `1` | `0` |

### 约束与理由

- 1.16.2 起原版把珍珠条目由 `weight` `20`、数量 `4..8` 降为 `weight` `10`、数量 `2..4`，单次期望降到约四分之一。本项目只回调这一条，不碰表内其余条目。
- 不改条目集合：新版新增的交易属于内容广度，删掉无收益；珍珠供应已由末影人保底解决，以物易物只需保住这条捷径。

### 版本差异

- 以物易物的落点：1.20 及以前在 `loot_tables/gameplay/piglin_bartering.json`，26.1 起目录名改为 `loot_table/`。
- 末影人走实体掉落表 `entities/enderman.json`，该表 1.16.5 起存在。

### 验收

- 以物易物表相对基线的差异只有珍珠条目的 `weight` 与 `count` 的 `min`、`max`。
- 末影人相对基线的差异只有 `count.min`，`random_sequence` 保留。

## 尺度估值

群系尺度可在开工前估个大概，不必反复开局实测：按下界气候噪声重建群系场，统计各群系面积占比、斑块尺寸与「探全五个群系」所需的半径。倍率指相对原版的频率倍率，与 `xz_scale` 的对应关系是 `0.25 × 倍率`。

参考值：倍率 `1` 时覆盖半径中位数约 `300` 格，`4` 时约 `75` 格，`8` 时约 `37` 格。瓶颈通常是诡异森林与灵魂沙峡谷。

## 全局验收

- 构建全部版本成功。产物只含补丁产出的文件与 `pack.mcmeta`，不含未改动的原版拷贝。
- 仓库内没有 `__pycache__`。
- 单文件比对：同一路径的基线文件与产物文件，差异应恰好等于该改动项的字段；与基线相同说明补丁未生效或方向错误。
- 格式：`pack.mcmeta` 的格式字段与 overlay 登记能覆盖目标版本区间，且不含过期字段。
- 旋钮：任取一项改值后重建，所有走补丁的版本产物应同步变化，静态文件的版本不应变化。

## 参考来源

原版类路径均以 `net/minecraft/` 开头，数据包内资源路径均以 `data/minecraft/` 开头。

- 群系大小与河流大小滑块、怪物房与矿石项的滑块范围：[Old Customized - Minecraft Wiki](https://minecraft.wiki/w/Old_Customized)
- 原 bingo 的设置实测值与出处：见 [DESIGN.md](DESIGN.md) 的「原 bingo 基线」
- 缩放层数：1.16.4 的 `net/minecraft/world/level/newbiome/layer/Layers.java` 与 `net/minecraft/world/level/biome/OverworldBiomeSource.java`
- 旧版群系源与匹配规则：1.16.4 的 `net/minecraft/world/level/biome/MultiNoiseBiomeSource.java` 与 `net/minecraft/world/level/biome/Biome.java`；1.17.1 的同名文件结构相同
- 噪声归一化：1.16.4 与 1.18.2 的 `net/minecraft/world/level/levelgen/synth/NormalNoise.java`
- 群系查表的空间索引：`net/minecraft/world/level/biome/Climate.java` 的 `ParameterList` 与 `RTree`
- 官方参数表：1.18.2 的 `data/minecraft/dimension/overworld.json`
