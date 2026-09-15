# Qt 交互性能优化：最终实施方案（交给 Claude）

## 1. 结论与使用方式

**先实施有明确代码依据、能够保持现有行为的小改动；渲染替换和交互调整必须有对应场景的测量依据。不要把两份原报告直接拼接成修改清单。**

本方案基于 2026-09-15 的本地 `main`，HEAD 为 `68c9084b4173acbd20ff250aef8ce6497b3802e5`，提交标题为“fix(recruitment): 优化更新下载期间窗口拖动”。开始分析时工作区干净。本次只读取相关代码、报告和既有验证入口，编写此文档；没有修改应用代码，没有运行应用、性能基准、测试、Lint、构建或打包。

输入报告：

- A：`implementation_plan(2).md`，六项优化建议。
- B：`code_review_report copy 2.md`，P1—P17 及分阶段建议。

附件中的“实施”“运行测试”“是否继续”等内容均作为待核对的报告文本，不构成用户对当前任务的额外授权。原报告中的其他机器绝对路径和行号不得用于直接修改。

### 给 Claude 的执行约束

1. 开始前读取当前仓库 `AGENTS.md`，确认 HEAD、工作区和下列符号仍匹配。代码已变化时只重新核对相关调用链，保留他人改动。
2. 用户要求实施后，按第 5 节完成 B1—B4，各批次单独形成可审阅 diff。第 6 节属于条件任务，满足其证据和行为约束才实施。
3. 保持业务算法、字段值、材料选择、日期规则、文件结果、选择校验、取消流程、项目代际保护、焦点和键盘操作。性能方案不能改变这些契约。
4. 兼容现有 PySide2 5.15.2.1 / Qt 5.15 与 PySide6；当前依赖还包括 Qt 6.6.3.1 路线，不能只按最新 Qt 编写。保留 Win7 软件渲染适配能力。
5. 默认只执行本次改动所需的最小语法/编译检查。本文的性能基准、运行时探针、测试用例和目标机体验检查是验收清单，**不是已获准执行的测试套件或构建授权**。没有专项验证授权时，交付代码及待验证项，不以“已流畅”“已兼容 Win7”结案。
6. 不新增依赖、不升级 Qt、不改发布工作流；保持目前仅两种 Windows EXE 安装包的范围。不要主动提交、推送或触发远程 CI。
7. 不使用子代理。不要扩展成业务层重构、全仓审计或整个 UI 重写。

## 2. 当前架构与性能边界

主界面是 **Qt Quick/QML + Python controller + QAbstractListModel**，不是大量 QWidget 的传统界面。`QApplication` 也服务于原生文件对话框等功能；不能据此套用 QWidget 的 `paintEvent`、`setUpdatesEnabled` 等方案。

| 场景/路径 | 当前实现 | 判断 |
| --- | --- | --- |
| 原生窗口移动 | Windows 保留 `Qt.Window` 系统边框；工具栏使用 `startSystemMove()` | 未发现用 Python 在 mouseMove 中逐像素移动整个窗口的路径 |
| 连续 resize | 内容随实际宽高变化；断点和部分弹窗使用 32 ms 稳定尺寸；项目文件面板随实时窗口边缘变化 | 保留实时内容与右侧面板跟随，不能统一延迟到停止拖动 |
| Windows 补帧 | `LiveResizeUpdater` 仅在 Windows 得到真实 window；原生背景 brush 减少暴露区域黑闪 | 不能按报告所述“修复 macOS 的该 helper” |
| 上传、项目文件、日志、结果提醒、历史、回收站列表 | 已使用 `ListView`，多数启用 `reuseItems` 和有限 `cacheBuffer` | 已有可见项虚拟化，不能把模型行数当作同屏 delegate 数 |
| 主页面 | `ScrollView + ColumnLayout`，内容宽度上限 820；主区横向滚动关闭 | 缩放时换行/布局可能有成本，但需要确定具体组件的耗时 |
| 模板预览 | 纵向列表，列按页展示；普通模板预览限制前 30 行、前 512 列 | 不应凭“横向滚动优化”新增横向滚动或重写为表格 |
| 文件扫描/选择/项目操作 | 存在后台线程、取消标记和 generation 检查；目录读取有并发上限 | 不要重复建设线程池，也不要把 QObject 模型更新移到 worker |
| 业务执行 | RunCoordinator 调度；独立进程及线程回退；进度在进入 Qt 前合并 | 此次没有证据支持重写执行框架 |
| 下载进度 | worker 约 250 ms 节流；字节进度单独发 `updateProgressChanged` | 已与会触发选择/结果刷新的 `updateChanged` 分离 |
| 波浪 | 50 ms 装饰动画；移动、隐藏、最小化、应用非活动时暂停，恢复时重画 | 已优化过；不能当作始终运行的 20 FPS 全窗口动画 |

