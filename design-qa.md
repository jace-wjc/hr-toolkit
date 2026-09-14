# 侧栏分隔线与顶部留白：2026-09-14 局部调整

- 参考：`codex-clipboard-398c2ae1-2efc-4467-8c39-846b4cf79ff4.png`（1412×780，含窗口边缘），用户红框指定取消侧栏顶部横线、竖线延伸至顶及主区上移。
- 实现：`/tmp/hr-sidebar.N2JrQX/expanded.png`（1400×780 原生 Mac 内容截图，1×）；与参考在同次图像输入中比较。忽略窗口边缘和示例项目的差异，只核对分隔线、顶部间距与现有样式。
- 修改：侧栏容器不再绘制四边框；独立右侧分隔线贯穿内容窗口全高，随侧栏滑动及隐藏；主内容顶部内边距由 28 改为 8，上移 20 逻辑像素。
- 对照结果：顶部横线消失，竖线连接顶边，无双线；主区标题、说明、卡片整体上移，未与顶部操作区相撞；字体、颜色、图标、文案和业务交互不变。
- 检查：本机实际 QML 加载及原生截图通过，未见 QML 警告；未运行测试套件、构建或发布，未重新验证 Windows 实机。

**final result: passed**

---

# Claude 式侧栏与融合标题栏：2026-09-14 专项验收

- 范围：左侧导航收起／悬停预览／固定展开、顶部开关与原生窗口控制。遵照用户最新答复，不添加任何快捷键；不改人事业务处理、输入文件、输出或发布数据。
- Source visual truth：用户的 `codex-clipboard-d286531f-b9a6-4620-90fd-8c6830c8451f.png`（1851×1000），以及现有 HR 界面 `codex-clipboard-1fe047f9-c8c6-410e-9e55-ae1edf3bdc6f.png`。本机 Claude 停在登录页，悬停语义以用户明确描述为准，不声称已实测 Claude 内部动画。
- 实现证据：`/tmp/hr-sidebar.N2JrQX/expanded.png`（Mac 原生 1400×780，1×，开关与系统按钮同一行）；`collapsed-1400.png`、`hover-1400.png`、`collapsed-760.png`（760×780 逻辑视口，2×）和 `collapsed-900.png`（900×780，1.5×）。
- 比较：同一输入中打开参考图、收起及悬停实现图，重点对照顶部和左栏。参考为 Claude 首页，实际为 HR 社保页面，不比较业务内容；Mac 原生标题栏控件由桌面截图另行确认，窗口内容截图不包含系统交通灯。完整窗口保持原图比例，聚焦区域按逻辑像素比较，不将 2× 截图视作双倍界面尺寸。
- 字体与内容：保留 HR 原有字体、菜单、表单与文案，不复制 Claude 对话内容。
- 间距与布局：顶部为 40 逻辑像素的同色拖动区域，只有一个侧栏开关；临时展开不占主区宽度，固定展开保留 248 宽导航，收起不残留窄图标栏。
- 颜色与图标：沿用现有暖白／绿色；标准 Phosphor 开关和窗口图标附 MIT 许可，使用 96×96 PNG 副本以适配不包含 SVG 插件的现有 Windows 包，不增加运行时依赖。
- 交互：110ms 悬停打开、220ms 移走收起缓冲、190ms 平移动画；点击收起后停留图标不会立即再次展开；鼠标跨入侧栏不误收起；项目菜单打开期间保持预览；点击固定后移走保持展开。
- 实际专项检查：真实 Main.qml 隔离加载，在 1400／900／760 宽、100%／150%／200% 缩放下通过点击、悬停、移走、跨入、固定、菜单保持与当前业务选择不变的断言；未见 QML 加载或绑定警告。没有运行测试套件、构建、打包或发布。
- 对照修正：第一轮 Mac 受 Qt 新版安全区自动留白影响，开关落在系统按钮下方；桥接检测到 topPadding 时关闭重复留白，复查已同排。另发现现有 Windows 包会裁剪 SVG 插件，已改用 PNG 并重新加载检查。
- 窗口控制：Mac 保留系统红黄绿按钮，透明标题栏；Windows 用 Qt 5.15 已支持的系统移动／边缘缩放和最小化、最大化／还原、关闭，沿用关闭确认，不安装全局键盘或窗口过程钩子。
- 剩余验证范围：Mac 原生显示和点击已检查；Windows 控件仅在本机模拟渲染，Win7／Win11 原生拖动、缩放、任务栏及真实低配机帧率仍需实机验收，不声称所有平台已通过。

