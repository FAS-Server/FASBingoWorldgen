# 实现指南

整体目标见 [DESIGN.md](DESIGN.md)，本文记录实现路线。各项改动按目标分节，每节先给目标值与各版本现状，再给落点与操作。

## 目标

1. 群系缩小
2. 增加结构密度
3. 调整战利品表，减小风险，增加可能性
4. 尽量保持物品价值的相对顺序不变



## 版本分界

1.18 重构了地形、结构与群系源，1.17 及以前与 1.18 起分属两套文件。以下是各项改动的落点。

| 机制 | 1.17 及以前 | 1.18 起 |
| --- | --- | --- |
| 地形 | `worldgen/noise_settings/<维度>.json` 的 `noise` 块 | 同名文件的 `noise_router` |
| 结构定义 | `worldgen/configured_structure_feature/` | `worldgen/structure/` |
| 结构分布 | `noise_settings` 的 `structures.structures` | `worldgen/structure_set/<集合>.json` 的 `placement` |
| 群系源 | `dimension/<维度>.json` 的 `biome_source`，主世界为 `vanilla_layered` | 同左，主世界为 `multi_noise` |
| 战利品表目录 | `loot_tables/` | 26.1 起为 `loot_table/` |
| 包格式字段 | `pack_format` | 26.1 起为 `min_format` 与 `max_format` |

- 1.17 起维度文件引入 `min_y` 与 `height`，主世界为 `0..256`；1.18 起主世界为 `-64..320`。
- 原版数据取自官方 worldgen dump 或反编译源码。反编译产物自 1.20.1 起含 `worldgen/`，更早的版本只能取 dump。
- 字段是否存在不能作为版本判断依据。旧版本的编解码器会忽略新增字段，例如 1.16.5 忽略 `min_y`、`height`、`aquifers_enabled`、`noise_caves_enabled`、`deepslate_enabled`。

## 补丁形态

- 版本目录下的 `.py` 文件是补丁，其余文件作为静态资源原样复制进产物。
- 补丁暴露 `TYPE`、`reference_file` 与 `process_single` 或 `process_multi`。
- 被引用的原版文件放进 `common/vanilla/<版本>/`，扁平命名为 `<类别>__<标识>.json`，内容与基线逐字节相同。
- 目标路径相对包根书写，与 `patch_lib.paths.package_root(patch_path)` 拼接，使同一张表同时适用于本体与 overlay。
- 同类别且同时变化的资源合并为一个 `*__multi.py`，按目标路径显式分派，未登记的目标报错。
- `pack.mcmeta` 的描述取自 `common/pack.mcmeta`，版本补丁只提供格式字段。
- 版本按声明顺序构建，只能引用声明在前的版本。

### 参数常量

补丁顶部的大写全局常量是可调参数，取值即当前决策，不是「未配置时的默认值」。

- 参数注释里的 `vanilla` 取值是对照基准，用于换算，不表示关掉后回到该值。
- `1.0` 与 `True` 是「不缩放」的哨兵：对应文件或分支从产物中消失，不输出与原版相同的拷贝。仅当该值为哨兵时，参数才参与 `SOURCES` 与 `RELATIVE_PATCHERS` 的条件注册，因为需要增减源文件；只改字段内容的参数（如 `UNDERGROUND_RELIEF`）在补丁函数内判断。
- `XZ_SCALE_*` 的基准是原版 `0.25`，不是 `1.0`。
- 一个参数只在一处取值，被多处使用时引用同一常量（如地形与群系的 `xz_scale`）。
- 文档记录参数名与当前取值，不写「默认启用」或「默认关闭」。参数调整只改数值，不改文档结构。

## 离线工具

`generator/` 放不参与构建的分析脚本，与 `tools/` 的构建框架分开，因为后者是外部子模块。

- `generator/biome_scale.py`：按下界气候噪声重建群系场，输出各群系面积占比、斑块尺寸与「探全五个群系」所需的半径。
- 用于调尺度时先估算手感，不必反复开局。参数 `--multiplier` 取相对原版的频率倍率，与补丁里的 `xz_scale` 对应：`0.25 × 倍率`。
- 依赖 `numpy` 与 `scipy`。
- 参考值：倍率 `1` 时覆盖半径中位数约 `300` 格，`4` 时约 `75` 格，`8` 时约 `37` 格。瓶颈通常是诡异森林与灵魂沙峡谷。


## 群系缩小

基准见 [DESIGN.md](DESIGN.md) 的「原 bingo 基线」。

### 尺度依据

