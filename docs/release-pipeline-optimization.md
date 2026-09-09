# Release 耗时优化核对与实施

核对日期：2026-09-09。基线为 v0.8.8 的 [Release 运行 34304651286](https://github.com/jace-wjc/hr-toolkit/actions/runs/34304651286)。以下时间来自该次已完成的日志，不是本次重新构建的结果。

## 实际耗时

| 环节 | 现代 Windows | Win7 |
| --- | ---: | ---: |
| 整个构建任务 | 9 分 28 秒 | 4 分 36 秒 |
| Python 依赖安装 | 47 秒 | 38 秒 |
| Inno Setup 步骤 | 13 秒 | 6 秒 |
| 源码测试步骤 | 4 分 41 秒 | 27 秒 |
| PyInstaller 阶段，含脚本自带检查 | 97.0 秒 | 64.5 秒 |
| EXE 安装器阶段，含安装验证 | 93.5 秒 | 61.5 秒 |
| 桥接更新清单 | 0.3 秒 | 2.4 秒 |

Linux `validate` 共 55 秒，其中完整测试步骤约 30 秒。Win7 运行时准备为 5 秒。两个 Inno Setup 步骤的日志均为 `InnoSetup v6.7.1 already installed`，并未重新下载安装器。

## 对原方案的判断

1. **不能删除 Windows/Win7 测试并用 Ubuntu 测试替代。** 测试运行环境分别涉及 Windows、Python 3.8、PySide2 及不同平台的条件分支。`pip check` 是依赖一致性检查，OCR smoke 是运行时检查，都不是额外的一遍单元测试。
2. **依赖体积分析与仓库不符。** 当前 `requirements-gui.txt` 使用 `PySide6_Essentials`/`PySide2`，不使用方案描述的 PyQt6 + WebEngine。
3. **不能只改工作流就传入 `--incremental`。** `scripts/build_windows.py` 有该参数，但工作流调用的 `scripts/release_windows.py` 没有接收和转发它，直接添加会导致参数解析失败。
4. **提出的缓存方式不能支持“后续版本稳定命中”。** GitHub 明确限制不同 tag 之间的缓存访问；方案只在 tag 发布任务中保存缓存，缺少默认分支缓存来源。缓存键还包含 `hr_toolkit/**`，每次发布更新 `hr_toolkit/__init__.py` 中的版本号就会改变键。参见 [GitHub 缓存访问限制](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching#restrictions-for-accessing-a-cache)。
5. **不能承诺增量构建与清理构建字节完全一致。** 需要实际验证输入完整性、缓存失效与构建结果；本次未授权运行这些构建实验。正式发布继续使用现有清理构建。
6. **Inno 和 Win7 运行时缓存不符合此次日志中的瓶颈。** Inno 已预装，Win7 运行时仅需 5 秒；因此不新增目录缓存，也不跳过运行时下载脚本的 SHA-256 验证。将 pip 与 Chocolatey 放入后台进程也不是此次主要收益来源。

## 已实施

- `.github/workflows/release.yml` 新增 `validate-windows`：同一 tag、相同 Windows runner 类型、Python 3.12 及构建依赖约束，运行原有完整 Windows 测试。该任务与 Linux 校验和构建并行。
- 从 `build-windows` 移出完整测试步骤，保留原有 OCR、PyInstaller、安装器及产物检查。
- `publish.needs` 和成功条件均加入 `validate-windows`。测试失败或取消时不发布，即使构建已完成也不能绕过此条件。
- Win7 测试保留在原构建任务内；其 27 秒耗时不值得再增加一次 runner 初始化和依赖安装。
- Win10 优先复用预装 Inno Setup，缺失时才执行原安装命令；Win7 由 Chocolatey 确认固定的 6.7.1 版本，保留安装失败和编译器文件缺失检查，不再用 ISCC 的 ProductVersion 字段判断安装版本，避免错误阻断构建。未新增 PyInstaller 缓存或增量发布参数。
- 添加发布依赖关系的回归用例，防止后续误删 Windows 测试或发布条件。本次仅检查该测试文件的语法，未运行用例。

仅修改 Release 的任务安排和 Inno 准备步骤；日常 CI、安装器压缩参数、业务代码和已暂停的 MSI/DMG/ZIP 不变。

## 收益与验证边界

按基线做耗时相减，现代 Windows 构建任务有望从 9 分 28 秒降至约 4 分 34 秒。完整发布仍需等待独立的 Windows 测试、上传和镜像任务，估算约 7～8 分钟，不承诺整个 Release 小于 5 分钟。

这是基于旧日志的估算，尚无修改后的实测。增加独立 Windows 任务会多一次环境准备，因此优化的是等待时间，不保证减少 runner 总计费时间。Windows 测试失败时，已并行执行的构建也可能消耗额外资源。

本次只做修改文件的最小语法检查，不创建测试 tag、不触发工作流、不构建安装包、不执行测试套件。实际收益及 Windows 上的安装器探测逻辑留待下一次用户授权的发布运行确认。
