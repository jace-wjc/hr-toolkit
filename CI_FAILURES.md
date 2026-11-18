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

## 2026-11-17：UI 探针失败后未释放项目文件锁

- CI：[44057831559](https://github.com/jace-wjc/hr-toolkit/actions/runs/44057831559)，提交 `97458b2b4663c9bf829eda4b0e73a5e30a592c89`；失败 job：Windows Python 3.12（`133951793714`），与上条 UI 用例相同。
- 最终异常链：先因 QML 告警抛出 `AssertionError`，再在 `TemporaryDirectory` 清理时抛出 `PermissionError: [WinError 32]`，文件为临时项目的 `.hrtoolkit/project-write.lock`。
- 已确认根因：`tests/qt_presentation_probe.py` 只在全部断言成功后显式关闭控制器和项目；失败路径先退出临时目录上下文，项目仍持有 Windows 文件锁。该清理异常掩盖了原始失败，不是应用项目锁失效。
- 修复：使用 `ExitStack` 注册控制器和 QML 引擎的清理，在移除临时目录之前、控制器仍存活时销毁 QML，再关闭控制器释放锁；恢复设置用的第二个控制器也在失败时清理。保留成功路径上的设置持久化检查。
- 实际验证：临时 Python 3.12 / Qt 6.6 的原 UI 用例通过；本机 Python 3.13 / Qt 6.11 中在项目创建后注入断言失败，确认原始断言保留、`ProjectStore.close()` 被调用、临时项目目录移除；探针通过 Python 3.8 语法解析。
- 未验证：Windows 文件锁的修复后实际执行结果和 Win7 实机；未执行全量测试、构建、打包或发布。
- 防复发：GUI 探针创建项目、控制器或 QML 引擎后立即注册清理，不能把资源释放仅放在最终成功断言之后。

## 2026-11-17：本地启动回归——窗口颜色回调依赖具体包装类

- 来源：用户本地执行 `python -m hr_toolkit` 的日志，并非已定位到某次 CI run 的失败；用户未提供提交号。本地在 `e1d32af` 基线上复现。
- 报错：`gui_qt/main.py` 的 `refresh_resize_backdrop` 调用 `root_window.color()`，抛出 `AttributeError: 'PySide6.QtGui.QWindow' object has no attribute 'color'`。
- 根因：未预先导入 QtQuick Python 绑定的启动路径将 QML 根窗口包装成 `QWindow`；窗口的 `colorChanged` 信号仍存在，但 Python 包装类没有 `QQuickWindow.color()` 方法。原探针预先导入 QtQuick，或未切换主题，因此未覆盖该回调。
- 修复：直接使用 `colorChanged` 信号传入的 `QColor`；Qt 5.15 和 Qt 6 均使用此信号签名，不增加依赖、强制类型转换或全局异常屏蔽。
- 回归：新增 `tests/qt_resize_backdrop_probe.py`，不预加载 QtQuick，调用生产启动入口并切换深浅主题，检查背景色传递、旧背景资源释放及退出清理；同时捕获 Qt 回调异常，避免进程仍退出 0 时漏报。
- 实际验证：该探针修复前复现用户同一异常，修复后通过；非 Windows 与 headless 平台的两个相关用例也通过，共 3 项。修改的 Python 文件通过 Python 3.8 语法解析。
- 未验证：用户另一台 Mac 的具体环境、修复后的远程 CI、真实 Windows GDI 和 Win7 实机；未执行全量测试、构建、打包或发布。
- 防复发：验证 Qt 启动时保留生产导入顺序并实际触发信号；不能只凭窗口出现或进程退出 0 判断回调无异常。

## 2026-11-17：本地交互回归——下拉框使用隐式信号参数

- 来源：用户本地 Qt 日志；不是新增远程 CI 失败，用户提交号未提供。本地可复现主题、语言和考勤选项三个处理函数的警告。
- 报错：`Parameter "index" is not declared. Injection of parameters into signal handlers is deprecated.`，对应 `AppearanceDialog.qml` 两处及 `AttendanceChoiceField.qml` 一处 `onActivated`。
- 根因：处理函数直接使用隐式注入的 `index`；只创建控件或直接调用 Python 的主题/语言设置不会触发该警告，必须执行 ComboBox 的 `activated(index)` 信号。
- 修复：三个处理函数均改为 `function(index) { ... }`，保留原来的模型索引、主题/语言值及公司/地点原始值；语法沿用项目 Qt 5.15/Qt 6 共用的显式信号参数写法。
- 回归：新增 `tests/qt_choice_activation_probe.py`，激活生产外观与考勤控件，检查深浅主题、两种语言和“公司默认”/“杭州”的原值，并将参数弃用警告列为失败条件。
- 实际验证：本机 Python 3.13 / Qt 6.11.2 中，修复前用例捕获三个相同警告并失败，修复后通过；修改的 Python 文件通过 Python 3.8 语法解析，现有路由覆盖 presentation 和 Win7 兼容栈。
- 未验证：用户另一台 Mac、修复后的远程 CI、Qt 5.15 / Win7 实机；未执行全量测试、构建、打包或发布。
- 防复发：涉及信号参数的 UI 测试需实际触发控件信号，并检查标准错误中的 Qt 告警，不能仅检查后端字段值。

## 2026-11-17：Win7 兼容栈控制器测试进程退出时访问冲突

- CI：[44092177073](https://github.com/jace-wjc/hr-toolkit/actions/runs/44092177073)，提交 `9424eaffb9f314f8362c8e3a05944ae99fcf9eb9`，首次失败 job：Windows 7 compatibility stack on Python 3.8（`134070004923`）。
- 最终错误：`tests.test_qt_controller` 输出 `Ran 109 tests; OK` 后，出现 `Windows fatal exception: access violation`、`<no Python frame>`，进程退出码 `3221225477`（`0xC0000005`）。测试执行器正确将非零退出判为失败；后续模块没有继续执行。
- 运行边界：依赖安装及 Qt 启动检查已通过；Python 3.9、Python 3.12 和现代 Windows Python 3.12 job 均通过。失败模块在上一轮成功提交 `e1d32af` 后未改动。
- 已确认的清理缺陷：目录记忆持久化测试直接创建两个 `AppController`，绕过统一测试工厂；结束时只执行业务 `close()`，没有销毁 Qt 对象树。跟踪确认恢复设置的控制器仍持有两个已安装的翻译器，资源存活到解释器退出阶段。
- 原生崩溃的最终归因仍待确认：日志没有原生调用栈，本机旧版 Qt 环境也未复现该访问冲突；不能仅凭资源遗留认定它是此次崩溃的唯一原因。
- 修复范围：仅修改 `tests/test_qt_controller.py` 的该用例，用 `ExitStack` 在临时设置和 `QCoreApplication` 仍存活时关闭并销毁两个控制器，正常和异常退出均清理；保留保存/恢复目录断言，新增两对象均已销毁的断言。生产代码、Win7 依赖、退出码判定及测试名单均未修改。
- 实际验证：macOS 上临时 Python 3.8.20 x86_64 / PySide2 5.15.2.1 与本机 Python 3.13 / PySide6 6.11.2 各执行该模块 109 项，均通过且进程正常退出；Qt 5 中注入启动后异常，确认原始错误保留且两棵控制器对象树均销毁；Python 3.8 语法检查通过。
- 远程复验：只重跑原失败 job 后，第 2 次执行（job `134075275176`）成功，原提交 `9424eaf` 的整个 CI 已恢复通过。这说明首次退出崩溃具有偶发性；重跑不包含本次尚未推送的清理修改，不能据此宣称该修改已通过远程验证。
- 未验证：清理修改后的远程 Windows 结果及 Win7 实机；未执行全仓测试、构建、打包或发布。
- 防复发：直接创建 Qt 控制器的测试必须管理其原生对象生命周期；保留对子进程真实退出码的检查，不能以断言全通过、强制退出 0 或忽略访问冲突代替正常清理。

## 2026-11-17：本地发布校验失败，Sage 保存时遍历空附件

- 来源：用户提供的 macOS 本地发布校验日志，执行 `python -m unittest discover -s tests -v`。共 1349 项，1 项失败、3 项跳过，发布脚本报告本地状态已回滚。用户未提供当次提交号，本地在 `a63d51b` 核对了相同调用链。
- 失败用例：`test_ai_assistant_panel_and_popups_instantiate_without_layout_loops`。Sage 探针结束回复时进入 `ConversationStore.save()`，写入历史后收集图片引用，抛出 `TypeError: 'NoneType' object is not iterable`。后面的 QML 空对象提示出现在探针异常退出时。
- 已确认根因：Qt 探针构造的消息可以省略附件字段，消息模型用 `None` 补齐。`4b1cc65` 新增的图片引用收集用 `get("attachments", [])` 取值，该默认值只处理字段缺失，不能处理字段值为 `None`。用于图片清理的 `retained_image_paths()` 存在同样的问题。
- 修复：`hr_toolkit/ai/history.py` 的两处引用收集将空附件按空序列处理。`tests/test_ai_assistant.py` 的历史用例补入一条无附件回复，与带图消息一起保存，覆盖重新读取、图片引用保留和删除失败回滚。
- 实际验证：两个修改的 Python 文件通过 Python 3.8 语法解析及本机 Python 3.13 字节码编译，`git diff --check` 通过。原 Qt 用例和完整发布校验待复验。
- 防复发：新增历史字段消费者时，核对 Qt 模型生成的 `None` 与旧数据中的字段缺失，并用带附件和无附件消息混合验证保存、读取与图片引用。

## 2026-11-17：Win7 兼容栈控制器测试在清理阶段卡住

- CI：[44101355386](https://github.com/jace-wjc/hr-toolkit/actions/runs/44101355386)，提交 `4d40127ec3dee0b737454b98f83a8594eaae83ca`，失败 job 为 Windows 7 compatibility stack on Python 3.8（`134101987366`）。Python 3.9、Python 3.12 和现代 Windows 检查均通过。
- 最终结果：`tests.test_ai_assistant` 的 113 项已通过。控制器模块停在 `test_ai_edit_and_regenerate_keep_history_when_saved_attachments_are_not_for_this_service`，每 60 秒输出相同线程栈，300 秒后出现 `TIMEOUT: tests.test_qt_controller; stopping its process tree` 并退出 1，后续 Qt 入口模块未执行。
- 堆栈定位：核对 CPython 3.8.10 源码，主线程 `unittest/case.py:681` 对应 `self.doCleanups()`，后台线程 `threading.py:874` 对应释放 `_target`、`_args` 和 `_kwargs`。后台工作函数已经返回，卡点位于测试与线程释放引用的阶段。
- 已确认缺陷：前面的附件准备和连接测试只等待模拟函数内部的 `Event`，没有等待真实线程退出。事件发生后线程仍要发出 Qt 信号并释放闭包中的控制器引用，可能与后续测试清理同时发生。`controller.close()` 只执行关闭操作，不能证明这些线程已结束。
- 归因边界：现有 Python 堆栈未包含原生 Qt/PySide 锁的调用栈，不能据此确认具体锁或认定这是唯一原因。此次修复消除上述可确认的线程收尾缺口，Win7 结果需在修复后复验。
- 修复范围：仅调整 `tests/test_qt_controller.py` 的上述两个异步用例。记录实际启动的线程，在控制器仍被主线程持有、模拟接口和临时目录仍有效时等待退出，单线程等待上限 5 秒，仍存活则明确失败。附件用例在断言失败时也释放等待事件。原异步执行、取消及设置断言继续保留。
- 实际验证：经用户当次授权，在本机 Python 3.13.0 / PySide6 6.11.2 下依次运行附件准备、关闭时取消展示更新、连接测试、跨服务附件编辑与重试四个相关用例，4 项通过，结束后没有遗留 AI 工作线程。在两个异步用例中分别注入断言失败，均保留原始失败并确认线程已经等待退出。配置路径使用临时目录。
- 语法与范围检查：修改文件通过 Python 3.8 语法解析和 Python 3.13 字节码编译，差异检查通过。Win7 / Qt 5、修复后的远程 CI 及完整模块尚未复验。
- 防复发：后台函数中的“进入”或“收到结果”事件不代表线程已完全结束。测试释放 Qt 控制器或退出临时目录前，必须等待自己启动的真实线程退出，失败路径同样执行，并保留明确的超时失败。

## 2026-11-18 英文教程的实际目录名被误判为漏译

- 提交 `8f0bba1b2b42b91da03904663c6913a845db195a` 的第 1 次 CI 运行中，Windows Python 3.12（`134530374701`）和 Windows 7 兼容栈 Python 3.8（`134530374700`）均在单元测试步骤失败。 [CI 44223315496](https://github.com/jace-wjc/hr-toolkit/actions/runs/44223315496)
- 最终失败用例为 `tests.test_presentation.PresentationTests.test_real_ui_themes_languages_dialogs_and_persistence`。`tests/qt_presentation_probe.py:155` 对 `helpDialog` 调用 `english_complete`，第 102 行因英文段落中的 `the batch's 处理结果 folder` 触发 `AssertionError`。两项任务均报告 `FAILED (failures=1)`，退出码为 1。
- 教程提交 `63c5be4` 在英文批量改名指南中引用了磁盘上的实际目录名「处理结果」。项目存储通过 `CATEGORY_VISIBLE_NAMES[CATEGORY_RESULTS]` 定义该名称。原探针只识别了地区名称等已有例外，把这处目录名当成了未翻译文案。
- 修复位于 `tests/qt_presentation_probe.py`。明确打开批量改名教程，从项目存储取得结果目录名，要求英文教程确实显示该名称，只在本处允许「目录名 + folder」这一短语，其余中文残留仍会使断言失败。生产教程和项目存储沿用原实现。
- 本地通过 Python 3.8 语法解析、Python 3.12.14 内存编译和差异检查。原 UI 探针、修复后的远程 CI 和 Win7 实机待复验。
- 更新英文教程时，按测试场景检查真实目录名、文件名和工作表名。只允许该场景确实需要的原样名称，保留对其他文案的翻译检查。