尺度以原版世界为 `1`。1.13 前「群系大小」是可选滑块，参数 `1`–`8`、默认 `4`，每加一尺寸翻倍；同页「河流大小」`1`–`5`、默认 `4`。滑块在 1.13 随地形重写移除，`large_biomes` 是其后仅存的相关开关。

两个值直接对应低版本 `vanilla_layered` 群系源的缩放层数：`OverworldBiomeSource` 按群系大小调用 `Layers.getDefaultLayer(seed, legacy, biomeSize, riverSize)`，主世界传 `4`，`large_biomes` 传 `6`，每次缩放把坐标刻度翻倍。据此：

- 原版默认 = `4`。
- `large_biomes` = `6`，为原版的 4 倍。
- 滑块最小 = `1`，为原版的 `1/8`；JSON 可直接写 `0`，为 `1/16`。

基准目标因此取 `1/8`，即滑块最小档。原 bingo 的 `level.dat` 实测 `biomeSize` 为 `1`，与推导一致。原 bingo 的 `riverSize` 为 `4`，即滑块默认值，说明河流未调整，河流密度无需另设旋钮。

换算关系：`firstOctave` 每加一，频率翻倍、线性尺度减半；`xz_scale` 翻倍等价。故 `1/8` 为加三，`1/4` 为加二。

噪声由 `firstOctave` 与 `amplitudes` 两项声明。`amplitudes` 必须照抄原版，它决定各倍频的权重，即布局的细节层次；自造成单一 `[1.0, 1.0]` 会改变网格细节。照抄可行的依据是两代 `NormalNoise` 等价：1.16.5 与 1.18.2 的输入因子同为 `1.0181268882175227`，归一化同为 `0.16666666666666666 / expectedDeviation(octaveSpan)`，且噪声坐标单位同为四格。因此同一组 `firstOctave` 与 `amplitudes` 在两代产生相同取值。

保真度差异：原版滑块只缩放群系层，海洋与湖泊的形状由独立的层生成，其缩放层数写死为 `6`，不受群系大小影响。改用 `multi_noise` 后，海洋作为表内条目与其余群系一同缩放，没有这个豁免。

### 目标效果

主世界取 `xz_scale` `1.8`，相对原版 `0.25` 为 `7.2` 倍频率。`1/8` 基准对应 `2.0`，`1.8` 是实测调参的结果，低版本无法精确复现 `7.2` 倍，按 `1/8` 取。

1.18 起，噪声文件保持原版，频率只改在 `xz_scale` 上。五个气候字段沿用原版的文件归属：

| 字段 | 原版形式 | 目标 | 1.18.2 | 1.20 | 26.1 |
| --- | --- | --- | --- | --- | --- |
| `temperature` | `noise_router` 内联 `shifted_noise` | 内联字段 `xz_scale` `1.8` | `firstOctave` `-7` | 同 1.18.2 | 已达标 |
| `vegetation` | 同上 | 同上 | `-5` | 同 1.18.2 | 已达标 |
| `continents` | 引用 `overworld/continents` | 命名密度函数 `xz_scale` `1.8` | `firstOctave` `-6` | 同 1.18.2 | 已达标 |
| `erosion` | 引用 `overworld/erosion` | 同上 | `-7` | 同 1.18.2 | 已达标 |
| `ridges` | 引用 `overworld/ridges` | 同上 | `-5` | 同 1.18.2 | 已达标 |

命名密度函数由群系源与地形共用，改它即同时作用于两侧，不需要另设地形侧落点。

1.17 及以前，目标是把四轴换成投影表：

| 轴 | 目标 `firstOctave` | 目标 `amplitudes` | 原版值 | 1.16.5 | 1.17.1 |
| --- | --- | --- | --- | --- | --- |
| `temperature` | `-7` | `[1.5, 0.0, 1.0, 0.0, 0.0, 0.0]` | 无此噪声 | `-4`，`[1.0, 1.0]` | `-5`，`[1.2, 1.2]` |
| `humidity` | `-5` | `[1.0, 1.0, 0.0, 0.0, 0.0, 0.0]` | 无此噪声 | `-5`，`[1.0, 1.0]` | `-5`，`[1.2, 1.2]` |
| `altitude` | `-6` | `[1.0, 1.0, 2.0, 2.0, 2.0, 1.0, 1.0, 1.0, 1.0]` | 无此噪声 | `-5`，`[1.0, 1.0]` | `-6`，`[1.2, 1.2]` |
| `weirdness` | `-4` | `[1.0, 2.0, 1.0, 0.0, 0.0, 0.0]` | 无此噪声 | `-4`，`[1.0, 1.0]` | `-4`，`[1.2, 1.2]` |
| 群系参数表 | 投影表，条目数按档位 | 原版表 | `vanilla_layered` | 68 条自建表 | 29 条自建表 |