**final result: passed**

以上为本地界面与交互验收，不包含 Windows 实机结论。

---

# 长更新说明弹窗：2026-09-14 本地专项验收

- 范围：更新前提示、更新后说明／更新记录；只调整展示，不改发布说明数据、下载安装或人事统计逻辑。
- 参考：用户提供的 ChatGPT 无更新截图，以及下方已查看的 ChatGPT 有更新截图；保留本程序图标、中文、浅色背景和现有操作含义，不宣称逐像素复制。
- 方法：按 Product Design 的截图对照流程，直接加载实际 QML 组件，使用临时完整 0.9.1 说明；不启动业务控制器、不下载、不安装、不发布。
- 修改前证据：`/tmp/hr-update-scroll.22Zdw7/before-900x480.png`。900×480 窗口中弹窗高 448，外层滚动裁掉了说明区底边；分类与正文层级不明显。
- 修改后证据：`/tmp/hr-update-scroll.22Zdw7/after-900x480.png` 与 `after-900x480-bottom.png`。同一视口、同一说明、1× 像素密度，弹窗改为 580×403.2；标题和按钮固定，只有说明区滚动，边框完整。
- 尺寸：最大 580×520 逻辑像素，高度不超过宿主窗口 84%；短说明按内容收缩；无更新仍为 260 宽紧凑卡片。
- 排版：分类加粗、条目缩进、自动换行；长连续英文不会横向溢出；滚动条独立留白，不覆盖文字；不足一屏时隐藏滚动条。
- 专项检查：1366×768、1024×600、900×480、640×480、400×480 逻辑视口，1×／1.5×／2× 缩放组合；完整说明、8 倍长度说明、长英文、短说明、无说明、无更新、强制手动下载提示和多版本记录。
- 交互检查：滚轮向下、拖动滚动条、PageDown／PageUp、End／Home；能到达末尾，按钮坐标不随正文移动；重新打开回到顶部；组件加载没有 QML 警告。
- 高缩放证据：`/tmp/hr-update-scroll.22Zdw7/after-stress-mandatory-900x480.png`（1.5×）与 `after-history-stress-640x480-bottom.png`（2×）；按对应像素密度观察，不把放大的截图当作窗口逻辑尺寸。
- 短说明与无更新证据：`/tmp/hr-update-scroll.22Zdw7/after-short-1024x600.png`、`after-none-640x480.png`。修正了小数高度造成短说明仍显示滚动条的边界问题。
- 可复现预览：`/tmp/hr-update-scroll.22Zdw7/preview.py`、`preview.qml`；仅临时夹具，不写入正式发布说明。
- 兼容边界：沿用 QtQuick／Controls 2.15 的能力，现有打包规则会包含新增 QML；本机 Qt 实际渲染及缩放模拟通过，尚未进行 Windows 7／11 实机验证或打包。未执行全仓检查或测试套件。
- 生效范围：新布局随新版程序安装生效，不能远程改变已安装旧版的更新提示。

**final result: passed — 本地更新说明布局与滚动专项；Windows 实机待验证。**

---

# 更新提示样式：此前验收记录（非上述专项结果）

