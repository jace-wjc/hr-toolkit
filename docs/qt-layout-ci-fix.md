# Qt 布局循环与跨版本探针修复

2026-09-15，修复基线 `91c17ed`。对应失败运行：[34947845487](https://github.com/jace-wjc/hr-toolkit/actions/runs/34947845487)。

## 原因与修复

- Windows Qt 5 报主 ScrollView `contentHeight` 循环；Windows Qt 6 报 `materialOptionsColumn` 布局反复 polish。本机换用 Qt 6.6 后，还复现了 `uploadColumn`、`formColumn` 的同类警告。
- 主视口只领取标题下方剩余空间，显式清除由内容反推的隐式尺寸。滚动内容、上传卡片、表单及资料设置的纵向堆叠改用自然高度 Column，宽度从视口向下传递，高度按子项向上汇总；不再由父 ColumnLayout 一边分配尺寸、一边读取依赖这些尺寸的子布局高度。
- 保留横向 RowLayout、控件字体/颜色、各段间距、上传标题最小高度、资料说明缩进、侧栏宽度预算与动画、考勤表单的局部横向滚动。业务计算、文件处理、更新决策和下载逻辑未修改。
- 扩展历史更新弹窗场景后，Qt 5 复现了关闭弹窗后缩放时的高度循环。其首选高度现由摘要与更新说明的自然高度计算；说明视口只使用扣除页脚后的正文空间，与更新提示弹窗保持相同原则。

## 探针修正与覆盖

- 保留已有 Qt 5/6 事件循环等待与对应 Controls 样式，不屏蔽 QML 警告。逐场景记录新增警告，全部场景结束后统一失败，避免第一条警告掩盖其他同类问题。
- 保留遍历到的可视父子对象引用，避免 PySide2 临时父包装对象回收时使已有子对象包装失效；父链遍历止于中间面板。
- Qt 5/macOS/software 的窗口截图为空时，使用同一内容项的异步截图接口；仍要求获得非空图像，设置 2 秒等待上限，不跳过截图检查。
- 显式设置阈值测试的初始窗口尺寸与侧栏固定状态。Qt 5 在 150% 缩放下实际曾将初始 1400×820 调整为 933×547，触发应用原有的小窗口侧栏收起规则；测试不再依赖这个平台初始化结果。
- 检查动画期间分配宽度、收起/恢复阈值、手动收起保持、Escape、9 个工具在不同宽度下的控件边界、纵向卡片不重叠及滚动范围。
- 检查无更新、短说明、长说明、必要更新无说明、手动下载加必要更新，以及长历史说明；覆盖 760×600、760×820、1400×820 和弹窗关闭后继续缩放。
- 检查资料打包的按人员文件夹/平铺 OCR 模式、全部/指定材料设置，在 760px 与 1400px 间切换。

## 本机验证

使用隔离环境；没有打开用户项目或执行实际业务处理。

| 环境 | 范围 | 结果 |
| --- | --- | --- |
| macOS x86_64 / Python 3.9.6 / PySide2 5.15.2.1（Qt 5.15.2） | 本次 CI 选择的五个相关测试模块，110 项 | 通过 |
| macOS arm64 / Python 3.12.14 / PySide6 Essentials 6.6.3.1（Qt 6.6.3） | 同上，110 项 | 通过 |
| macOS arm64 / Python 3.13.13 / PySide6 6.11.2 | Qt 入口、控制器、表单规格三个模块，101 项 | 通过 |
| Qt 5.15.2、Qt 6.6.3 / 150% 缩放 | 完整布局探针 | 均通过 |

前两组五个模块为 `tests.test_qt_entrypoint`、`tests.test_qt_controller`、`tests.test_qt_form_specs`、`tests.test_material_collector_gui`、`tests.test_project_creation_gui`。Qt 6.11 运行前三个模块。QML 由实际加载与交互探针检查，所有捕获的 QML 警告仍导致失败。

原始本机日志：`/tmp/hr-ci-verified-qt515.log`、`/tmp/hr-ci-verified-qt66.log`、`/tmp/hr-ci-verified-qt611.log`；高 DPI 探针日志为 `/tmp/hr-ci-scale-qt515-pinned.log`、`/tmp/hr-ci-scale-qt66.log`。临时日志可能被系统清理。

验证边界：上述均为 macOS 本机检查，不能代替 Windows 原生平台或 Python 3.8 运行验证；未运行全仓测试、全量构建、安装包、发布或远程 CI。没有声称后续 CI 必然不会失败。

## 0.9.8 发布中的日志行循环补修

失败运行：[Release 34951052536](https://github.com/jace-wjc/hr-toolkit/actions/runs/34951052536)，提交 `8be3aa8`。Win10/11 EXE 任务通过；Win7 任务在 `Run Python 3.8-compatible core tests` 阶段失败，尚未进入安装包生成。332 项测试中唯一失败的是工作区布局探针：`data_statistics`、1400×820，`Main.qml:1311` 的日志行 RowLayout 报 `height` 绑定循环。此前普通 CI 通过并未覆盖这次 Windows 发布运行触发的警告。

### 修复范围

- 日志行原先一边让 RowLayout 分配文字宽度，一边以文字换行后的隐式高度绑定 RowLayout 自身高度。这条尺寸反馈路径在前一轮外层布局修复中遗漏。
- 日志行改为普通 Item：列表宽度决定行宽，圆点和时间的自然宽度决定正文起点，正文换行高度决定行高。消除布局容器参与的高度回算；不修改日志内容、跟尾、虚拟列表复用、颜色字体和选择复制菜单。
- 维持原来的 7px 间距、最小行高 25px、正文上下共 4px 留白，以及布局原有的整数尺寸取整。Qt 5 对照短日志、中文长日志、显式换行在 760/1400/1600px 下的 9 个样本，修复前后行高及各文字项坐标、宽高一致。
- 原探针新增 120 条混合日志、连续缩放、列表首尾切换、模型重置和追加、只读与选择检查；继续将所有 QML 警告判为失败。
- Qt 6.11 的复用池对象可能仍保留 `visible=True` 和旧坐标；探针按 `ListView.itemAtIndex()` 获取当前有效行，检查有效行宽度、换行高度、边界和互不重叠，避免把未参与当前布局的池中对象算进去。

### 补修验证结果

- Qt 5.15.2 / Python 3.9.6、Qt 6.6.3 / Python 3.12.14、Qt 6.11.2 / Python 3.13.13：分别运行 `tests.test_qt_entrypoint` 的 36 项相关检查，均通过；包含上述新增日志场景，耗时分别约 21.4/19.9/20.2 秒，未提高原探针的 45 秒超时。
- 修改的 Python 探针通过语法编译；`git diff --check` 通过。
- 结果日志：`/tmp/hr-log-fix-entry-qt515.log`、`/tmp/hr-log-fix-entry-qt66.log`、`/tmp/hr-log-fix-entry-qt611.log`；几何对照：`/tmp/hr-log-row-before.json`、`/tmp/hr-log-row-after-rounded.json`。
- 原始循环的直接证据来自 Windows 发布日志；本机短样本未复现该警告。以上验证均在 macOS 完成，不能据此声称 Windows 原生或 Win7 安装包已通过。未运行全仓测试、全量构建、打包或远程重跑；发布任务仍需在包含本修复的提交上复验。

## 0.9.10 发布中的头部行布局循环

失败运行：[CI 35338983577](https://github.com/jace-wjc/hr-toolkit/actions/runs/35338983577)、[Release 35338983656](https://github.com/jace-wjc/hr-toolkit/actions/runs/35338983656)，提交 `a2253ed`（发布 0.9.10）。两个运行的 Windows 车道都只失败在 `test_workspace_panel_allocates_width_and_restores_after_narrow_resize`：探针在 `material_collector`、1400×820 报 `Main.qml:614` 的 `ColumnLayout`（`id="mainLayout"`，几何 484×758）布局 polish 循环。Win7（Qt 5.15.2）车道当次未报。

### 原因

- 前一轮 CI 绿灯没有覆盖这次运行：`476c59c`、`8e68150` 只改了 `tests/test_qt_controller.py`、`tests/test_qt_entrypoint.py`，`ci_scope` 没有选中 `test_qt_entrypoint`。发布提交改动版本号与发布说明后范围扩大，探针才执行。
- 触发点在 `03bb229` 新增的「地区编号维护」按钮：它的 `visible` 跟随当前工具（`archive_import`、`personnel_change_merge`），切到其它工具时该按钮进出头部 RowLayout。
- 头部标题块当时是嵌套 `ColumnLayout`。按钮进出改变了分配给标题块的宽度，标题与说明文字随之换行（2 行 ↔ 1 行）；嵌套布局在外层 `mainLayout` 正在分配尺寸时又写回 `Layout.*` 提示，Qt 的「最多两次迭代」保护（`QQuickLayout::invalidate()` 的 `m_polishInsideUpdatePolish`）被第三次重入打断并告警。
- 本机对照：移除按钮、把按钮固定为常显、或把按钮换成固定尺寸的普通 Item 后现象有变化，说明是「跟随工具的可见性切换」与「嵌套布局在 polish 期间回写尺寸提示」共同作用，而不是按钮宽度本身。

### 修复范围

- 头部标题块由嵌套 `ColumnLayout` 改为普通 `Column`：宽度由 RowLayout 自上而下分配，三个文字项用 `width: parent.width` 取用，换行高度自然向上汇总，不再有布局容器在外层布局分配尺寸期间回写提示。
- 未改动按钮的可见性条件、文案、间距、字号与行内顺序；其余布局结构保持原样。

### 验证结果（macOS 本机）

- 环境：PySide6 6.6.3.1（Qt 6.6.3），与失败车道安装的 `requirements-gui.txt` 版本一致。
- 工作区探针（告警一律判失败的原始断言）：修复前 3 次运行中 2 次报该循环；修复后 7 次运行 0 次。
- 逐像素对照：修复前、修复后各跑一次完整探针并对比全部截图，确定性页面 25/28 完全一致；`salary_split` 三张的差异只有 26〜72 个像素，且同一份代码连跑 9 次该文件哈希每次不同，属该页面的固有渲染抖动，与本改动无关。`geometry.json` 中窗口宽度、中间面板与右侧面板宽度在静止场景一致，差异只出现在面板动画帧。
- `tests.test_qt_entrypoint` 37 项在修复后通过（单次运行耗时约 84〜91 秒）。

### 未处理与验证边界

- 本机为 macOS，未验证 Windows 原生与 Qt 5.15.2（Win7 车道），验收仍依赖重跑发布工作流。
- 本机偶发另一个告警：`formScroll.contentWidth` 绑定循环（`minimumFormWidth` 读 `attendanceOptions.implicitWidth`，经 `formColumn.width` 回到 `contentWidth`）。该路径来自 `9030cfc`，随 0.9.9 发布，本次未改动；4 次本机运行中 1 次出现，且目前所有 Windows 车道日志中都没有出现过，故未纳入本次修复。
