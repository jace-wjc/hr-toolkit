# CI 失败根因记录

本文件记录已经核实的 CI 失败及防复发措施。每次提交前先阅读，再按本次改动检查相关项。后续收到 CI 失败反馈并检查时，追加记录；信息不足时标记“待确认”，不要猜测原因。

## 提交前检查

1. 核对本次暂存改动及其调用方，并检查下方与改动相关的记录。
2. 修改默认配置或新增必填信息时，核对现有测试样本是否仍满足入口要求；明确测试要覆盖的模式，保留业务校验。
3. 修改日期样本时，核对跨月、跨年、大小月和闰年的合法性，不直接把 29/30/31 日替换到不包含该日的月份。
4. 修改日志或提示文案时，区分通用说明与实际异常；断言应检查实际异常标记、字段或结果，避免宽泛关键词误判。
5. 修改界面名称、控件、信号参数或布局时，同步核对对应测试与 QML 探针；修改应用文件路径时核对 `scripts/ci_scope.py` 路由。
6. 检查不得变成未经授权的测试套件或全量构建。遵循 `AGENTS.md` 的验证范围，并明确说明本次实际检查、未验证项及远程 CI 状态。

## 2026-11-17：考勤测试样本与新规则不同步

### 失败证据

- CI：[44041772706](https://github.com/jace-wjc/hr-toolkit/actions/runs/44041772706)。
- 被检查提交：`d1ba99d753e4d69773bb3b28739d4d01d6459130`。
- Python 3.9、Python 3.12、Windows Python 3.12、Windows 7 兼容栈 Python 3.8 四个 job 均在 `tests.test_data_statistics` 失败：`failures=1, errors=3`，涉及下列三个测试方法（日期范围测试在两个年份各报错一次）。
- 安装依赖已成功；两个 Windows job 的 Qt 启动检查也已成功。本次应依据最终测试栈处理，不能推断为依赖或 Win7 启动故障。
- 测试执行器在失败模块停止，后续模块未继续执行；本记录不代表其他模块已经通过。

### 根因 1：跨月测试生成了不存在的 2 月 30 日

- 失败用例：`test_cross_year_carry_keeps_same_month_in_two_years_separate`。
- 报错：`ValueError: day is out of range for month`，发生在测试内的 `replace(month=2)`。
- 根因：`1f51841` 新增跨年用例沿用了含 1 月 30 日的样本，只替换月份而未调整日，尚未执行二月结转就异常退出。
- 修复：使用 `calendar.monthrange` 将样本日期限制到目标月份的最后一天；保留跨年同名月份区分及过期余额不再结转的断言。
- 影响文件：`tests/test_data_statistics.py`，不改业务日期解析或结转算法。
- 提交前检查：对日期构造代码检查目标月份是否合法，特别是 1 月转 2 月、闰年转非闰年。

### 根因 2：旧日期范围测试触发了新增的公司规则确认

- 失败用例：`test_september_ranges_remain_independent_through_form_and_excel_output`，2025 和 2026 两个分支。
- 报错：`TemplateSelectionRequired`，`kind=attendance_rules`，人员缺少公司信息。
- 根因：`1869f8f` 将界面默认模式改为按公司/驻地自动匹配；旧测试从 `default_values` 取配置，却继续使用不含公司/驻地的简化考勤样本，因而在日期统计前进入预期的规则确认流程。
- 修复：日期范围测试显式选择现有的统一规则模式 `attendance_auto_rules=False`，保留周/月范围独立、范围外数据排除、考勤单元格与样式不变等断言。自动匹配和缺失信息确认仍由已有专门用例覆盖。
- 影响文件：`tests/test_data_statistics.py`；保留正式界面的自动匹配默认值与缺失信息确认。
- 提交前检查：变更默认值时追踪使用 `default_values`、`build_invocation` 的测试，确保样本信息和测试模式一致。

### 根因 3：通用说明被宽泛关键词断言误判为人员异常

- 失败用例：`test_hr_september_example_accepts_named_history_sheet_and_keeps_current_rest`。
- 报错：`assertFalse(any("待核对" in warning ...))` 失败。
- 根因：`1f51841` 的正常结转说明包含“余额不足仍生成结果并高亮待核对”，测试把这段说明当成了实际异常。真正的人员异常使用完整标记 `【加班调休待核对】`。
- 修复：检查完整异常标记，并检查结果备注中没有该标记和异常批注；保留各月余额、当月调休、旧备注不带入及源文件不变的断言。
- 影响文件：`tests/test_data_statistics.py`；不删除或修改正式说明、异常提示及高亮逻辑。
- 提交前检查：正常状态的说明中可以提及异常处理方式，不能仅凭“失败”“异常”“待核对”等词判断发生了异常。

### 本地检查与待验证范围

- 修改范围：修正上述测试样本与断言，并在 `AGENTS.md` 中加入提交前阅读本记录及后续追加根因的要求。
- 本地检查：`tests/test_data_statistics.py` 的 Python 3.8 语法解析及 Python 3.13.0 字节码编译通过；编译产物放在临时目录，结束后清理。
- 本地未执行上述三个用例；语法/编译通过不代表修复后的测试已经通过。
- 未运行测试套件、构建、打包或发布；未推送或重跑远程 CI。
- 修复后的远程 CI 和 Win7 实机结果仍待验证。

## 后续记录模板

- 日期、CI 链接、被检查提交、失败 job/步骤：
- 最终报错及失败用例：
- 已确认根因（未确认则写“待确认”）：
- 修复方式与影响文件：
- 实际验证结果及未验证范围：
- 下次提交前的防复发检查项：

## 2026-11-17：历史考勤断言复用了旧报表列号

- CI：[44057831559](https://github.com/jace-wjc/hr-toolkit/actions/runs/44057831559)，提交 `97458b2b4663c9bf829eda4b0e73a5e30a592c89`。
- 失败 job：Python 3.12（`133951793706`）、Windows 7 兼容栈 Python 3.8（`133951793679`）；均在单元测试步骤的 `tests.test_run_coordinator` 失败。
- 最终报错：`test_attendance_history_reads_manual_edits_without_relaxing_other_inputs` 的历史余额断言得到 `None != 3`，模块结果 `Ran 15 tests; FAILED (failures=1)`。
- 已确认根因：七月与九月考勤报表的结转月份列不同，测试将七月报表的列号用于九月结果，实际读取了“漏打卡”。本地复现时，九月结果的“7月份加班天数”仍为人工修改后的 `3`，业务结转未丢失。
- 修复：在 `tests/test_run_coordinator.py` 中从本次结果重新解析列名；保留历史余额、原文件未修改、普通资料仍拒绝被篡改结果等断言，不改生产代码。
- 实际验证：本机 Python 3.13 上单独运行上述失败用例，修复前复现、修复后 `Ran 1 test; OK`。
- 未验证：修复后的远程 CI、Windows 和 Win7 实机；未执行全量测试、构建、打包或发布。CI 的 Win7 兼容栈运行在现代 Windows runner 上，不等同于 Win7 实机验收。
- 防复发：测试跨期报表时分别解析每份结果的动态表头，不沿用输入或旧月份的列索引。

## 2026-11-17：Python 3.9 的 OCR 版本模拟指向旧模块

- CI：[44057831559](https://github.com/jace-wjc/hr-toolkit/actions/runs/44057831559)，提交 `97458b2b4663c9bf829eda4b0e73a5e30a592c89`；失败 job：Python 3.9（`133951793618`），单元测试步骤。
- 最终报错：`tests.test_material_collector.TestOCRCacheHelpers.test_engine_signature_is_non_empty` 的 `modern=True` 分支得到 `rapidocr@unavailable`，期望 `rapidocr@3.9.2:ppocrv4-mobile:2`；模块结果 `Ran 113 tests; FAILED (failures=1, skipped=2)`。
- 已确认根因：测试先对 `sys.modules` 建立快照，再通过字符串补丁懒加载 `importlib.metadata`；第一次循环恢复快照后模块被移除，Python 3.9 的 `mock` 在第二次循环仍从父包属性找到旧模块，实际函数重新导入的模块没有被模拟。问题发生在测试补丁的生命周期，不是 OCR 包版本或安装错误。
- 修复：`tests/test_material_collector.py` 在快照之前导入元数据模块，使用对象补丁；继续在两个后端分支校验签名及版本查询次数，不修改生产代码或 OCR 依赖。
- 实际验证：临时隔离的 Python 3.9.25 环境中，原用例复现相同失败，修复后单独运行通过；本机 Python 3.13 同一用例也通过。临时环境未安装现代 OCR 包，因此通过结果不依赖本机恰好存在该包。
- 未验证：修复后的远程 CI、Windows 和 Win7 实机；未执行全量测试、构建、打包或发布。
- 防复发：混用 `patch.dict(sys.modules)` 与模块补丁时，先加载被模拟模块，再保存模块快照，并在项目支持的旧版 Python 上检查懒加载路径。

## 2026-11-17：Qt 6.6 年份输入的数字格式冲突

- CI：[44057831559](https://github.com/jace-wjc/hr-toolkit/actions/runs/44057831559)，提交 `97458b2b4663c9bf829eda4b0e73a5e30a592c89`；失败 job：Windows Python 3.12（`133951793714`），单元测试步骤。
- 最终报错：`tests.test_presentation.PresentationTests.test_real_ui_themes_languages_dialogs_and_persistence` 的 QML 告警断言失败，多次报告 `SpinBox.qml:27:18: QML QQuickTextInput: Binding loop detected for property "text"`。
- 已确认根因：`AppDateField.qml` 年份使用 `String/Number` 格式化和解析，但 SpinBox 默认整数校验器在英文和中文区域设置下将 `2026` 修正为 `2,026`；Qt 6.6 将修正结果回写显示文本时形成绑定循环。使用生产约束中的 `PySide6-Essentials==6.6.3.1` 已在本机复现相同告警；本机原有 Qt 6.11 不复现。
- 修复：仅将年份 SpinBox 的数字区域设置固定为 `C`，使校验器与现有格式一致；日期范围、语言显示和日期选择逻辑不变，不升级 Qt 或 Python，不使用 Qt 6 专用 API。
- 回归覆盖：新增 `tests/qt_date_field_probe.py`，由 `tests/test_presentation.py` 调用，在英文、中文区域设置下真实输入 `1`、`9999`、`2027`，检查边界增减、无分隔符、未选择日期时不修改原值，以及无 QML 告警。`scripts/ci_scope.py` 现有 `tests/qt_` 路由已覆盖 presentation 和 Win7 目标，无需改动。
- 实际验证：临时 Python 3.12.16 / Qt 6.6.3 环境中，原失败 UI 用例修复后通过；新年份输入用例在该环境及本机 Python 3.13 / Qt 6.11.2 均通过。新探针通过 Python 3.8 语法解析。
- 未验证：修复后的远程 Windows CI、Qt 5.15 / Win7 实机；未执行全量测试、构建、打包或发布。
- 防复发：自定义数字控件的文本转换时，同时核对校验器区域设置；QML 回归使用 CI 固定的生产 Qt 版本，不能以较新 Qt 的通过结果替代。
