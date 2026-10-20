# AGENTS.md

## 关键目录

| 路径 | 作用 |
| --- | --- |
| `build.py` | 构建入口：按 `build_settings.py` 依次构建并打包全部版本 |
| `build_settings.py` | 唯一的项目配置：产物目录、共享目录、版本列表 |
| `<版本>/` | 每个支持版本的源目录（如 `1_20/`），放补丁脚本与新增资源 |
| `patch_lib/` | 补丁的共享实现，如 `mcmeta.py` |
| `common/` | 跨版本共享的原版源文件与新增静态资源 |
| `tools/` | 构建框架子模块 `builder/`、`json_diff.py`、补丁接口模板 |
| `doc/` | 设计文档、补丁适配指南与逐版本改动对照 |
| `ref/` | 只读参考：反编译源码、原版 dump（已 gitignore） |
| `build/` | 构建产物（已 gitignore） |

## 构建与验证

- 构建：`python build.py`；产物为 `build/<版本目录>/` 与 `build/*.zip`。
- 清理字节码缓存：`python tools/clean.py`，在仓库根运行，跳过 `build/`、`.git` 与虚拟环境目录。
- 新增版本须先在 `build_settings.py` 注册。版本按声明顺序构建，只能引用声明在前的版本。
- 单文件比对：`python tools/json_diff.py <原版文件> <产物文件>`。
- 新增版本与迁移的适配步骤、目标值、验收标准见 `doc/IMPLEMENTATION.md`。
- 产物核对以 `doc/IMPLEMENTATION.md` 各节「目标效果」为准：差异应恰好覆盖该节列出的字段，未列出的同名文件应零差异。设计判断见 `doc/DESIGN.md`。

## 版本目录与补丁

- 版本目录只放补丁脚本与确实新增或整体改写的资源，不得整份复制未改动的原版 JSON。
- 补丁按命名空间放在 `<包根>/data/<namespace>/` 下，同类别且同时变化的资源合并为一个 `*__multi.py`；文件名只作描述，目标路径由 `reference_file` 给出。
- 包根指补丁所在包在 zip 内的前缀目录：本体为 `.`，overlay 为 overlay 目录名（如 `26_2_noise`）。
- 目标路径在补丁内按相对包根的路径声明，与 `patch_lib.paths.package_root(patch_path)` 拼接；同一张表因此同时适用于本体与 overlay。
- overlay 目录名需同时在 `pack.mcmeta` 的 `overlays.entries` 中登记，并给出其格式范围。
- `process_multi` 按目标路径显式分派（如以目标路径为键的字典），不用 `if/else` 的顺序或 `else` 兜底；未登记的目标应报错。
- 仅当补丁与目标文件同名时使用 `___`：文件名即目标文件名（`.` 写作 `___`），如 `pack___mcmeta.py`。
- 补丁声明 `TYPE = 'json'`，并暴露 `reference_file` 与 `process_single` / `process_multi`，接口见 `tools/template/json_patcher.py`。
- 补丁顶部的大写常量是可调参数，取值即当前决策，不是默认值；注释里的 `vanilla` 值只作对照，`1.0` / `True` 是「不缩放」哨兵（`XZ_SCALE_*` 的基准是原版 `0.25`）。详见 `doc/IMPLEMENTATION.md` 的「参数常量」。
- `reference_file` 的来源键：`COMMON` 指 `common/`，`MC_0` 指当前版本的静态文件，其他 `MC_*` 指已构建的旧版本产物；目标路径相对当前版本的构建根目录。

## 原版数据与参考资料

- 修改原版 JSON 时，先把原版文件原样复制到 `common/vanilla/<版本>/`，补丁以 `('COMMON', ...)` 引用，只写修改逻辑，不重复原版字段。
- `common/` 按「类别/版本」组织，版本目录内用 `<类别>__<标识>.json` 扁平存放，不镜像原版的 `data/minecraft/` 路径。
- `common/pack.mcmeta` 是共享的包描述模板；版本补丁只提供格式字段（`pack_format` 或 `min_format`/`max_format`）与需要时的 `overlays`，描述沿用模板，需改动时显式传入。
- 沿用旧版本原版数据时，把该版本原文件也放进 `common/`，并在 `patch_lib/` 提供该版本的解析器，输出与版本无关的数据结构。
- 各版本补丁自写适配函数把该结构转成自己的 JSON 格式；`patch_lib/` 不产出任何具体版本的 JSON。
- `ref/` 只读且不纳入版本控制：可查看、可临时导出到仓库外，但不得被构建脚本、配置或资源引用，也不得留在构建输入链路上。
- 补丁给出的目标路径按目标版本的实际布局书写；26.1 起为单数目录，如 `loot_table/`、`worldgen/structure_set/`、`worldgen/placed_feature/`。