- 本轮补充：更新后首次启动说明、离线“更新记录”入口，以及下载／校验／启动安装程序的独立状态。
- 更新中参考：本机 `/Applications/ChatGPT.app/Contents/Frameworks/Sparkle.framework/Resources/SUStatus.nib`，以原生资源加载出 `/tmp/hr-update-reference.cNw43B/sparkle-status.png`（400×110 内容区；原生窗体含标题栏 400×139）。预览使用示例进度文字，并未下载或更新 ChatGPT。
- 参考结构：左侧应用图标；右侧标题、细进度条；状态文字与取消按钮位于同一行。本轮实现为 `UpdateProgressDialog.qml`，保留本程序图标与中文。
- Windows 安装阶段：`update_runner.py` 的独立轻量 Tk 安装进度窗口同步改为左图标、右标题／进度条／状态；不引入 Qt 依赖，不提供会中断文件替换的取消按钮。Windows 系统权限确认保持原生，不提前显示安装成功。
- 更新说明来源：`hr_toolkit/release_notes.py`，发布清单与程序离线记录共用，历史版本未提供的内容不编造。

- 参考图：用户提供的 `codex-clipboard-24b6c076-5782-46d0-9f58-8bb00c11ab0c.png`（259×232，无更新）；已通过浏览器查看 https://cdn3.ldstatic.com/original/4X/0/0/a/00adcf7c4b080943ebe86817bb5ceb2ec5f0bd76.png （1138×810，有更新）。
- 实现：`hr_toolkit/gui_qt/qml/components/UpdatePromptDialog.qml`。无更新为紧凑卡片，有更新为图标、版本说明、更新内容和操作区。
- 有意保留的差异：中文与本程序图标、浅色主题；不新增跳过版本或自动下载功能；强制更新拒绝按钮明确标为退出程序。
- 实现截图、视口与密度归一化、全图和局部对照：尚未采集，不沿用下面历史工作区验收的结论。
- 字体、间距、颜色、图标清晰度及文字换行：已按参考编写，尚未进行实际渲染对照。
- 已执行：仅变更 Python 语法与 QML 编译检查。没有进行点击验收、Windows 实机验证、测试套件或打包。
- 阻塞原因：项目当次默认验证范围仅允许最小语法与编译检查；后续需要在授权后补两种状态的截图与按钮行为验证。
- 对照迭代：暂无实际渲染对照，不宣称像素级复刻已通过。

**final result: blocked**

---

# HR Toolkit 项目工作区设计验收（历史记录，非本次更新提示验收）

**Source visual truth**

- `/private/tmp/hr-toolkit-requirements-audit/01-workspace.png`
- 原型像素：1440 × 900

**Rendered implementation**

- `/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/com.openai.sky.CUAService/Python Screenshot 2026-08-03 at 6.27.59 PM.jpeg`
- 实现截图像素：1187 × 768
- 对照图：`/private/tmp/hr-toolkit-ui-comparison.png`

**Viewport and normalization**

- Tk 窗口请求尺寸：1440 × 900；受当前 Mac 可用屏幕区域限制，实际整窗截图为 1187 × 768。
- 对照时将原型按比例缩小后居中到 1187 × 768 白底面板；实现截图保持原始 1187 × 768，未拉伸。
- 桌面原生 Tk 界面没有 CSS viewport 或浏览器 `deviceScaleFactor`；本次按最终屏幕像素比较。

**State**

- 当前功能：社保明细与汇总。
- 当前项目：已打开可写项目。
- 右侧范围：全部文件。
- 实现截图中的目录树为根目录折叠态；原型为示例资料已选中、目录树展开态。因此不把文件行数量和展开层级差异计为视觉缺陷，只比较三栏结构、层级、间距、颜色、文字和控制位置。

## Findings

- 没有遗留 P0、P1 或 P2 问题。
- [P3] 右侧原型为文件和文件夹提供了更丰富的图标，当前原生 `Treeview` 主要依赖展开箭头和文字。
  - Location: 右侧“项目文件”目录树。
  - Evidence: 原型为文件夹和文件显示独立图标；实现保留系统展开箭头、结果色标和文字层级。
  - Impact: 不影响查找、展开、打开或定位，视觉识别速度略低。
  - Follow-up: 后续如提供正式跨平台图标资产，可为目录、Excel、ZIP、PDF 增加统一图标；本次不使用字符或手绘图标替代。