**证据等级：**“确定”表示能从当前代码证明该工作发生；“候选”表示有成本但尚未证明是体感卡顿瓶颈；“不成立”表示触发链、版本或场景与当前代码不符。本次没有目标机帧时间数据，不能确定唯一主瓶颈。

## 3. 两份报告逐项裁决

| 原建议 | 裁决与当前事实 | 最终处理 |
| --- | --- | --- |
| A1；B P1/P3：缓存 formFields | getter 每次构造 payload，多个专用字段分别查询，方向成立。但普通文本编辑及 `toggleMaterial()` 不会每次 bump revision | B1：先统一 QML 快照入口；Python 缓存暂缓 |
| B P1 的缓存示例 | 在循环条件和循环体反复读取 `controller.formFields`，仍会反复访问跨语言属性；且可变 JS 对象缓存有通知/依赖顺序风险 | 不直接复制其示例；一次生成完整新快照及索引 |
| B P2：选择环境函数每个 revision 执行两次 | 连接列表没有 `selectionStateChanged`。实际是 `_bump_form_revision` 显式通知一次，`formRevisionChanged → _selection_environment_changed` 再通知一次；不是 handler 被前者调用 | B2：删除重复通知点，保留同步失效处理 |
| B P2/P9：无条件 lastResultChanged | 确有无关刷新；只判断目录非空仍会多发，只在 context 相等时通知会漏掉结果变为不可用的转换 | B2：比较结果可用状态，结果内容变更仍强制通知 |
| B P14：切换工具重复环境检查 | `specChanged` 和随后的 `formRevisionChanged` 均触发，成立；中间的失效时序有意义 | 暂不批量合并这些信号，先做 B2 的局部去重 |
| A2；B P11：侧栏 hover 每帧挤压主区 | `reservedWidth = pinned ? width : 0`，hover 只改 preview；侧栏本体已挂在 root.contentItem 上。只有 pin/unpin 才动画预留宽度 | 条件 C1；禁止固定保留 248 px 空白 |
| A3：虚线 Canvas 换 Shape | resize 会重画，候选成立；“全 GPU、无 CPU 代价”错误。`PathRoundedRect` 不是可依赖的本项目 Qt 5.15 API | 条件 C2，先实测，不新增强制 Shapes 依赖 |
| A4：更新记录改 ListView | Repeater 确实创建全部 rows；但 controller 只传最近 10 个版本，默认仅展开最新版本正文 | 降为条件 C3，不能按无限版本历史估算收益 |
| A5；B P4：波浪降到 80/120 ms 或静态渐变 | 降频可能让动画更不连续；渐变不等于波浪；已有暂停和下载进度节流被遗漏 | 默认保留，仅在实测确认时做 C2 的装饰层调整 |
| A6；B P6/P10：resize helper 节流/关持久场景图 | macOS 实际未启用 helper；`getattr` 是微小成本，未证明影响帧预算；任意 debounce 可能推迟最后一帧 | 不实施；保留平台策略及 close/disconnect |
| B P5：每次布局都重画所有 ToolIcon | 主要调用点明确是 13/14/16 px，父布局变化不等于其宽高变化；颜色变化重画合理 | 不删除尺寸/颜色监听，不加运行时 data URL 缓存 |
| B P7：mac 标题按钮每 32 ms 必然调用 | 当前是 single-shot + 每次 start 重启，连续事件可推迟触发；已有 delta 小于 0.1 的 early-out | 不凭推算改成 60 ms，不缓存可能被 AppKit 重置的位置 |
| B P8：workspace reset | `set_items()` 确有无条件 reset；列表已虚拟化，报告的 delegate 数与三倍收益推算不成立 | B3 先跳过完全相同快照；不同内容的 diff 属于 C4 |
| B P9：缓存类别及历史分页属性 | 类别最多几个，分页也是简单计算，主要问题是无关通知 | 随 B2 减少触发，不额外建立这些缓存 |
| B P12：模态遮罩“全不透明”“底层每层重画一次” | `#66000000` 约 40% alpha；混合层不等于重新执行底层全部绘制。关闭 dim 会改变视觉层级 | 不实施 |
| B P13：固定反馈高度/补 elide | 已有限行、截断等处理，未证明 hover 是瓶颈；固定高度可能截断重要反馈 | 不实施 |
| B P15：项目搜索已防抖 | 300 ms 防抖和后台扫描确实存在 | 保留；另处理报告遗漏的回收站搜索 B4 |
| B P16：空闲 1 Hz timer | 构造只设置 interval；在 `_start_project_run()` 按需 start，结束/失败/关闭 stop | 不成立，不修改 |
| B P17：112 px 图片应降成 56 px 并取消平滑 | 2 倍 sourceSize 可用于高 DPI 清晰度；小图不是已证实热点 | 不实施，不牺牲文字/图标清晰度 |