低版本用 `firstOctave` 表达频率，只能取到 8 倍；26.1 的 `1.8` 对应 `7.2` 倍，低版本无法精确复现，按 `1/8` 取。

下界目标取 4 倍，即 `xz_scale` `1.0`；1.17 及以前等效为 `firstOctave` 加二。

| 项目 | 目标值 | 原版值 | 1.16.5 | 1.17.1 | 1.18.2 | 1.20 | 26.1 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `temperature` | `xz_scale` `1.0` | `0.25` | 未改 | `firstOctave` `-5` | `0.65` | `0.65` | `1.0` |
| `vegetation` | `xz_scale` `1.0` | `0.25` | 未改 | `firstOctave` `-5` | `0.65` | `0.65` | `1.0` |
| `nether_wastes` 的 `offset` | `0.0` | `0.0` | `0.0` | `0.2` | 不适用 | 不适用 | 不适用 |

### 1.18 起：气候噪声的共享结构

原版 `noise_router` 的 `continents`、`erosion`、`ridges` 引用命名密度函数 `minecraft:overworld/<轴>`，而地形也读这三个函数（`factor`、`offset`、`jaggedness` 经它们取值）。改这三个函数会同时改群系与地形，改 `noise_router` 的内联字段只改群系。

两侧取同一频率时，不动 `noise_router` 的引用，只改三个命名密度函数的 `argument.xz_scale`：

```json
{
  "type": "minecraft:flat_cache",
  "argument": {
    "type": "minecraft:shifted_noise",
    "noise": "minecraft:continentalness",
    "shift_x": "minecraft:shift_x",
    "shift_y": 0.0,
    "shift_z": "minecraft:shift_z",
    "xz_scale": 1.8,
    "y_scale": 0.0
  }
}
```

`temperature` 与 `vegetation` 在原版 `noise_router` 里就是内联的 `shifted_noise`，地形不读它们，直接改其 `xz_scale`。

`worldgen/noise/*.json` 保持原版：频率只在密度函数层表达，`firstOctave` 与 `amplitudes` 不动。

把三个字段内联进 `noise_router` 也能只影响群系，但会让两侧各自取值、靠人工保证相等，任一侧调整都会漂移，因此不采用。

### 1.17 及以前：四轴投影

1.18 前的主世界群系源读四轴，没有官方主世界参数表。投影的前提是两代群系源结构不同：

| | 低版本 | 高版本 |
| --- | --- | --- |
| 读取的轴 | `temperature`、`humidity`、`altitude`、`weirdness` 四条，各 `[-2, 2]` | 上述四条加 `continentalness`、`erosion`、`depth` 共七条 |
| 轴的值形式 | 单个浮点（点） | `[min, max]` 区间 |
| 匹配方式 | 最近邻，五项平方和最小 | 区间距离最小 |
| `offset` 作用 | 采样恒传 `0.0`，实际是加性优先级，非独立轴 | 同左 |
| `depth` 采样 | `useY` 硬编码为 `false`，四轴都在 `y=0` 采样，纯二维 | 随高度变化 |

官方主世界 surface 表实际用到五条轴：`temperature`、`humidity`、`continentalness`、`erosion`、`weirdness`，`depth` 恒为 `point(0)`。低版本只有四条，因此投影必须丢一条轴。两版的 `multi_noise` 都接受内联的 `biomes` 与 `*_noise` 字段，不必依赖预设名。

目标是把它投影到四轴：

| 源轴 | 目标轴 |
| --- | --- |
| `temperature` | `temperature` |
| `humidity` | `humidity` |
| `continentalness` | `altitude` |
| `weirdness` | `weirdness` |
| `erosion` | 丢弃 |
| `depth` | 丢弃 |

- 源表取 1.18.2 的 `dimension/overworld.json` 内联 `biomes`，共 7578 条、50 个群系。源表不可用时按 `OverworldBiomeBuilder` 复现。
- 各轴取源区间中点，`offset` 统一写 `0.0`。
- 丢弃 `erosion` 不构成信息损失：低版本群系没有侵蚀度概念，地形变体由 `altitude` 与 `weirdness` 表达。
- 投影结果为 2058 个唯一点位，其中 598 个点位存在多个源条目，表现为同一气候下的侵蚀度变体塌缩。

