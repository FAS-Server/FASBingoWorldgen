---
name: adapt-mc-version
description: 适配新的 Minecraft 版本（1.18 起）：新增版本目录、判定 overlay 落点、迁移静态版本目录、重算数据格式区间。Use when adding a Minecraft version, choosing between a version directory and an overlay, migrating a static version directory to patches, or recomputing a pack or overlay data format range.
---

# 适配 Minecraft 版本

目标：新版本获得与既有版本相同的世界生成改造，产物只含改动过的文件。

本文的流程与判定方法适用至 26.3（数据格式 121.0）；数据组织与补丁接口见 [PATCHING.md](../../../doc/PATCHING.md)，目标值、约束与验收判据见 [IMPLEMENTATION.md](../../../doc/IMPLEMENTATION.md)。更晚的版本若改动了原版文件结构，先按「判定落点」跑扫描复核，再套用本文结论。

## 边界

- 本仓库覆盖 1.18 起的 `worldgen/` 布局。1.17 及以前用 `dimension/*.json` 的 `biome_source` 与 `noise_settings` 的 `noise` 块，机制不同：走 `patch_lib/worldgen_legacy.py` 与 `generator/biome_projection.py`，落点见 [IMPLEMENTATION.md](../../../doc/IMPLEMENTATION.md) 的「旧机制：四轴投影」，不适用本文的 overlay 流程。
- 字段名、目录名与语法形态的差异以版本差异扫描和构建时的工厂校验为准，不靠记忆版本号。工厂只接受它识别得出的结构，形态不符即报错；此时在 `patch_lib/` 增加该形态的处理，不放宽校验。

## 事实来源

- 原版文件与版本差异扫描工具在 `ref/`，只读，内容布局不在仓库内描述。
- 数据包导出不含 `worldgen/` 的版本，改用目标版本的官方世界生成数据作基线。
- 原版资源统一用包内相对路径描述，如 `data/minecraft/worldgen/noise_settings/overworld.json`；类用 `net/minecraft/...`。
- 数据格式取目标版本游戏元数据的 `pack_version`：`data_major` 与 `data_minor`，写成 `[major, minor]`。
- 文件在哪些版本之间变化，用版本差异扫描工具查，不要凭版本号推断。

## 判定落点

先对本系列版本跑一次内容分段扫描：每个目标文件列出内容分段，`[ ]` 内是数据格式，`(newest)` 段是目标版本的内容，`(anchor)` 段是既有版本目录所带基线仍正确的范围，其余段内容不同。

```text
worldgen/noise_settings/nether.json
  26.1-snapshot-1 [95.0] ~ 26.1-snapshot-10 [99.3]
  26.1-snapshot-11 [100.0] ~ 26.2-snapshot-3 [102.0]  (anchor)
  26.2-snapshot-4 [103.0] ~ 26.2-snapshot-4 [103.0]
  26.2-snapshot-5 [104.0] ~ 26.2 [107.1]  (newest)
```

扫描时把既有版本目录对应的版本名作为 anchor，省略时以系列最新版本为参照；目标可以是文件或目录，清单之外的文件需要显式追加。

| 扫描结果 | 做法 |
| --- | --- |
| 所有目标只有一段 | 目的版本与既有版本内容相同，只把 `pack.mcmeta` 的区间延长到它 |
| 少数目标另有分段，目录结构不变 | 在既有版本目录下做 overlay |
| 多数目标分段紊乱，或路径、字段形态变化 | 新建版本目录，在 `build_settings.py` 注册 |

overlay 规则：

- 目录放在既有版本目录内：`<版本目录>/<overlay>/data/<命名空间>/`，名字取 `<内容起始版本>_<主题>`。
- 一个 overlay 只放起点相同的目标；起点不同的目标分属不同 overlay，各自登记区间。
- 目录与区间登记在被覆盖版本的 `pack.mcmeta` 的 `overlays.entries`，注释写 `起始版本 ~ 末版本`。

```python
OVERLAYS = [
    {
        'directory': '26_2_nether',    # 26.2 snapshot-5 ~ 26.2
        'min_format': [104, 0],
        'max_format': [107, 1],
    },
]
```

- 区间只能切在数据格式号变化处：多个快照常共用同一格式号。
- 起点之前的版本仍由主包提供旧内容，这是允许的；需要覆盖那段就再切一个 overlay。

主包区间：

- 起点取各目标 `(anchor)` 段起点的最大值。
- 终点取目标内容仍然正确的最后版本；被 overlay 接管的目标不影响主包终点。
- 目标没有 `(anchor)` 段时，说明该目录所带的基线与 anchor 版本不一致，先修基线再定区间。

静态版本目录迁移为补丁时，按同一流程处理：每个改动过的目标一条「基线 + 补丁」，删除对应的整份 JSON。`1_18_2/` 目前仍是整份静态 JSON，不读 `tuning.py`，迁移时同样改写。旧静态目录若沿用了与 `tuning.py` 不同的数值，迁移会按 `tuning.py` 重算，此时产物不与迁移前等价，变化字段要逐项列出并确认是预期修正。迁移进度与已知偏差见 [PROGRESS.md](../../../doc/PROGRESS.md)。

## 注册

- 新版本目录在 `build_settings.py` 增加 `MC_*` 常量；声明顺序即构建顺序，只能引用声明在前的版本。
- 目录名与产物名取首个支持的版本；后续兼容版本、以及内容相同而格式号不同的版本，都不新建目录，只延长区间、加 overlay 或改格式字段。
- overlay 只登记 `overlays.entries`，不新增 `MC_*`。
- 版本目录至少有一个 `pack___mcmeta.py`，由 `mcmeta.make` 生成；字段按该包覆盖的数据格式区间选，规则见 [PATCHING.md](../../../doc/PATCHING.md) 的「包描述」。三种情形：
  - 全部落在 26.1 前：`pack_format` 写首个格式号，`supported_formats` 覆盖整段，如 1.20 的 `15` ~ `41`。
  - 全部落在 26.1 起：`min_format` 与 `max_format`。
  - 跨越两者：两套都写，区间一致。1.21 系列即此类（1.21 ~ 1.21.8 用前者，1.21.9 起用后者）。

## 验收

- `python build.py` 全部版本成功；`python tools/clean.py` 后没有 `__pycache__`。
- 逐文件 `python tools/json_diff.py <该版本基线> <产物>`：差异恰好是预期字段，且不出现多余字段。
- overlay 产物落在 `build/<版本>/<overlay>/data/...`，同名文件在主包之上生效。
- 改一个 `tuning.py` 的值重建：所有走补丁的版本同步变化，静态文件版本不变。
- 重构既有补丁时，先记录各产物与基线的差异字段，改完重建后逐项相同，才算无行为变化。

## 常见错误

- 取到的原版文件为空或不完整，先确认它确实属于该版本，再当作基线。
- 用 PowerShell 重定向写基线，文件变成 UTF-16。
- 基线经过 JSON 反序列化再写回：键序与格式被改写，基线不再是该版本原版文件的拷贝。
- overlay 目录没有登记到 `overlays.entries`：产物存在但游戏不加载。
- 把不同起点的文件塞进一个 overlay，区间只能取其中一段。
- 在新版本补丁里重复写数值，之后调 `tuning.py` 时漏掉该版本。
- 沿用 1.17 的 `noise_settings.noise` 或 `dimension` 落点处理 1.18+ 版本。
- 反过来用 1.18+ 的 `density_function`、`structure_set` 或 `placed_feature` 落点处理 1.16/1.17。
