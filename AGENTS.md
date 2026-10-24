# AGENTS.md

## 关键目录

| 路径 | 作用 |
| --- | --- |
| `build.py` | 构建入口：按 `build_settings.py` 依次构建并打包全部版本 |
| `build_settings.py` | 唯一的项目配置：产物目录、共享目录、版本列表 |
| `<版本>/` | 每个支持版本的源目录（如 `1_20/`），放补丁脚本与新增资源 |
| `patch_lib/` | 补丁的共享实现与旋钮 |
| `common/` | 跨版本共享的原版源文件与新增静态资源 |
| `tools/` | 构建框架子模块 `builder/`、`json_diff.py`、补丁接口模板 |
| `generator/` | 不参与构建的分析与数据生成脚本 |
| `doc/` | 设计、实现指南、补丁组织约定与迁移进度 |
| `.github/skills/` | 适配版本的流程 |
| `ref/` | 只读参考区（已 gitignore） |
| `build/` | 构建产物（已 gitignore） |

## 文档分工

| 文件 | 回答什么 |
| --- | --- |
| `doc/DESIGN.md` | 为什么改、改到什么程度算够 |
| `doc/IMPLEMENTATION.md` | 每项改动的目标值、约束与验收判据 |
| `doc/PATCHING.md` | 补丁与数据怎么组织 |
| `.github/skills/adapt-mc-version/SKILL.md` | 适配一个新版本的步骤 |

## 构建与验证

- 构建：`python build.py`；产物为 `build/<版本目录>/` 与 `build/*.zip`。
- 清理字节码缓存：`python tools/clean.py`，在仓库根运行，跳过 `build/`、`.git` 与虚拟环境目录。
- 单文件比对：`python tools/json_diff.py <原版文件> <产物文件>`。
- 版本差异与 overlay 区间：用版本差异扫描工具输出各目标文件的内容分段。
- 产物核对以 `doc/IMPLEMENTATION.md` 各节的「目标值」与「验收」为准：差异应恰好覆盖该节列出的字段，未列出的同名文件应零差异。

## 红线

1. 版本目录只放补丁脚本与确实新增或整体改写的资源，不整份复制未改动的原版 JSON。
2. 数值只在 `patch_lib/tuning.py` 取一处，版本补丁只写落点。
3. 产物只含补丁产出的文件与 `pack.mcmeta`。
4. `patch_lib/` 不产出任何具体版本的 JSON。
5. `ref/` 只读、已 gitignore：不得被构建脚本、配置或资源引用，不得留在构建输入链路上，内部结构不得在任何文件中描述。
6. 新增版本先在 `build_settings.py` 注册；按声明顺序构建，只能引用声明在前的版本。