冲突消解按两级规则挑选代表群系：

1. 候选中的非变体群系优先。
2. 仍有多个时取出现次数最多者。

变体群系指 `sunflower_plains`、`ice_spikes`、`old_growth_*`、`sparse_jungle`、`bamboo_jungle`、`eroded_badlands`、`wooded_badlands`、`meadow`、`cherry_grove`、`grove`、`snowy_slopes`、`*_peaks`、`stony_shore`、`windswept_*`。

官方表中部分群系在低版本没有同名对应，按下表降级：

| 官方 | 低版本 |
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

低版本的群系查找是线性扫描，条目数直接决定区块生成开销；高版本用 `Climate.ParameterList` 内的 R-tree，对数级，不敏感。因此只有低版本需要控制规模，按档位出产物：

| 档位 | 量化粒度 | 条目数 | 群系数 | 缺失的必备群系 |
| --- | --- | --- | --- | --- |
| `full` | 不量化 | 2058 | 47 | 无 |
| `balanced` | `0.25` | 1046 | 42 | 无 |
| `lite` | `0.5` | 130 | 25 | `river`、`swamp`，需按必备群系保底补回 |

量化粒度 `0.25` 是不损失必备群系的前提下能达到的最粗粒度；`1/3` 起即丢失 `river`（538 条、37 个群系），因此不作档位。必备群系指海洋、河流、海岸、蘑菇岛与各基础陆地群系。三档的产物结构相同，只是条目集合不同，可整套替换。

投影产物提交为版本目录内的静态文件，因为源表不在本仓库，构建环境取不到。

### 下界群系尺度

目标取原版 4 倍。

| 版本 | 落点 | 改法 |
| --- | --- | --- |
| 1.16.5 | `dimension/the_nether.json` | `temperature_noise` 与 `humidity_noise` 的 `firstOctave` 由 `-7` 改 `-5` |
| 1.17.1 | 同左 | 同左 |
| 1.18.2 与 1.20 | `noise_settings/nether.json` 的 `noise_router` | `temperature` 与 `vegetation` 的 `xz_scale` 由 `0.65` 改 `1.0` |
| 26.1 | 同左 | 同左 |

1.17 及以前用 `firstOctave`，加二即 4 倍；1.18 起用 `xz_scale`，`1.0` 相对原版 `0.25` 为 4 倍。

### 编写指导：1.16.5 与 1.17.1

落点是 `dimension/overworld.json` 的 `biome_source`。

- 把 `biome_source.type` 改为 `minecraft:multi_noise`。
- 写入 `temperature_noise`、`humidity_noise`、`altitude_noise`、`weirdness_noise` 与投影得到的 `biomes` 表。
- `seed` 同时写 `generator.seed` 与 `generator.biome_source.seed`，两处取值相同。
- 1.16.5 同时移除原版 `vanilla_layered` 的 `large_biomes` 字段。

群系噪声内联在 `biome_source`，与 `noise_settings` 的地形噪声互不相干，改频率不影响地形。两版结构一致，只是条目表与噪声参数不同：

- 1.16.5 与 1.17.1 的噪声参数取目标效果表的 `firstOctave` 与 `amplitudes` 两列，替换现有取值。
- 1.17.1 另需替换现有的 29 条自建群系表。

### 编写指导：1.18.2 与 1.20

两版共用同一套源，取值逐字段相同。

- `worldgen/noise/<噪声>.json` 不修改；版本目录内已有的这些文件删除。
- `worldgen/noise_settings/overworld.json` 的 `temperature` 与 `vegetation` 就地改 `xz_scale` 为 `1.8`。
- 为 `overworld/continents`、`overworld/erosion`、`overworld/ridges` 提供覆盖文件，只改 `argument.xz_scale` 为 `1.8`。三者属于内置条目，需以完整原文件作源。
- `worldgen/noise_settings/nether.json` 的 `temperature` 与 `vegetation` 的 `xz_scale` 改 `1.0`。

覆盖内置命名密度函数要求文件结构与目标版本一致，迁移时以产物与基线的逐文件比对确认。

### 编写指导：26.1

落点是 `terrain__multi.py`，源文件取 `common/vanilla/26_1/`。