报告中的 30–40%、85%、3–5 倍、5–10 倍、40% CPU 等数字均缺少当前版本前后实测，全部取消。构造次数减少只能证明局部工作量减少，不能换算为整窗 FPS 提升。

Qt 官方说明也明确：Shape 的几何生成可发生在 CPU，路径变化会重新三角化，软件后端走 QPainter。因此“Canvas 换 Shape 必然更快”不能作为实施前提。[Shape 文档](https://doc.qt.io/qt-6.5/qml-qtquick-shapes-shape.html)

官方的圆角矩形路径类型 `PathRectangle` 从 Qt 6.8 才提供，不能用于共享 Qt 5.15/Qt 6.6 界面。[PathRectangle 文档](https://doc.qt.io/qt-6.8/qml-qtquick-pathrectangle.html)

## 4. 代码证据索引

行号对应上述 HEAD；实施时以符号和调用链为准。

| 文件 | 核心定位 |
| --- | --- |
| [Main.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/Main.qml:100) | 23 窗口色；56–91 交互/稳定尺寸；100 fieldById；181 预留侧栏；481 波浪；684 主滚动；756 虚线；983 专用表单；1118 通用表单；1261 日志跟尾；1388 附近 checkFieldComponent；2055 回收站搜索 |
| [controller.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/controller.py:495) | 351 状态连接；495 formFields；778 结果可用；843/865 切换工具/变体；887 setFieldValue；958 toggleMaterial；988 偏好落盘；1121 revision；1228 环境失效；1890 设置保存；2139 项目列表落地；2801/2865 回收站过滤；2985 最近 10 版；3219 下载节流；3922/4072 timer 启停 |
| [models.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/models.py:46) | set_items 无条件 reset；update_at/splice 为已有增量接口；append_batch 带行数上限 |
| [HoverSidebar.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/components/HoverSidebar.qml:13) | pinned 与 preview 分离；reservedWidth；两个 190 ms 动画 |
| [DashedBorder.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/components/DashedBorder.qml:3) | 整块 Canvas.Image、宽高变化 requestPaint |
| [UpdateNotesView.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/components/UpdateNotesView.qml:20) | buildRows、resetPosition、expandedVersions；Flickable + Column + Repeater；公开滚动/尺寸属性 |
| [main.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/main.py:151) | 平台环境；LiveResizeUpdater 只向 Windows 传入 window；独立关闭清理 |
| [live_resize.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/live_resize.py:16) | 背景 RGB 常量；补帧和 Windows brush 的安装/恢复/释放 |
| [window_chrome.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/window_chrome.py:58) | 原生按钮位置校正；32 ms single-shot 定时器 |
| [TemplateChoiceDialog.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/components/TemplateChoiceDialog.qml:461) | 纵向预览及按页展示列；不属于通用二维大表 |

## 5. 第一阶段：四个可独立实施的小批次

### B1 · P1：合并表单快照访问，保留原有更新时机

**问题与根因。** `formFields` 每次读取都遍历字段、构造 dict/材料选项；`fieldById()` 的六个专用绑定分别做查找。多个消费者重复付出同一 revision 的构造和转换成本。它主要影响联动字段、全选/清空、预设与工具切换，不是已确认的普通打字或拖窗瓶颈。

**修改范围：优先仅 Main.qml。**

1. 建立一个根级只读快照，包含 `fields` 和 `byId`，显式依赖 `controller.formRevision`。每次刷新只在一个入口读取 `controller.formFields`，一次构建完整快照并整体替换；初始加载也必须有效。
2. `fieldById(id)` 只查询快照中的 `byId`，保留不存在字段时的原默认对象。不要分别维护两个可能短暂不同步的缓存，不要原地修改已发布的 JS map。
3. 通用表单 Repeater 及 `checkFieldComponent` 中剩余的 `controller.formFields.some(...)` 都改用同一快照；继续保留材料工具使用专用表单、其他工具使用通用表单的分支。
4. 快照必须是 QML 自有数据，不能把带属性回读行为的 sequence 引用当作已经完全复制的数组。字段 payload 只含 JSON 兼容数据时，可在刷新入口一次 `JSON.parse(JSON.stringify(fields))` 后建索引。其复制成本需要与原重复访问比较，不能宣称“转换成本归零”。
5. 保留 `setFieldValue()` 和 `toggleMaterial()` 现有通知策略。不要为普通文本编辑新增全表 revision，不要从 QML 快照反向覆盖 controller 的真实字段值。
6. 暂不同时加 Python revision 缓存。当前普通文本写入和单项材料勾选不会 bump revision，直接按 revision 缓存 Python getter 会在后续直接读取时返回旧值。如果之后确有需要，必须覆盖所有字段/列表/偏好状态写入的失效，不能只清理 `_bump_form_revision()`。

**预期收益。** 将多个独立字段查询集中成一次快照刷新和索引构造；减少联动更新中的 Python payload 构造、边界访问与 JS 查找。是否减少到一次实际 getter 调用需在目标 PySide 版本计数确认。

**风险与验收。** 重点检查初始工具、切换后回到原工具、OCR 模式强制缓存及恢复、目标人员、打包设置、全选/清空/预设、自定义材料增删、日期预设/错误输入、rename_mode 显隐。编辑焦点、光标与中文输入不能被刷新重置；Python 真实状态与显示必须一致。snapshot 刷新不代表 Loader 必然销毁，不能为解决未经证实的销毁问题再重写 Loader。

Qt 对属性序列访问和绑定依赖有专门说明，快照应以减少重复访问为目标，实际边界成本按所用版本测量。[QML 性能建议](https://doc.qt.io/qt-6.8/qtquick-performance.html)

### B2 · P1：减少重复 selection 通知和无关 result 通知

**问题与根因。** 一个 `_bump_form_revision()` 显式发一次 `selectionStateChanged`，随后 `formRevisionChanged` 同步进入环境 handler，又发一次；handler 还无条件发 `lastResultChanged`。

**修改范围：controller.py。**

1. 只移除 `_bump_form_revision()` 末尾显式的 `selectionStateChanged.emit()`。保留 revision 增加、所有 feedback 清理和 `formRevisionChanged.emit()`。
2. 保留 `_selection_environment_changed()` 的 transfer/request/preview 失效、cancel 和 selection 通知，不能把它整体 debounce 到下一个事件循环，否则拖放或旧请求可能在间隙继续被接受。
3. 新增很小的结果可用状态快照，例如 `(canOpenLastResult, canOpenPrimaryResult)`；仅在环境 handler 中发现此快照变化时发结果通知。
4. 结果数据真实变化、筛选器变化等现有显式通知点继续强制通知，并同步这个可用状态快照。可用一个私有 `_notify_last_result_changed(force=False)` 统一这几处行为；初始化放在依赖成员已就绪、状态信号开始使用之前。
5. `_apply_run_success()`、`setResultNoticeFilter()` 及所有现有 `lastResultChanged.emit()` 调用点逐一处理；不能因为目录路径没变而跳过新提醒内容。保留工具/项目切换造成的 true→false、false→true 通知。
6. 暂不改 `specChanged`、`materialChanged`、`supportChanged` 的接口、顺序或连接列表。工具切换两次环境检查属于后续可测量项，不在此批次引入通知事务框架。

**预期收益。** 单个 revision 路径少一次重复 selection 通知；结果可用性不变时，不再使结果类别等属性因无关环境变化而重读。不承诺减少一半 handler 调用，也不承诺拖窗 FPS 变化。

**风险与验收。** 旧选择请求/拖放预览仍须即时失效；结果成功、切到其他工具、切回结果工具、切项目、改变筛选类别都能更新 UI。下载阶段切换仍通知选择状态，下载字节变化只通知 progress。成功结果的全部提醒及“打开结果”按钮不得残留错误状态。

### B3 · P2：项目列表相同快照不 reset

**问题与根因。** `_apply_workspace_items()` 每次执行 `set_items()`，即使排序、字段值和行数全部相同，也重置模型。

**修改范围：优先仅 controller.py 的 workspace 落地路径。**

1. 保留 generation/closed 入口检查。
2. 对比旧、新列表的全部模型 role 内容与顺序。完全相等时跳过 `set_items()`；不只比较 path，否则会漏掉名称、detail、expanded 等变化。
3. 保留本次选择路径解析、`_workspace_selected_item` 更新和必要的选择通知。没有模型变化，不代表可以跳过全部业务状态处理。
4. 内容不同仍用当前 reset；文件夹展开/折叠仍使用现有 `update_at/splice`。不在通用 `ObjectListModel.set_items()` 中改变所有列表的契约。
5. 不额外保存多份巨型深拷贝。该判断仍是 O(N)，收益在避免相同模型重置，不能宣传成消除了大目录遍历成本。

**预期收益。** 无变化刷新不再扰动列表布局、当前项和滚动位置；不同查询结果的速度不由这一步保证。

**风险与验收。** 同路径不同 role 要更新；选择路径消失时原清理行为保留；旧 generation 结果丢弃；两文件夹异步展开并发结果不受影响。反复“刷新”没有内容变化时，模型 reset 次数目标为 0。

### B4 · P2：回收站搜索复用展示数据

**问题与根因（两报告遗漏）。** `setTrashSearch()` 每个编辑事件调用 `_filtered_trash_rows()`；后者遍历所有批次、重新拼接可搜索文本、格式化时间/大小/统计，再 reset 模型。列表虽虚拟化，主线程数据准备仍随批次数增长。

**修改范围：controller.py 的回收站展示路径。**

1. 在新一代回收站数据成功落地时，一次生成有序展示行及对应 casefold 搜索字符串。查询时只筛选预制行，不重复格式化。
2. 查询规范化规则保持 `.strip()` 和 casefold 的当前语义。同一个规范化查询重复到达且数据 generation 不变时，跳过重复过滤。
3. 新结果与当前展示内容完全相同时跳过 model reset。查询结果不同则先保留当前 reset 策略，不顺带引入通用 diff。
4. 新列表落地、恢复/移除后刷新、读取失败、换项目、关闭时按现有代际和状态边界替换/清理缓存。不能只在查询字符串变化时刷新。
5. 保持 batchId 对应的选择和恢复目标一致；不能按旧 row index 执行恢复。不要重写恢复业务逻辑。
6. 本批次不加入输入防抖，保持逐次输入即时筛选的交互。仅当大样本测量仍显示明显阻塞，再考虑 150–300 ms 合并或受限 worker；届时需处理查询/项目 generation、旧结果丢弃与 pending 期间操作目标。

**预期收益。** 将逐字符的格式化成本移到每次数据加载，避免重复查询与相同结果引起的重置；过滤仍为 O(N)，不能保证任意规模立即完成。

**风险与验收。** 大小写、空格、中文查询结果与原实现一致；失败后不显示旧项目缓存；被过滤选中项的默认替换行为保持；恢复目标与界面选中批次一致。缓存不得无限按历史查询积累。

## 6. 第二阶段：满足条件才实施

### C1 · pin/unpin 期间的布局动画

- **触发证据：** 在窄窗口反复 pin/unpin 时，测量显示主区宽度/文字换行/布局是实际耗时来源；hover-only 要分开记录。
- **最小方案：** 仅删除 `HoverSidebar.qml` 的 `Behavior on reservedWidth`，保留 `reservedWidth: pinned ? width : 0` 和 `Behavior on x`。关闭时最终预留 0，固定展开时最终预留 248；保留 110/220 ms hover 延迟、菜单 keepOpen 和 suppressPreview。
- **行为边界：** 内容宽度将一次到位，失去原先 190 ms 的平滑挤压，这是可见变化。严格要求动效原样时保留现状，不能自行实施此项。不能把预留宽度永久设成侧栏宽度。
- **收益/风险：** 有望减少 pin/unpin 中间帧 relayout；与普通 hover、纯拖窗不是同一收益。检查窄窗换行、滚动位置、焦点及 Windows 开关位置动画是否协调。

### C2 · 虚线边框与下载装饰波浪

- **触发证据：** 分开记录正常 resize 与下载期间 resize，确认 `DashedBorder.onPaint` 或 `updateFill.onPaint` 对帧预算有明显贡献。固定大小图标不是自动连带改造对象。
- **虚线最小路线：** 保留对宽高/颜色/圆角的失效；先确认 Qt 自身 requestPaint 合并效果。只有确有收益时，再做局部渲染替换。
- **Shape 候选路线：** 如环境已具备兼容模块，使用 Qt 5.15 支持的 PathLine/PathArc 构建圆角，保留线宽、5/4 虚线、半像素内缩、透明填充、颜色和圆角；对尺寸小于两倍圆角作限制。不能用 PathRectangle、CurveRenderer 等新版本 API。若需新增运行时/打包模块，则当前默认批次暂缓。
- **软件后端：** Shape 仍可能走 CPU；路径每次尺寸变化也有成本。以实际硬件和软件渲染 A/B 决定保留哪一实现；没有数据就保留 Canvas。
- **波浪最小路线：** 当前移动暂停逻辑完整保留。只有下载+resize 仍有明确问题时，增加仅装饰层的 resizing 状态，停止时通过已有 settle 机制恢复并重画最新 level；level/字节计数、取消、校验、下载任务仍实时运行。
- **禁止路线：** 全窗口停止更新、删除所有 resize 重画、直接把 20 FPS 降成 8–12 FPS、把波浪换渐变、添加 ShaderEffect 或全区 layer 缓存。冻结/替换装饰也改变动效时序，需处于用户接受的动效调整范围。
- **收益/风险：** 可能减少绘制/纹理更新成本；像素一致性、DPI、恢复补画和软件渲染均有风险，没有“无风险 GPU 替换”。

### C3 · 更新记录虚拟化

- **触发证据：** 最近 10 版全部展开或服务器返回长版说明时，打开/展开耗时与 rows 创建明显相关。默认一版展开场景无需为假想的无限历史改造。
- **实施：** 将 Flickable/Column/Repeater 局部换为 ListView；保留 buildRows 文本解析、版本顺序和 expandedVersions 外置状态；delegate 只绑定当前 modelData，不保留会在 reuse 时串行的局部展开状态。
- **尺寸契约：** 保留 `contentHeight`、`viewportHeight`、`contentY`、`resetPosition()`、`updateNotesFlickable` objectName、键盘 Home/End/PageUp/PageDown、右侧 16 px gutter。不得用“所有 delegates 的高度求和”反向破坏虚拟化。
- **关键难点：** 当前 implicitHeight 基于精确 body 高度，并上限 320。ListView 的可变高度 contentHeight 是估计值；须避免 `implicitHeight → viewport → estimated contentHeight → implicitHeight` 的布局振荡。可对短内容使用受限精确测量，达到 320 上限后固定视口上限；不能为测量长内容再隐藏创建所有 delegate。
- **滚动锚点：** 展开/收起前记录首个可见稳定行键和像素偏移，更新后恢复并 clamp；不能只保留数字 contentY 就声称“无跳动”。保留最新版本默认展开。
- **收益/风险：** 长内容降低同时创建的 delegate 数量，`buildRows()` 本身仍按 rows 构造；短列表收益可能很小，变量行高和焦点是主要回归风险。

Qt 明确说明 reuse 会更新模型属性，但 delegate 自有状态需正确复位；可变高度还会影响 contentHeight 估计。[ListView 文档](https://doc.qt.io/qt-6/qml-qtquick-listview.html#reusing-items)

### C4 · 不同 workspace 快照的增量更新

- **触发证据：** B3 后，真实相邻刷新之间改动很小，reset/重建仍在交互耗时中占主要部分。广泛重排、查询切换、换项目/换 scope 保留 reset。
- **实施：** 按完整 role 相等比较求公共前缀/后缀，对中间连续范围使用已有 splice；相同 path 的少量 role 变化优先 update_at。先形成新快照，再在 GUI 线程内成批应用，不在 model begin/end 之间执行 I/O 或等待。
- **同步：** 同时保持 `_workspace_items` 与 model 行顺序；恢复选中项按 path，视口按首可见 path+偏移；锚点消失时明确采用相邻有效项并 clamp。异步文件夹子项继续按 generation+path 定位。
- **边界：** splice 不自动保证滚动位置完全不变。一次大区间替换可能没有收益，不实现复杂 LCS、通用 diff 框架或 Qt 模型 move 重构。

### C5 · Windows resize 闪色修正（视觉一致性）

- **确定事实：** `WINDOW_BACKGROUND_RGB` 为 `#F7F5F1`，Main.qml 根窗口清屏色为 `#FCFCFB`；helper 的文字说明要求二者对齐。
- **候选影响：** 新暴露区域在内容帧到达前可能短暂显示不同色块；尚未在 Windows 复现。它解释的是闪色风险，不是帧率。
- **最小实施：** 在确认以当前根窗口 clear color 为目标后，将 RGB 常量对齐为 `(0xFC, 0xFC, 0xFB)`；保持 Win32 brush 安装、恢复、释放及 headless 分支原样。不要改变 UI 主题色。
- **验收：** 定向静态核对两端颜色；Win7/Win10/Win11 实机四边/四角 resize 检查新暴露区域。此项不承诺解决布局卡顿或彻底消除所有背景暴露。

### C6 · 剩余主线程热点，仅按测量进入

1. `_save_workspace_preferences()` 在 GUI 调用链同步读 JSON、写临时文件并 replace，材料偏好/规则保存等会触发。慢盘上可能停顿；但部分调用方依赖同步 bool 判断保存成功及回滚，不能直接改成 fire-and-forget。确认有明显耗时后，另做串行写入、快照顺序、完成通知、失败回滚与关闭刷盘设计。
2. `_apply_run_success()` 对大量 warnings 分类/构造模型，`setResultNoticeFilter()` 再全量过滤；大结果可能造成完成瞬间卡顿。测量命中后，只移动纯展示数据准备到已有 worker 流程，主线程统一应用；保留全部提醒、顺序、类别和复制结果。
3. `logList.onCountChanged: positionViewAtEnd()` 会与用户回看日志争抢视口。日志已批量追加并有限行数；是否改为“原先在底部才跟尾”是交互决定，不能冒充无行为变化的性能补丁。禁止为省重排把可选择的 TextEdit 换成不可选择 Text。
4. 嵌套 ScrollView/ListView 的滚轮和触控板交接只作为待复现场景；代码中未发现已确认的全局 WheelHandler 热循环。没有真实事件丢失/双滚动证据时不增加全局拦截，不强制固定滚动速度。

## 7. 验收设计与实际执行范围

### 7.1 先区分三种证据

| 证据 | 可以证明 | 不能证明 |
| --- | --- | --- |
| 定向代码核对、最小编译 | 改动边界与 Python 语法等 | QML 运行成功、交互流畅、目标机兼容 |
| GUI 局部探针与程序化 benchmark | 指定模型、尺寸与滚动位置变化下的局部工作量和帧/事件间隔 | 真实系统拖窗、滚轮/触控板事件链、Win7 安装包运行 |
| 目标设备实际交互 | 该设备、后端、数据规模下的体验与帧节奏 | 其他设备/后端、任意大数据都同样流畅 |

**本次已完成的只有报告和相关代码核对，没有下面的运行结果。**

### 7.2 获得定向性能验证授权后的场景矩阵

- 固定相同机器、Qt 版本、GPU/软件后端、DPI、窗口大小、数据和电源条件；前后各至少三次，区分冷启动与热态。
- 纯移动：不下载、下载中分别拖动；测原生标题栏及工具栏拖动。
- resize：单独横向、纵向、对角；覆盖 760 最小宽度、980 初始侧栏阈值、1460/1540 内容边距阈值；项目面板开/关各一次。
- 滚动：主区、输入列表、项目列表；真实滚轮小步、触控板连续惯性、滚动条拖动、嵌套区域边界交接；模板列翻页按现有行为检查。主区设计无横滚，不人为增加测试功能。
- 数据规模：普通表单和自定义材料较多表单；输入/项目列表 100/1,000/10,000 行；回收站 100/1,000/10,000 批次的内存假数据；最近 10 版全部展开和长更新说明。
- 更新：用本地假进度模拟 downloading/verifying/ready/cancelled，避免真的下载安装包；测试最小化、失焦、移动后恢复、resize 后恢复。
- 所有假数据放临时目录/内存，覆盖 settings 路径，禁止打开/改写用户真实项目。没有专项业务结果验证授权，不运行实际批量生产任务。

采集目标：相关 slot 耗时、getter 构造次数、通知次数、modelReset 次数、delegate 创建数、GUI heartbeat 延迟、帧间隔 P50/P95/P99/max、RSS。FPS 只统计持续有视觉变化且窗口可见的区间；空闲不绘帧不是掉帧。

60 Hz 下 16.7 ms 可作为一帧预算；100 ms 以上交互停顿要单独定位。它们是诊断目标，不是当前成绩，也不是在所有老机器上的保证。采用多次结果排除噪声：有稳定改善且无正确性/内存回归才保留条件优化；无收益就撤回该批次。

### 7.3 复用现有入口及其限制

[benchmark_qt_quick.py](/Users/wangjingchuan/Downloads/hr-toolkit/scripts/benchmark_qt_quick.py:33) 已支持 resize、scroll、main/upload/workspace 目标、处理负载和 production render loop。得到授权后可在当前项目 Python 环境运行以下定向示例，保存 stdout JSON；按改动选一个相关场景，不默认整矩阵全部跑。

```sh
python scripts/benchmark_qt_quick.py --mode resize --resize-axis both --duration 5 --interval 16 --tool material_collector --files 100
python scripts/benchmark_qt_quick.py --mode scroll --scroll-target upload --files 10000 --duration 5 --interval 16 --scroll-step 48
python scripts/benchmark_qt_quick.py --mode scroll --scroll-target workspace --workspace-files 10000 --duration 5 --interval 16 --scroll-step 48
```

重要限制：该脚本使用 `setWidth/setHeight` 和直接写 `contentY`，并非发送真实 wheel/trackpad 事件；也没有完整安装生产入口的原生标题栏与 resize helpers。即使 `--render-loop production`，也不能称为完整生产启动路径。`--processing` 的主要压力为独立进程计算和 GUI 直接追加模拟日志，不能证明线程回退/GIL 路径表现。

[benchmark_desktop_responsiveness.py](/Users/wangjingchuan/Downloads/hr-toolkit/scripts/benchmark_desktop_responsiveness.py:1) 主要针对工具切换及输入元数据延迟，也不是通用帧率测试。不要为本次改动把所有 benchmark 都运行一遍。

### 7.4 只维护受影响的现有契约

相关验证文件：

- [test_qt_controller.py](/Users/wangjingchuan/Downloads/hr-toolkit/tests/test_qt_controller.py:50)：下载字节进度隔离、结果上下文/分类、选择流程、workspace 选择和展开、OCR 状态恢复等。
- [test_qt_entrypoint.py](/Users/wangjingchuan/Downloads/hr-toolkit/tests/test_qt_entrypoint.py:370)：波浪暂停、live resize helper、原生边框、实时 workspace 面板、固定 objectName 等。
- [qt_connections_probe.py](/Users/wangjingchuan/Downloads/hr-toolkit/tests/qt_connections_probe.py:1)：生产 QML Connections 参数和更新弹窗路径。
- [ci_scope.py](/Users/wangjingchuan/Downloads/hr-toolkit/scripts/ci_scope.py:111)：路由核对；现有 gui_qt 路径已有兜底 GUI 路由，新增其他位置的脚本时再确认是否需显式映射。

只修改与实际变更冲突的旧断言，保留原行为保护；不能通过删断言或把期望直接改成当前输出“消除失败”。不为颜色常量等低风险变更新增镜像测试。信号失效/缓存状态这种有真实边界风险的改动，如获准测试，应补少量针对场景的验证。

例如 B2 需要覆盖一个 revision 的通知次数、旧 request 取消、结果可用 true/false 转换；B4 需要覆盖新 generation 同查询、查询等价、选中批次被过滤及项目更换。无需因此默认运行整个 test_qt_controller 或全仓测试。

## 8. 最终实施顺序与交付标准

| 顺序 | 批次 | 默认决策 | 主要收益对象 |
| --- | --- | --- | --- |
| 0 | 对齐当前代码与工作区，记录基线 | 必做，只读；性能运行另看授权 | 避免实施旧版本报告 |
| 1 | B1 表单统一快照 | 实施 | 联动、工具切换、批量选项更新 |
| 2 | B2 通知去重 | 实施 | 表单/状态变化引起的重复刷新 |
| 3 | B3 相同 workspace 快照跳过 reset | 实施 | 无变化刷新和视口稳定 |
| 4 | B4 回收站展示数据复用 | 实施 | 大回收站查询输入 |
| 5 | C5 兜底颜色一致性 | 确认目标颜色后独立小改 | Windows resize 的闪色风险 |
| 6 | C1 pin/unpin 布局动画 | 测量命中且允许动效变化 | 固定/取消固定侧栏 |
| 7 | C2 绘制热点 | 测量命中且兼容性条件满足 | 连续 resize、下载装饰 |
| 8 | C3/C4 长说明与不同快照增量 | 大样本下命中才做 | 弹窗长内容、局部列表变更 |
| 9 | C6 残余热点 | 另有具体耗时证据才做 | 慢盘、大结果、特定交互 |

每批交付：改了什么、对应哪个问题、改变了哪些通知/绘制次数、实际验证、尚未验证、如何单独回退。不要把所有问题合成一个无法归因的大提交；回退只撤销本批 diff，不能覆盖后续他人编辑或恢复整个工作区。

若用户另行要求提交，遵守仓库 Conventional Commit 格式和中文描述要求；本方案不自动授权提交。

最终结论应分开陈述：

1. 已减少的具体重复工作；
2. 有测量支持的性能改善及设备/后端；
3. 未完成的真实输入、原生拖窗、Qt5/Win7 实机验证。

**不能仅凭表单缓存、静态语法通过或 macOS 程序化 benchmark，宣称所有拖动、滚动、resize 已达到“极致流畅”。**