## Required fidelity surfaces

- Fonts and typography: 延续现有系统中文字体，标题、分组、正文和辅助信息层级清楚；修正后表单标签完整显示，无裁切。项目长路径仅在右侧显示，左侧改为“当前项目 · N 次处理”。
- Spacing and layout rhythm: 三栏结构、固定左导航、主操作区和右项目区成立；卡片间距、圆角和边界沿用现有 HR Workbench 设计语言。右区支持 270–430 宽度调节及折叠轨道。
- Colors and visual tokens: 暖纸底色、白色卡片、深绿色主色和灰色辅助文字与原型一致；成功、警告和禁用状态使用现有语义色。
- Image quality and asset fidelity: 原型没有照片、插画或品牌图片资产；实现没有用占位图片替换目标资产。目录图标差异列为 P3。
- Copy and content: “结果位置”显示为“当前项目 / 本次处理结果”，避免向人事暴露长路径；“处理结果”“上传资料”“补充资料”“共用资料”等名称与需求一致。
- Responsiveness and accessibility: 主区变窄时表单切换纵向布局；右区在窄窗口进入抽屉模式。按钮均保留可读文字，禁用状态可见，正文对比度符合现有桌面主题。
  抽屉支持 `Esc` 关闭，折叠轨道支持鼠标、回车和空格重新展开。

## Focused region evidence

- 对照图中重点检查了中心表单和右侧项目区。第一轮发现中心“参保人员花名册”“结果位置”标签被压缩为单字，且长磁盘路径降低可读性；修正后的实现截图显示完整标签和业务化结果位置。
- 右侧区域在全视图中已经能清楚判断标题、项目身份、范围切换、搜索、添加、刷新、目录树和详情区，无需额外裁切图。

## Comparison history

1. 第一轮实现截图：`Python Screenshot 2026-08-03 at 6.24.21 PM.jpeg`
   - [P2] 非紧凑表单第一列宽度不足，两个字段标签只显示首字。
   - [P2] 结果位置直接显示很长的绝对路径，不符合人事用户的阅读方式。
2. 修正：
   - 为非紧凑表单标签列增加 116 像素最小宽度，并提高紧凑布局切换阈值。
   - 结果位置改为业务文案“当前项目 / 本次处理结果”，实际路径仍在内部用于运行。
   - 左侧项目卡片改为处理次数摘要，完整路径保留在右侧项目区。
3. 第二轮实现截图：`Python Screenshot 2026-08-03 at 6.27.59 PM.jpeg`
   - 表单标签和业务化结果位置已完整显示，未发现新的 P0/P1/P2 视觉问题。
   - 后续收起态和窄窗口追加截图因 Mac 锁屏未能继续；相关状态已由 Tk 隐藏窗口 smoke、方法绑定和响应式分支检查覆盖，作为残余测试缺口记录，不阻塞主视图验收。
4. 发布前安全与交互复核：
   - 资料导入期间禁止切换项目或开始处理；退出时先取消并等待安全落盘，再释放项目写锁。
   - 重复打开当前项目保持原可写实例；切换项目会清空上一项目的输入和“打开结果”状态。
   - 链接输入、未登记或已改动的历史结果、处理期间插入的链接均会被拒绝。
   - Windows 与 macOS 打包检查同时阻止 `.hrtoolkit`、上传资料、处理结果、补充资料和共用资料进入安装包。
   - 317 项自动化测试、强制编译检查和差异格式检查全部通过。

## Implementation checklist

- [x] 三栏工作区与右侧项目文件区。
- [x] 项目切换、打开文件夹、全部文件/当前功能、搜索、添加、刷新。
- [x] 右侧收起/展开、宽度记忆和窄窗口抽屉逻辑。
- [x] 表单标签裁切修复和人事化结果位置文案。
- [x] 上传资料、正式结果、补充资料和项目复用链路。
- [ ] P3：获得正式跨平台文件类型图标资产后再增强目录树图标。