- `noise_settings/overworld.json` 的 `temperature` 与 `vegetation` 就地改 `xz_scale` 为 `1.8`；`continents`、`erosion`、`ridges` 保持原版引用。
- 三个命名密度函数 `overworld/continents`、`overworld/erosion`、`overworld/ridges` 的 `argument.xz_scale` 改 `1.8`，由 `TERRAIN_DENSITY_FUNCTIONS` 驱动。
- `depth` 引用包一层 `×1/UNDERGROUND_RELIEF` 的 `mul`。
- `noise_settings/nether.json` 的 `temperature` 与 `vegetation` 的 `xz_scale` 改 `1.0`。

频率只有一个取值 `XZ_SCALE_OVERWORLD`，群系与地形不可能漂移。

下界地貌不随群系缩放，`noise_settings/nether.json` 只改气候字段。



## 地形调整

群系频率提高后，同样的垂直振幅分布在更短的水平距离上，坡变得陡而碎，峰顶成尖。本节把高地压低，并保证不改变以 `depth` 为输入的地形与地下机制。

### 机制约束

地表高度只能经 `offset` 与 `jaggedness` 调整，`depth` 不动。

- `depth` 被三处使用，改它会静默移动地下群系：地形密度经 `overworld/sloped_cheese` 读它；群系源的第五轴直接取 `noise_router.depth`，`dripstone_caves` 与 `lush_caves` 取 `0.2..0.9`，`deep_dark` 取 `1.1`；深暗之域另有一处硬编码判定，条件为 `erosion` 低且 `depth` 大于 `0.9`。三处都以斜率为每单位 `128` 格、零点在地表为前提，改区间或端值会同时改变斜率与零点。
- 地表高度由 `offset` 给出：

$$
y_0 = 128 + 128 \cdot (offset_{const} + offset_{spline})
$$

压正值叶等价于压低陆地并把坡度同步压缓，两个效果出自同一个乘法。负值叶是海洋深度，保持原版使海深、海岸线与沙滩位置不变。
- `jaggedness` 只加在低侵蚀、高脊的峰顶，值为零的叶覆盖海洋、海岸、平原与湿地，缩放后仍为零。
- `factor` 不参与地表求解，改它改变的是地形与 `base_3d_noise` 的相对比重，不是坡度。

### 目标效果

| 项目 | 26.1 取值 | 原版 | 落点 |
| --- | --- | --- | --- |
| 高地高度 | `offset` 正值叶乘 `0.45` | 地表 `25..256` | `density_function/overworld/offset.json` |
| 峰顶细节 | `jaggedness` 全部叶乘 `0.45` | 最大叶值 `0.63` | `density_function/overworld/jaggedness.json` |
| 陡坡 | 系数 `1.0`，该文件不进产物 | `0.625..6.3` | `density_function/overworld/factor.json` |
| 地下群系带 | `depth` 引用包一层 `×1/0.9` 的 `mul` | 深暗之域在地表下 141 格 | `noise_settings/overworld.json` 的 `depth` |

各项系数按同一比例取，使峰顶细节与山体高度同步缩小。系数取哨兵值时该文件不进产物，可直接与原版对照。

海平面以上的地表越低降得越多，海平面处是不动点。依赖地表高度的结构（村庄、神殿、废弃传送门的 y 坐标）随之移动，这是预期结果。

### 地下群系带

地下群系的层位由 `depth` 轴给出，零点跟地表走，所以山地被压低后山下的带随之下移，平原与海洋处逐值不变。

若要连层带本身一起压短，只包装 `noise_router` 的 `depth`，不改命名密度函数：地形仍经 `sloped_cheese` 读原版函数，密度与洞穴形状不变，只有群系采样器取到放大后的值。

| 相对深度 | 原版 | 压缩到 `0.9` |
| --- | --- | --- |
| 洞穴带 `0.2` | 26 格 | 23 格 |
| 洞穴带 `0.9` | 115 格 | 104 格 |
| 深暗之域 `1.1` | 141 格 | 127 格 |

参数为 `UNDERGROUND_RELIEF`，当前 `0.9`。代价是平坦地面的地下带同步上移：平原可用深度为 `127` 格，压缩比低于约 `0.9` 时深暗之域会进入世界底部，当前取值贴近该临界。该阈值由 `offset` 的基准常量决定，换版本需重算。

### 编写指导：1.18 起

只改三张密度函数的 spline 叶值，结构与原版一致。

- `offset.json`：正值叶乘高地系数，负值叶不动。
- `jaggedness.json`：全部叶乘峰顶系数。
- `factor.json`：大于 `1.0` 的叶改为 `1 + (v - 1) × 陡坡系数`，其余不动。

导数的局部斜率跟着叶值同乘，曲线形状保持，不会在分段处出现折角。

