# 补丁与数据组织

> 仓库级的机制约定，与具体版本和具体任务无关。适配新版本的步骤见 [.github/skills/adapt-mc-version/SKILL.md](../.github/skills/adapt-mc-version/SKILL.md)，每项改动的取值与验收见 [IMPLEMENTATION.md](IMPLEMENTATION.md)，改动理由见 [DESIGN.md](DESIGN.md)。

## 版本目录

- 版本目录只放补丁脚本与确实新增或整体改写的资源，不整份复制未改动的原版 JSON。
- 补丁按命名空间放在 `<包根>/data/<namespace>/` 下。同类别且同时变化的资源合并为一个 `*__multi.py`。
- 文件名只作描述，目标路径由补丁声明，不靠文件名推断。

包根指补丁所在包在 zip 内的前缀目录：本体为 `.`，overlay 为 overlay 目录名（如 `26_2_noise`）。目标路径在补丁内按相对包根的路径声明，与 `patch_lib.paths.package_root(patch_path)` 拼接，同一张表因此同时适用于本体与 overlay。

## 补丁接口

- 补丁声明 `TYPE = 'json'`，暴露 `reference_file` 与 `process_single` 或 `process_multi`，接口见 `tools/template/json_patcher.py`。
- `process_multi` 按目标路径显式分派（如以目标路径为键的字典），不用 `if/else` 的顺序或 `else` 兜底；未登记的目标报错。
- 仅当补丁与目标文件同名时使用 `___`：文件名即目标文件名（`.` 写作 `___`），如 `pack___mcmeta.py`。
- `reference_file` 的来源键：`COMMON` 指 `common/`，`MC_0` 指当前版本的静态文件，其他 `MC_*` 指已构建的旧版本产物；目标路径相对当前版本的构建根目录。
- `dispatch.make(sources, patchers)` 生成三个入口：`sources` 是目标路径到 `common/` 相对路径的映射，`patchers` 是目标路径到处理函数的映射；未登记的目标报错。
- 处理函数由工厂提供：`worldgen_26.terrain`、`worldgen_26.structure`、`worldgen_26.placed_feature`、`loot_table.make`、`mcmeta.make`。工厂会校验输入形态（如内联 `shifted_noise`、`random_spread`、`set_count`），形态不符即报错；形态不同时在 `patch_lib/` 增加该形态的处理，不放宽校验。
- 可调参数集中在 `patch_lib/tuning.py`，取值即当前决策，不是默认值。版本补丁只写落点并引用它；目录名、集合清单与基线文件名属于落点，留在版本补丁里。
- `1.0` / `True` 是「不缩放」哨兵；`XZ_SCALE_*` 的基准是原版 `0.25`。注释里的 `vanilla` 值只作对照。

## 基线

- 只把补丁引用到的原版文件原样放进 `common/vanilla/<版本>/`，内容与该版本原版文件相同；补丁以 `('COMMON', ...)` 引用并只写修改逻辑，不重复原版字段。
- 不在版本目录或 `common/` 存放补丁未引用的原版 JSON，也不为相同内容存两份：新版本目录只放相对前一版有变化的文件，其余继续引用前一版目录。变化指解析后不相等，字段顺序与空白不同不算。
- 基线目录以内容所属版本命名，与补丁所在的版本目录无关。
- 新增基线时直接复制目标版本原版文件的原始字节，不经 shell 重定向，也不先反序列化再写回：反序列化会改键序与格式，使基线不再是该版本原版文件的拷贝。
- `common/` 按「类别/版本」组织，版本目录内用 `<类别>__<标识>.json` 扁平存放，不镜像原版的 `data/minecraft/` 路径。`worldgen/` 之后的路径用 `__` 连接，`worldgen_26.source_name` 生成同样的名字；战利品表省略子目录，名字在补丁里显式给出（`loot_table__enderman.json`）。

## 包描述

`common/pack.mcmeta` 是共享的包描述模板。版本补丁只提供格式字段与需要时的 `overlays`，描述沿用模板，需改动时显式传入。

字段写法由该包覆盖的数据格式区间决定：

- 全部落在 26.1 前：`pack_format` 写首个格式号，`supported_formats` 覆盖整段。区间必须包含 `pack_format`；较早的版本只读 `pack_format`，较新的版本读区间。
- 全部落在 26.1 起：`min_format` 与 `max_format`。
- 跨越两者：两套都写，且区间必须一致。新版会校验 `supported_formats` 的两端与 `min_format`/`max_format` 相符，并要求 `pack_format` 落在区间内；只写新字段会让旧版报「缺少 `pack_format`」。

overlay 条目按同一规则：26.1 前写 `formats`，26.1 起写 `min_format`/`max_format`，跨越时两处都写。

## 旧版原版数据

沿用旧版本原版数据时，把该版本原文件也放进 `common/`，并在 `patch_lib/` 提供该版本的解析器，输出与版本无关的数据结构。各版本补丁自写适配函数把该结构转成自己的 JSON 格式；`patch_lib/` 不产出任何具体版本的 JSON。

## overlay 与落点

- overlay 目录名需同时在 `pack.mcmeta` 的 `overlays.entries` 中登记，并给出其格式范围。
- 区间起点取「该目录的基线文件与目标版本内容相同的第一个数据版本」，通常是快照；终点取该内容存在的最后版本。起点不同的文件分属不同 overlay。
- overlay 补丁的参数同样取自 `patch_lib/tuning.py`，避免同一参数两处取值。
- 补丁给出的目标路径按目标版本的实际布局书写，不沿用旧版写法。目录、字段名与语法形态的差异以版本差异扫描与构建时的工厂校验为准，不靠记忆版本号。
- 版本事实适用至 26.3（数据格式 121.0）；适配更晚版本时先用版本差异扫描复核。
