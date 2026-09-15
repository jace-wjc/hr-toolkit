# Qt 交互性能方案实施记录

实施基线：`68c9084b4173acbd20ff250aef8ce6497b3802e5`，2026-09-15。

按[原实施方案](/Users/wangjingchuan/Downloads/hr-toolkit/docs/ui-interaction-performance-plan-for-claude.md)完成默认实施项 B1—B4，以及已能确定目标色的 C5。其余条目按方案的条件门槛保留原实现。没有提交、推送或修改构建/发布配置。

## 已实施

| 批次 | 改动 | 具体效果与边界 |
| --- | --- | --- |
| B1 | Main.qml 新增 `formSnapshot`，集中读取并复制 formFields，建立 byId 索引；全部消费者使用该快照 | 代码中只保留一个 formFields 读取入口。普通输入/单项勾选的通知时机不变，Python getter 未加可能过期的 revision 缓存。实际 getter 次数及运行体验未测 |
| B2 | 新增 `_notify_last_result_changed()`；移除 `_bump_form_revision()` 的重复 selection 通知 | 环境变化只在结果可用性改变时通知；筛选、结果清空、新结果仍强制通知。旧选择/拖放请求继续同步失效 |
| B3 | `_apply_workspace_items()` 对完整数据及顺序比较，相同内容跳过 model reset | 选择路径解析及通知仍执行；不同内容仍走原 reset，展开/折叠不变 |
| B4 | 回收站加载时预制展示行和搜索文本；复用筛选数据、跳过等价查询及相同内容重置 | 新数据落地会重新生成索引；读取失败、换项目、关闭清理缓存；换项目同时失效旧列表 generation |
| B4 选择同步 | 增加 `trashSelectedRow`，QML 高亮绑定到 controller；点击只更新 controller 选择 | 筛选/刷新后按 batchId 重新定位行，恢复仍使用该 batchId。避免只改变行号而让高亮与恢复目标分离 |
| C5 | Windows 兜底背景 RGB 对齐 Main.qml 清屏色 `#FCFCFB` | 保持原生 brush 生命周期和补帧逻辑；只修正色值不一致，不能据此声称帧率提高 |

修改的应用文件：

- [controller.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/controller.py)
- [Main.qml](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/qml/Main.qml)
- [live_resize.py](/Users/wangjingchuan/Downloads/hr-toolkit/hr_toolkit/gui_qt/live_resize.py)

## 条件项处理结果

| 条目 | 当前决定 | 依据 |
| --- | --- | --- |
| C1 侧栏布局动画 | 保留 | 方案要求 pin/unpin 实测命中且允许改变动效；当前没有该测量及动效变更范围 |
| C2 Canvas/波浪替换 | 保留 | 未建立绘制热点及目标后端 A/B 证据；不凭假设更换渲染方式或暂停更多绘制 |
| C3 更新记录虚拟化 | 保留 | 当前最近 10 版、默认展开一版；没有长内容创建耗时证据 |
| C4 不同 workspace 快照增量 | 保留 reset | B3 已处理相同内容；没有证明不同内容局部更新是主要成本 |
| C6 同步设置保存、大结果、日志跟尾、滚轮交接 | 保留 | 这些条目要求具体耗时/输入问题证据，且部分改变工作流；不能直接套用候选建议 |

上述条件项没有实施，也没有以“全部优化已完成”或“已测量无收益”代替其实际状态。此轮用户要求按方案实施，方案仍明确沿用项目的最小验证范围；没有把实施授权扩展为性能基准、测试套件或业务运行授权。

## 实际验证

1. 项目 `.venv/bin/python` 对修改的两个 Python 文件执行内存 `compile(..., 'exec')`：通过，不生成 pyc。
2. 同一环境的 Qt **6.11.2**，通过 `QQmlComponent` 编译修改后的 Main.qml：状态 Ready。使用 offscreen 平台，未调用 `create()`，未实例化界面或 AppController，未打开用户项目。
3. 定向读取受影响调用点与现有测试契约：formFields 单一入口、结果通知统一出口、回收站选中行接口、现有 GUI CI 路由。没有运行测试、Lint 或路由脚本。
4. 为 B1/B2/B3/B4/C5 分别导出 patch，并执行 `git apply --reverse --check`：五份均通过。仅检查可反向应用，没有实际回退代码。

**未验证：** QML 绑定求值和真实交互、状态转换测试、帧率/延迟/内存数据、Qt 6.6、Qt 5.15、Win7/Win10/Win11 实机、安装包与远程 CI。没有运行应用、性能基准、业务处理、测试套件、构建或打包。

## 分批审阅与回退

各 patch 只包含对应批次的应用代码改动，B4 包含其 Python/QML 选择同步，必须一起回退：

- [B1 表单快照](/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/hr-toolkit-ui-performance-ldr8nrxs/B1.patch)
- [B2 通知去重](/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/hr-toolkit-ui-performance-ldr8nrxs/B2.patch)
- [B3 相同项目列表](/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/hr-toolkit-ui-performance-ldr8nrxs/B3.patch)
- [B4 回收站缓存与选择](/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/hr-toolkit-ui-performance-ldr8nrxs/B4.patch)
- [C5 缩放背景色](/var/folders/ng/s5d0j44s06z6zdc_qr9ylpv80000gn/T/hr-toolkit-ui-performance-ldr8nrxs/C5.patch)

patch 位于本机临时目录，系统清理前如需长期保留应另行保存。以后回退先在仓库根目录执行对应 patch 的 `git apply --reverse --check`，成功后才使用 `git apply --reverse`。若后续改动导致检查失败，按该 patch 逐块撤销本批内容，不使用整文件 restore 或 reset 覆盖后续修改。

本轮代码结构减少了重复工作，但没有量化性能结果，不能声称已经达到所有场景流畅或 Win7 验收通过。