1.17 及以前没有独立的密度函数文件，该改动不适用；`1_16_5` 的 `noise.bottom_slide` 属旧机制，按「版本迁移」处理。

### 验收

- 海洋与海岸：`offset` 负值叶逐字段等于原版，海平面附近的地表高度不变。
- 平原：`jaggedness` 叶值为零处的地形逐块等于原版。
- 地下：`final_density`、`preliminary_surface_level`、`surface_rule` 与基线逐字段相同；`noise_router` 的 `depth` 是引用外加一层 `mul`，命名密度函数 `overworld/depth` 本身不变。
- 不出现硬截断：高度上限仍为 `320`，峰顶不被削平。



## 增加结构密度

### 目标效果

密度按维度整体缩放，只对个别结构集合单独覆盖，不逐集合给终值。同一套规则适用于全部支持版本，落点随版本不同。

每个维度一组系数，作用在该版本原版的 `spacing` 与 `separation` 上：

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
| `strongholds` | `distance` `10`、`spread` `6` | `distance 32`、`spread 3` |

排除项：

| 集合 | 原版 | 原因 |
| --- | --- | --- |
| `mineshafts` | `1/0`，`frequency` `0.004` | 密度由 `frequency` 决定，缩放 `spacing` 无意义 |
| `ocean_monuments` | `32/5` | 按设计保持原版 |
| `nether_fossils` | `2/1` | 缩放后 `separation` 会顶到 `spacing` |

`ruined_portals` 在原版是单一集合，主世界与下界变体共用 `placement`，维度由各结构定义的群系标签过滤，因此按主世界系数缩放。1.18 前的结构表按维度分开，可分别缩放。

怪物房数量取浅层 `50`、深层 `20`，浅层高度上界压到 `128`。这两个值属测试期参数，实机验证后可能调整；调整只改数值，不改本节的其余规则。

### 机制分界

结构密度拆成三类落点，版本间形态不同。

- 结构分布：1.17 及以前写在 `noise_settings` 的 `structures.structures`，要塞另在 `structures.stronghold`；1.18 起写在 `structure_set/<集合>.json` 的 `placement`。
- 怪物房：1.16.5 与 1.17.1 写在 `configured_feature/monster_room.json` 的 `decorator.config.count`；1.18 起写在 `placed_feature/monster_room*.json` 的 `count` 与 `height_range` 项。
- 埋藏宝藏：1.17.1 与 1.18.2 写在 `configured_structure_feature/buried_treasure.json` 的 `config.probability`；1.20 起写在 `structure_set/buried_treasures.json` 的 `placement.frequency`。

1.16.5 的结构表在 `overworld.json` 与 `nether.json` 各有一份；1.17.1 另加 `end.json`，三份内容相同，改动需同步。

### 编写指导：1.16.5 与 1.17.1

落点是 `noise_settings/<维度>.json` 的 `structures.structures`，每维度一份表。

- 取该版本原版的 `spacing/separation`，按上表系数缩放；不要以当前文件里的现值作基准。
- 两版的 `ruined_portal` 在主世界、下界、末地各有一条，按各自维度的系数分别缩放。
- `structures.stronghold` 改 `distance` `10`、`spread` `6`。
- 埋藏宝藏：1.16.5 改 `configured_structure_feature/buried_treasure.json` 的 `config.probability`；1.17.1 已达标。
- 怪物房：1.16.5 改 `configured_feature/monster_room.json` 的 `decorator.config.count`；该版本无深层变种。1.17.1 同样只有一处。

### 编写指导：1.18.2 与 1.20

落点是 `structure_set/<集合>.json` 的 `placement`，两版共用一套取值。现有静态文件仍是旧值，未按本策略迁移（迁移完成后删除本句）。

- 按上表系数缩放各集合原版的 `spacing/separation`，再应用覆盖项。
- 埋藏宝藏：1.18.2 改 `configured_structure_feature/buried_treasure.json` 的 `config.probability`，1.20 改 `structure_set/buried_treasures.json` 的 `placement.frequency`。
- 远古城市只有 1.20 起：`structure/ancient_city.json` 的 `max_distance_from_center` 由 `116` 改 `96`；`spacing` 按主世界系数缩放。
- 怪物房：`placed_feature/monster_room.json` 改 `50` 并把高度上界压到 `128`，`monster_room_deep.json` 改 `20`。

### 编写指导：26.1

落点是补丁：结构定义与结构集合归 `structure__multi.py`，怪物房归 `placed_feature__multi.py`，源文件取 `common/vanilla/26_1/`。