**final result: passed**

---

## 项目弹窗追加验收（2026-08-10）

**Source visual truth**

- 新建工作项目：`/tmp/hr-toolkit-figma-reference/new-project.png`
- 项目回收站：`/tmp/hr-toolkit-figma-reference/recycle.png`
- 检查资料：`/tmp/hr-toolkit-figma-reference/import-checking.png`
- 复制并校验：`/tmp/hr-toolkit-figma-reference/import-progress.png`
- 完成保存：`/tmp/hr-toolkit-figma-reference/import-finalizing.png`

**Rendered implementation**

- 新建工作项目：`/tmp/hr-toolkit-final-visual-qa.P0L0WO/01-new-project-current.png`
- 检查资料：`/tmp/hr-toolkit-final-visual-qa.P0L0WO/02-import-checking-current.png`
- 复制并校验：`/tmp/hr-toolkit-final-visual-qa.P0L0WO/03-import-copying-current.png`
- 正在完成保存：`/tmp/hr-toolkit-final-visual-qa.P0L0WO/04-import-finalizing-current.png`
- 修复后的项目回收站：`/tmp/hr-toolkit-figma-reference/current-recycle-fixed.png`
- 回收站并排对照：`/tmp/hr-toolkit-figma-reference/recycle-comparison-fixed.png`

**Findings**

- 没有遗留 P0、P1 或 P2 问题。
- 新建项目弹窗完整展示名称、保存位置、最终路径、留存内容、位置风险和操作按钮；长路径会换行，内容较高时可滚动。
- 导入弹窗的实际内容区为 640 × 510，检查、复制和最后保存三种状态均无裁切；前两阶段可取消，最后安全登记阶段禁用取消。
- 回收站曾出现底部操作按钮被裁切的发布阻断问题。修复后弹窗为 760 × 487，关闭和恢复按钮完整显示，底部保留 20 像素空间；小屏只压缩可滚动的中间列表区。
- 回收站使用业务事项作为主标题，单列业务分组和功能；恢复位置不显示带时间戳的内部目录，同名保护使用提醒色。
- macOS 原生标题栏和无背景蒙层与 Figma 有视觉差异，属于桌面平台惯例，不影响操作和信息层级。

**Scope decision**

- 原型中的“直接修改原文件夹”风险确认页没有实现。当前冻结范围明确不直接修改外部原文件；资料文件夹改名只处理项目内经过校验的结果副本，因此该风险分支已被产品方案取消，不属于漏做弹窗。

**Verification**

- 317 项自动化测试在严格 `ResourceWarning` 模式下全部通过。
- 项目创建、回收站、导入取消、最后保存恢复、只读、同名不覆盖、链接拒绝和打包防资料泄漏均有定向覆盖。
- 全模块强制编译、运行烟测和 `git diff --check` 全部通过。
- macOS 源码版已逐页实机截图验收；Windows 安装包仍需在真实 Windows 100% / 125% / 150% 缩放下完成发布前人工烟测。

**final result: passed for source and macOS visual QA; Windows packaged smoke pending**

---

## 滚动条样式追加验收（2026-08-03）

**Source visual truth**

- 目标滚动条：`/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/codex-clipboard-467e6e0b-bb06-4bfc-aebf-f2994e9888a4.png`（63 × 424）
- 原问题全图：`/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/codex-clipboard-17129da5-7631-40db-a2f6-66cd59a7a6dc.png`（1636 × 855）

**Rendered implementation**

- 最终 Tk 组件截图：`/private/tmp/hrtoolkit-scrollbar-final-window.png`（328 × 640）
- 同尺寸聚焦对照：`/private/tmp/hrtoolkit-scrollbar-final-comparison.png`（126 × 424；左侧为目标，右侧为实现）