- `DIMENSION_SCALES` 存维度系数，`DIMENSION_SETS` 列该维度参与的原版集合，两者驱动同一套缩放。
- `SPECIAL_FIELD_OVERRIDES` 存覆盖项；排除集合的覆盖项以注释预置，解除注释并加入清单即可启用。
- `ruined_portals` 用单一集合，按主世界系数缩放。
- 怪物房取浅层 `50`、深层 `20`，浅层高度上界压到 `128`；深层变种的高度范围保持原版。



## 调整战利品表

### 目标效果

1. 猪灵以物易物的珍珠条目回调到 1.16.1 的权重与数量，其余条目保留本版原版
2. 末影人的珍珠掉落率设置保底 1，减少运气成分

| 项目 | 目标值 | 原版值 | 1.16.5 | 1.17.1 至 1.20 | 26.1 |
| --- | --- | --- | --- | --- | --- |
| 珍珠条目 `weight` | `20` | `10` | `20` | `20` | 已达标 |
| 珍珠条目 `count` | `4..8` | `2..4` | `4..8` | `4..8` | 已达标 |
| 其余条目 | 本版原版 | 本版原版 | 已换成 1.16.1 | 已换成 1.16.1 | 已达标 |
| 末影珍珠 `count.min` | `1` | `0` | 未改 | 已达标 | 已达标 |

1.16.2 起原版把珍珠条目由 `weight` `20`、数量 `4..8` 降为 `weight` `10`、数量 `2..4`，单次期望由 `0.284` 降到 `0.065`。本项目只回调这一条，不碰表内其余条目。

不改条目集合的理由：新版新增的交易属于内容广度，删掉无收益；而珍珠供应已由末影人保底解决，以物易物只需保住这条捷径。

下界合金锄仅存在于 `20w09a` 至 `20w20a` 的快照，1.16 正式版发布前已移除以物易物，因此任何正式版的原版表都不含该工具。

### 格式迁移

当前方案只改珍珠条目的两个字段，不重写条目集合，本节仅在改用整表替换时需要。

旧版本战利品表的写法与现代格式的对应：

| 旧写法 | 现代写法 |
| --- | --- |
| `set_nbt` 配 `{Potion:"<id>"}` | `set_potion` 配 `id` |
| `enchant_randomly` 的 `enchantments` 列表 | `options`，单元素可写裸 id |
| `set_count` 依赖默认的替换语义 | 显式写 `add: false` |
| 无 `random_sequence` | 保留目标版本原版的该字段 |
| 无 `bonus_rolls` | 保留目标版本原版的分池字段 |

- 只替换条目集合时，表的外壳取目标版本原版。
- `patch_lib/loot_table_1_16.py` 与 `common/vanilla/1_16_1/` 的整表可解析为与版本无关的结构，当前未接入构建，留作整表替换的备用。
- 解析器对未识别的字段报错，改用整表替换后新增交易不会被静默误读。

### 编写指导：1.16.5

- 以物易物：按条目名找到 `minecraft:ender_pearl`，`weight` 改 `20`，`set_count` 的 `count` 改 `min` `4.0`、`max` `8.0`。
- 同时把表恢复为本版原版，修掉已换入的 1.16.1 条目。
- 末影人：`loot_tables/entities/enderman.json` 的 `count.min` 由 `0` 改 `1`。该版本有这份文件，实体掉落走战利品表。

### 编写指导：1.17.1 至 1.20

- 以物易物：同上，按条目名定位珍珠条目后改 `weight` 与 `count`。
- 同时把表恢复为本版原版。1.17.1 至 1.20 的原版条目数均为 18，含黑石、追踪之箭、水瓶。
- 末影人：`count.min` 改 `1`。

### 编写指导：26.1

- 以物易物：`loot_table/gameplay/piglin_bartering.json` 的珍珠条目 `weight` 改 `20`，`count` 改 `4..8`，其余条目与原版一致。原版条目数为 19，较 1.17.1 至 1.20 多一条脱水幽灵。
- 末影人：`count.min` 改 `1`，保留 `random_sequence`。
- 两者归 `loot_table__multi.py`，目标路径为 `loot_table/`，单数。



## 版本迁移

### 老实现差异

1.18 前的版本目录早于构建器，整份 JSON 提交。各节目标表的版本列与目标值不符即为待办，本表只列目标表无法表达的项。迁移完成即删本节。

- 底部过渡：1.16.5 的 `noise.bottom_slide` 改为 `size 3`、`target 15`，取值来自 1.17 起原版，与该版重写后的初始密度公式配套。1.16.5 的公式未变，开启后只会把底部若干格强制实心，压掉该区间的洞穴与矿脉，应恢复为 `size 0`、`target -30`。
- 地下带压缩：1.18.2 与 1.20 不设，`depth` 保持原版。
- 冗余文件：1.17.1 有 30 份与基线零差异的 `configured_structure_feature/*.json`；1.16.5 的 `dimension/the_nether.json` 与 1.18.2 的 `structure_set/buried_treasures.json` 同样零差异，应删除。
- 冗余字段：1.16.5 的 `dimension_type/*.json` 显式写了 `min_y` 与 `height`，该版编解码器忽略这两项，可删。

### 迁移顺序

迁移完成即删本节。

1. 先完善 26.1 的补丁实现，作为其余版本的参照。
2. 按 1.20、1.18.2、1.17.1、1.16.5 自新到旧迁移。
3. 每版把需要修改的原版文件放进 `common/vanilla/<版本>/`，按目标效果节的策略写补丁。
4. 1.18.2 与 1.20 先删除噪声文件再改密度函数，顺序不可颠倒：噪声回到原版后，密度函数上的频率才是唯一取值。
5. 以产物与基线的逐文件比对为验收：除「老实现差异」列出的项外，迁移前后产物应等价。
6. 迁移完成后移除 `1_17_1/` 下的 `biomes.csv` 与 `convert_biome.ipynb`，它们是被投影表取代的原型。

## 校验

### 构建

- 运行 `python build.py`，确认全部版本成功。产物只含改动过的文件与 `pack.mcmeta`，文件集合与改动清单一致。
- 运行 `python tools/clean.py`，确认仓库内没有 `__pycache__`。

### 差异

- `python tools/json_diff.py <基线文件> <产物文件>`。每个文件的差异应恰好等于该改动项的字段，不多不少。生成后与基线相同说明补丁未生效或方向错误。
- 战利品：以物易物表相对基线的差异应只有珍珠条目的 `weight` 与 `set_count` 的 `min`、`max` 三项。

### 语义

- 共享：`noise_router` 的 `continents`、`erosion`、`ridges` 仍是字符串引用，三个命名密度函数的 `argument.xz_scale` 均为 `1.8`。
- 内联：`temperature` 与 `vegetation` 的 `xz_scale` 均为 `1.8`，且 `noise/*.json` 的 `firstOctave` 与 `amplitudes` 等于基线。
- 引用链：确认 `minecraft:overworld/continents`、`minecraft:overworld/erosion`、`minecraft:overworld/ridges` 仍被 `noise_router` 与地形密度函数共用。
- 地下：`noise_router` 的 `depth` 是原版引用外加一层 `mul`，`final_density`、`preliminary_surface_level` 与 `surface_rule` 与基线逐字段相同。
- 分段映射：`offset` 的负值叶、`factor` 不大于 `1.0` 的叶逐字段等于基线，零值处保持零。
- 地表：海平面附近的高度与原版一致；峰顶高度应低于原版上限 `256`，且不出现硬截断。
- 格式：`pack.mcmeta` 含目标版本的格式字段与 `common/pack.mcmeta` 的描述，且不含过期字段。
- overlay：把补丁临时放进 overlay 目录构建一次，确认产物落在 `<overlay>/data/...` 下。

## 参考来源

原版类路径均以 `net/minecraft/` 开头，数据包内资源路径均以 `data/minecraft/` 开头。

- 群系大小与河流大小滑块、怪物房与矿石项的滑块范围：[Old Customized - Minecraft Wiki](https://minecraft.wiki/w/Old_Customized)
- 原 bingo 的设置实测值与出处：见 [DESIGN.md](DESIGN.md) 的「原 bingo 基线」
- 缩放层数：1.16.4 的 `net/minecraft/world/level/newbiome/layer/Layers.java` 与 `net/minecraft/world/level/biome/OverworldBiomeSource.java`
- 低版本群系源与匹配规则：1.16.4 的 `net/minecraft/world/level/biome/MultiNoiseBiomeSource.java` 与 `net/minecraft/world/level/biome/Biome.java`；1.17.1 的同名文件结构相同
- 噪声归一化：1.16.4 与 1.18.2 的 `net/minecraft/world/level/levelgen/synth/NormalNoise.java`
- 群系查表的空间索引：`net/minecraft/world/level/biome/Climate.java` 的 `ParameterList` 与 `RTree`
- 官方参数表：1.18.2 的 `data/minecraft/dimension/overworld.json`