**Viewport and normalization**

- 实现使用 macOS Tk 9.0.3、1× UI 比例，组件窗口为 260 × 540 逻辑像素；系统窗口阴影使最终截图为 328 × 640 像素。
- 聚焦对照只保留滚动轨道，将实现轨道纵向归一到 424 像素，横向厚度保持 1×，再各置于 63 × 424 白底区域。
- 两侧内容量和当前位置不同，因此滑块长度与纵向位置不作为样式差异；本次只比较轨道宽度、滑块宽度、圆角、颜色和箭头可见性。

**State**

- 纵向滚动条处于接近顶部状态；横向滚动条同时显示在组件底部。
- 默认、悬停和按下使用三档浅灰色；截图记录默认状态。

**Findings**

- 没有遗留 P0、P1 或 P2 问题。
- 目标约为 12 像素白色轨道、8 像素浅灰圆角滑块；实现采用相同尺寸关系，端部为圆角胶囊，没有可见的旧式三角箭头。
- 原箭头点击区域仍以透明样式保留，拖拽、轨道翻页、逐行点击、滚轮以及内容回调没有改变。

**Required fidelity surfaces**

- Fonts and typography: 本次目标不包含文字，现有字体配置未改。
- Spacing and layout rhythm: 轨道厚度 12 像素、可见滑块约 8 像素；纵向和横向使用同一尺寸体系。
- Colors and visual tokens: 白色轨道；默认滑块 `#EAEAEB`，悬停 `#DCDCDD`，按下 `#CCCCCE`，与目标浅灰层级一致。
- Image quality and asset fidelity: 滑块按当前 UI 比例在内存生成，并使用可拉伸边框保留圆角端帽；1× 下边缘清晰，没有缩放模糊或透明边缘黑线。
- Copy and content: 没有改动任何界面文案或业务内容。

**Focused region evidence**

- 聚焦对照直接并排展示了目标轨道与最终实现轨道；宽度、浅灰色和圆角端帽一致，没有旧式箭头残留。
- 全图中的主区、运行记录和项目文件区均使用未命名的全局 `ttk.Scrollbar`；同一全局样式覆盖 8 个纵向和 1 个横向实例，无需逐个改控件。

**Comparison history**

1. 初始实现使用 `clam` 默认滚动条，14–15 像素宽，带可见三角箭头和立体边框，与目标存在 P2 视觉差异。
2. 修正为全局白色细轨道和浅灰圆角滑块；箭头命中区域透明化，保留原绑定。
3. Tk 8.6.14 与 Tk 9.0.3 实测纵向宽度和横向高度均为 12 像素；逐行点击与拖拽后内容位置均按原逻辑变化。
4. 最终聚焦对照未发现新的 P0/P1/P2 视觉问题。

**Implementation checklist**

- [x] 8 个纵向滚动条统一样式。
- [x] 1 个横向滚动条统一样式。
- [x] 保留箭头点击、拖拽、轨道点击、滚轮和内容联动。
- [x] Tk 8.6、Tk 9.0 运行验证。
- [x] 目标图与最终实现同图对照。

**final result: passed**

---

# Qt Quick 与 Tk 同版验收（2026-09-02）

## Evidence

- Source visual truth: `/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/codex-clipboard-f6d577b3-198a-4f67-a577-1699c1227df4.png`
- Initial Qt baseline: `/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/codex-clipboard-9aa81193-906d-4685-8953-620c7df3c423.png`
- Final implementation: `/tmp/hr_qt_tk_match_project_final.png`
- Full-view comparison: `/tmp/hr_tk_qt_project_comparison_final.png`
- Focused form comparison: `/tmp/hr_tk_qt_project_form_comparison_final.png`
- Compact-width implementation: `/tmp/hr_qt_tk_match_760_final.png`
- macOS Cocoa/Qt native capture: `/tmp/hr_qt_macos_native_final.png`
- Project drawer and styled dialog: `/tmp/hr_qt_workspace_dialog_styled.png`
- Viewport: source outer window 1810 x 941; source client area 1810 x 911 after removing the 30 px macOS title bar; Qt client viewport 1810 x 911.
- Density normalization: the source screenshot metadata does not expose macOS backing scale, so its cropped 1810 x 911 pixels were treated as the 1:1 target coordinate surface. The Qt implementation is 1810 x 911 logical/physical pixels at offscreen device scale 1. No resampling was applied.
- State: `material_collector`, light theme, writable project named `2026年8月人事月度工作`, no selected library or roster, no active processing task.

## Required fidelity surfaces

- Fonts and typography: platform families now follow Tk (`PingFang SC`, `Microsoft YaHei UI`, and Win7 `Microsoft YaHei`); title, group labels, body text, hints, weights, wrapping, and truncation match the source hierarchy. Minor antialiasing differences remain platform-renderer dependent.
- Spacing and layout: the sidebar is 248 px, the main content is centered and capped at 820 px, and the header, upload card, form card, actions, and log align within a few pixels of the normalized source. Card radii, padding, section gaps, and compact breakpoints were checked.
- Colors and tokens: Tk background, surface, border, text, disabled, navigation, and green action tokens are used directly.
- Image and icon fidelity: the original brand raster is reused; the tool and folder icons follow the original Tk icon geometry. No emoji or first-letter placeholders remain.
- Copy and content: the visible material-collector labels and action order match the source. Project status text remains data-dependent, so the empty QA project reports writable state rather than the source project's historical run count.
- Responsiveness and interactions: 760 x 600 compact mode keeps controls readable without overlap. Nine tool routes load successfully. Project drawer open/close, dialog styling, file actions, focusable controls, and scrollable content were exercised. A real macOS corner drag also repainted continuously to a smaller native window without a skeleton, blank region, mosaic, or post-drag remnant.

## Comparison history

1. Initial baseline — blocked.
   - P1: Qt used a full-width, low-density layout with native-looking gray controls and materially different visual hierarchy.
   - P1: navigation used text placeholders instead of the Tk icon system, and the project-files action did not follow the Tk right-edge workspace pattern.
   - P2: the material-collector form order, spacing, card proportions, and action placement drifted from Tk.
   - Fixes: introduced Tk design tokens and shared controls, restored the exact form order, capped and centered the content, reused the real brand mark, ported the tool icons, and rebuilt the right-side project workspace as an overlay.

2. Intermediate implementation (`/tmp/hr_qt_tk_match_1810.png`) — blocked.
   - P2: the upload card still had an extra header action, a solid drop-zone border, and compressed vertical rhythm.
   - P2: sidebar brand position and project-button widths differed from the source; compact navigation icons rendered too large.
   - P2: default Qt dialog footers visually broke the otherwise Tk-like screen.
   - Fixes: moved selection affordances into the drop zone, restored the dashed outline and card height, aligned sidebar geometry and control widths, fixed compact icon sizing, and added the shared Tk-style dialog surface.

3. Final implementation — passed.
   - Full-view and focused comparisons show no actionable P0, P1, or P2 mismatch.
   - The project drawer closes with `opened=false`, `visible=false`, and a pixel-identical post-close main screen (zero changed pixels), so no remnant panel remains.

## Follow-up polish

- P3: Qt and Tk render the combo-box arrow area and font antialiasing slightly differently. Keeping the custom Qt control avoids native-style relayout during live resize and is the safer cross-platform choice.

final result: passed

---

# 侧栏项目卡与教程二次验收（2026-09-02）

## Evidence

- Source visual truth: `/Users/wangjingchuan/Downloads/Codex Image Sep 2, 2026, 04_07_22 PM.png`
- Rendered implementation: `/tmp/hr_toolkit_sidebar_1647x915_final.png`
- Full-view comparison: `/tmp/hr_toolkit_sidebar_full_compare_final.png`
- Focused sidebar comparison: `/tmp/hr_toolkit_sidebar_focus_compare_final.png`
- Tutorial implementation: `/tmp/hr_toolkit_tutorial_final.png`
- Compact sidebar: `/tmp/hr_toolkit_sidebar_compact_final.png`
- Compact tutorial: `/tmp/hr_toolkit_tutorial_compact_final.png`
- Source pixels: 1647 × 953, including a 38 px macOS title bar.
- Implementation pixels and CSS/logical viewport: 1647 × 915 at offscreen device scale 1.
- Normalization: the source title bar was cropped, producing a 1647 × 915 client image; no resampling was applied before the full-view comparison. The source screenshot does not publish its backing-scale metadata, so the comparison treats its client pixels as the target surface.
- State: light theme, `social_security`, read-only project `2026年8月人事月度工作`, no selected input or roster.

## Findings

- No actionable P0, P1, or P2 differences remain in the requested project-card region.
- [P3] The proposal image uses a roughly 335 px sidebar while the product constraint requires retaining the current 248 px sidebar.
  - Evidence: the focused comparison shows the same hierarchy and controls compressed into the current width.
  - Impact: horizontal breathing room is smaller, but the project name, status, dropdown affordance, and both actions remain readable and usable.
  - Decision: accepted as intentional because widening the sidebar would violate the user's explicit constraint and reduce the main work area.

## Required fidelity surfaces

- Fonts and typography: existing platform typography and all current sizes/weights remain unchanged. Project title and status preserve the proposal hierarchy; long names elide rather than overlap.
- Spacing and layout rhythm: one rounded card now contains the header, selector, and two lightweight actions. The 248 px sidebar and all lower navigation geometry remain unchanged. Compact mode remains usable at 760 × 600.
- Colors and tokens: existing warm background, white surface, green accent, neutral border, and muted text tokens are reused without introducing a new palette.
- Image quality and asset fidelity: the existing brand mark remains unchanged. The project and log actions use the project's shared `ToolIcon` renderer at the existing stroke weight; no emoji or raster placeholders were introduced.
- Copy and content: the card shows `工作项目 / 最近项目`, the project name, `当前项目 · 只读`, `新建项目`, and `打开项目`. The tutorial contains the exact 11 legacy Tk entries and all 66 original lines from one shared source.
- States and interactions: selector, recent projects, new project, open project, tutorial navigation, and the icon-only log entry use focusable Qt controls. The old-history entry is hidden while its implementation remains available for later restoration.
- Responsiveness and accessibility: keyboard focus was restored after the first implementation pass by replacing mouse-only project actions with `Button` controls. The project card collapses to a single project button in compact mode; the tutorial remains scrollable and fully visible.

## Focused region evidence

- The focused comparison directly places the proposal sidebar and final sidebar in one image. It verifies the unified card, label order, selector border/radius, status line, two icon actions, downstream navigation position, and preserved color system.
- The tutorial required a separate state because the proposal does not show it. Its final capture verifies the original Tk two-column layout: grouped feature navigation on the left and styled, scrollable instructions on the right.

## Comparison history

1. Baseline — blocked.
   - [P2] Project title/status, new/open actions, and recent projects were rendered as four separate regions rather than one proposal-style card.
   - [P2] Qt used a generic six-step tutorial whose structure and copy differed from Tk.
   - [P1] Expanding or collapsing a workspace folder reset the model, forcing the visible list back to the top.
2. First implementation — blocked.
   - The unified card and exact tutorial content were present, but the project selector/actions were mouse-only and therefore introduced a keyboard-accessibility regression.
3. Final implementation — passed.
   - Replaced mouse-only project actions with focusable buttons without changing the visual layout.
   - Workspace expansion/collapse now updates, inserts, and removes rows without a model reset; a 10,000-row live test retained `contentY` exactly.
   - Final full-view, focused, tutorial, and compact captures show no new overlap, clipping, or actionable P0/P1/P2 mismatch.

final result: passed
