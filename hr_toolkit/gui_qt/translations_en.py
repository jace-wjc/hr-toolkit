"""US English display catalog. Numbered placeholders preserve source data."""

MESSAGES = {
 '收起 Sage': 'Collapse Sage',
 '回到最新消息': 'Jump to latest',
 '更多选项': 'More options',
 '数据发送说明': 'Data sharing details',
 '消息与附件将发送至 AI 服务': 'Messages and attachments are sent to the AI service',

 '表格：{0} 行': 'Table: {0} rows',
 '最近使用': 'Recent',
 '打开文件': 'Open File',
 '打开文件夹': 'Open Folder',
 '打开所在文件夹': 'Open Containing Folder',
 '清空本工具记录': 'Clear Tool History',
 '仅显示当前工具的记录；打开文件或位置不会添加资料或开始处理。': 'History for this tool only. Opening a file or location does not add inputs or start processing.',
 '无法打开最近记录：文件或文件夹已移动、删除、无法访问，或没有可用的打开程序。': 'Could not open this recent item. It may have been moved, deleted, or become unavailable, or no suitable app is installed.',
 '暂时无法打开最近记录，请稍后重试。': 'Could not open this recent item. Please try again.',
 '最近文件': 'Recent Files',
 '最近文件夹': 'Recent Folders',
 '浏览文件': 'Browse Files',
 '暂无适用于此输入的最近记录。': 'No recent items match this input.',
 '文件按当前输入类型筛选；选择文件夹位置后仍使用系统选择窗口。': 'Files match the current input type. Browse a recent folder using the system picker.',
 '移除或清空记录不会删除原文件。': 'Removing history does not delete your files.',
 '清空记录': 'Clear History',
 '最近文件已移动、删除或无法访问，请重新选择。': 'The recent file was moved, deleted, or is unavailable. Please select it again.',

 '图片缓存已满，请删除不再需要的旧对话后再试。': 'The image cache is full. Delete old chats you no longer need, then try again.',
 '服务返回详情：{0}': 'Provider details: {0}',
 '上次回复被中断，请重试。': 'The previous response was interrupted. Try again.',
 'Enter 发送 · Shift+Enter 换行 · Ctrl+K 开关助手': 'Enter to send · Shift+Enter for a new line · Ctrl+K for Sage',
 '{0} 个工作表': '{0} sheets',
 '共 {0} 行': '{0} rows',
 '共 {0} 行（已截取重点行）': '{0} rows (selected rows included)',
 '附件合计内容过大，无法完整发送。请先发送这批，再附下一批。': 'The combined attachments are too large. Send these first, then attach the next batch.',
 'GLM-5.3-Flash 和 GLM-5.3-FlashX 支持图片；GLM-5.3 仅支持文字。': 'GLM-5.3-Flash and GLM-5.3-FlashX support images. GLM-5.3 is text-only.',
 'Qwen3.7-Plus、Qwen3.8-Max / Flash 和 Qwen-VL 支持图片。': 'Qwen3.7-Plus, Qwen3.8-Max / Flash, and Qwen-VL support images.',
 'deepseek-flash 对应 V4.1 Flash；deepseek-v4-pro 对应 V4 Pro 0813。V4 Flash 0731 已下线，deepseek-v4-flash 仅为兼容名称，当前转至 V4.1 Flash。': 'deepseek-flash is V4.1 Flash; deepseek-v4-pro is V4 Pro 0813. V4 Flash 0731 has been retired. deepseek-v4-flash is a compatibility alias currently routed to V4.1 Flash.',
 'AI 服务返回错误：{0}': 'AI service error: {0}',
 'AI 服务返回错误（HTTP {0}）：{1}': 'AI service error (HTTP {0}): {1}',
 'API Key 无效或未授权，请检查设置。': 'The API key is invalid or unauthorized. Check Settings.',
 '服务余额不足，请充值后重试。': 'Your provider account has insufficient credit.',
 '当前 Key 无权访问该模型或接口。': 'This API key cannot access the selected model or endpoint.',
 '服务地址或模型名称不存在，请检查设置。': 'The endpoint or model was not found. Check Settings.',
 '请求过于频繁或额度受限，请稍后重试。': 'Rate limit or quota reached. Try again later.',
 '请稍后重试或联系管理员。': 'Try again later or contact your administrator.',
 'AI 服务返回了空回复。{0}': 'The AI service returned an empty response. {0}',
 'AI 服务未返回任何回复。{0}': 'The AI service returned no response. {0}',
 'AI 服务未返回有效回复。{0}': 'The AI service returned an invalid response. {0}',
 '（当前模型「{0}」可能不存在、未开通，或该服务商不认这个叫法。请在对话框左下角的模型菜单里换一个，或到设置里核对模型名称与控制台是否一致）': 'Check that {0} is available for your account. Choose another model or verify its name in Settings.',
 'AI 服务没有返回流式内容（{0}）。请确认服务地址是 OpenAI 兼容接口，例如 https://api.minimax.cn/v1/chat/completions{1}': 'The endpoint did not return a streaming response ({0}). Check that it supports Chat Completions. {1}',
 '响应是空的': 'empty response',
 '首个片段：{0}': 'first chunk: {0}',
 '列表里没有模型「{0}」。': 'Model {0} is not in the list.',
 '原图片附件已不可用，请重新附加图片后发送。': 'The original image attachment is unavailable. Attach it again before sending.',
 'AI 服务地址发生重定向，请在设置中填写最终接口地址。': 'The endpoint redirects to another address. Enter the final API endpoint in Settings.',
 '图片过大，请先缩小图片后再附加。': 'This image is too large. Resize it before attaching.',
 '图片尺寸过大或无法识别，请先缩小图片后再附加。': 'The image dimensions are too large or unreadable. Resize it before attaching.',
 '今天 {0}': 'Today {0}',
 '昨天 {0}': 'Yesterday {0}',
 '尚未配置 API Key。': 'No API key is configured.',
 '尚未配置 API Key，请先打开助手设置。': 'Add an API key in assistant settings.',
 'API Key 格式不正确，请重新复制。': 'The API key format is invalid. Copy it again.',
 '模型名称不能为空。': 'Enter a model name.',
 '模型名称不合法。': 'The model name is invalid.',
 '服务地址必须以 http:// 或 https:// 开头。': 'The endpoint must start with http:// or https://.',
 '服务地址不合法。': 'The endpoint is invalid.',
 '一次最多附加 {0} 个文件，请先移除不需要的。': 'You can attach up to {0} files per message. Remove an attachment first.',
 '一次最多附加 {0} 张图片，请先移除不需要的。': 'You can attach up to {0} images per message. Remove an image first.',
 '单张图片过大（{0}），请压缩到 {1} 以内再试。': 'This image is too large ({0}). Reduce it to {1} or less.',
 '本次附加的图片合计过大（上限 {0}），请减少张数或压缩后再试。': 'The images exceed the combined limit of {0}. Use fewer or smaller images.',
 '无法连接 AI 服务，请检查网络：{0}': 'Could not connect to the AI service. Check your network: {0}',
 '读取 AI 回复时中断：{0}': 'The response was interrupted: {0}',
 'AI 服务返回了无法解析的内容。': 'The AI service returned an unreadable response.',
 '请求失败，请稍后重试。': 'The request failed. Try again shortly.',
 '连接成功': 'Connection successful',
 '连接成功：{0}': 'Connection successful: {0}',
 '无法保存图片副本：{0}': 'Could not save the image copy: {0}',
 '无法读取图片 {0}，请确认文件未损坏。': 'Could not read {0}. Check that the image is not damaged.',
 '仅支持 .xlsx 或 .xls 文件：{0}': 'Only .xlsx and .xls workbooks are supported: {0}',
 '文件不存在：{0}': 'File not found: {0}',
 '无法解析文件 {0}：{1}': 'Could not read {0}: {1}',
 '附件内容过大，无法完整发送。请拆分表格、减少行数，或先用工具内的批处理功能缩小范围后重试。': 'The attachment is too large to send. Split the workbook or reduce its contents first.',
 '正在等待 AI 服务回复…': 'Waiting for the AI service…',
 '已附加表格，正在等待 AI 服务回复…': 'Spreadsheet attached. Waiting for a response…',
 '已附加图片，正在等待 AI 服务回复…': 'Image attached. Waiting for a response…',
 '已附加表格和图片，正在等待 AI 服务回复…': 'Files attached. Waiting for a response…',
 '发送后，问题、历史上下文和所附文件内容会传给所选 AI 服务。项目文件不会自动发送。': 'Sending shares your message, conversation context, and attachments with the selected AI service. Project files are not sent automatically.',
 '正在准备附件，可点击停止取消。': 'Preparing attachments. Click Stop to cancel.',
 '无法保存对话历史，请检查磁盘权限或删除不再需要的旧对话。': 'Could not save this conversation. Check disk permissions or delete old chats you no longer need.',
 '附件解析失败，请检查文件格式。': 'Could not prepare the attachment. Check the file format.',
 '问题过长，请缩短到 10000 字以内。': 'Your message is too long. Keep it under 10,000 characters.',
 '请分析所附文件。': 'Please analyze the attached files.',
 '已停止生成': 'Response stopped',
 '回复未完整生成，请缩小问题范围后重试。': 'The response is incomplete. Try a more focused question.',
 '回复过长，已停止接收。请缩小问题范围。': 'The response exceeded the size limit. Try a more focused question.',
 '连接提前结束，回复可能不完整。请重试。': 'The connection closed early. The response may be incomplete. Try again.',
 'AI 服务返回了过大的数据片段。': 'The AI service returned a response chunk that exceeded the size limit.',
 '流程核对': 'Workflow Check',
 '异动流程核对': 'Personnel Workflow Check',
 '异动与系统流程核对': 'Personnel Change and Workflow Check',
 '核对入职、离职流程与工具生成的异动汇总表，双向查漏并补齐空白，源文件不修改。': 'Compare onboarding and departure workflows with the generated change summary. Check both directions and fill blanks without modifying source files.',
 '系统入职 / 离职流程': 'Onboarding / Departure Workflows',
 '选择入职、离职流程文件': 'Select onboarding and departure workflow files',
 '开始核对': 'Run Check',
 '请选择同一事业部的流程导出文件和异动汇总表。重复流程及无法明确匹配的记录会单独列出，不自动选取。': 'Select workflow exports and the change summary for the same division. Duplicate or ambiguous workflows are listed for review, never automatically selected.',
 '工具生成的异动汇总表': 'Generated Change Summary',
 '核对月份（可选）': 'Check Month (optional)',
 '如 2026-07；留空按汇总表行内日期': 'e.g. 2026-07; leave blank to use summary row dates',
 '离职流程日期列': 'Departure Date Column',
 '离职日期（实际）': 'Actual Departure Date',
 '预计离职日期（确认后使用）': 'Expected Departure Date (confirm first)',
 '离职日期': 'Departure Date',
 '预计离职日期': 'Expected Departure Date',
 '公司对应（可选）': 'Company Mapping (optional)',
 '简称=完整公司名称；多组用分号分隔': 'Short name=full company name; separate entries with semicolons',
 '在结果副本中高亮补入字段和字段差异': 'Highlight filled fields and differences in the result copy',
 '核对设置有误': 'Invalid Check Settings',
 '适用：核对工具生成的异动汇总表与同一事业部的系统入职、离职流程。': 'Compare the generated change summary with onboarding and departure workflows from the same division.',
 '步骤：上方选择入职、离职流程文件，下方选择一份异动汇总表，点击“开始核对”。': 'Select workflow files above and one change summary below, then click Run Check.',
 '月份留空时，增员按汇总表入职日期、减员按离职日期分别确定月份，不按文件名推断。某类无日期记录时请填写核对月份。': 'If the month is blank, onboarding and departures use their respective summary row dates, not the file name. Enter a month if a category has no dated records.',
 '有流程状态列时自动排除未发起、退回；无状态列时按导入记录继续核对，并在运行日志提示未进行状态筛选；办结时间不作为状态依据。': 'When workflow status is available, Not Initiated and Returned are excluded automatically. Otherwise, imported records are checked as provided and the run log notes that status filtering was unavailable. Completion time is not a status.',
 '离职默认读取实际离职日期；若只有预计离职日期，先确认业务口径再切换日期列，工具不会自动替代。': 'Actual departure date is the default. If only an expected date is available, confirm the business rule before switching columns; substitution is never automatic.',
 '公司按全称或唯一的简称关键词对应；不唯一时填写“简称=全称”，多组用分号分隔。': 'Companies match by full name or unique short-name keywords. Resolve ambiguity with short name=full name, separating entries with semicolons.',
 '重复入职流程、姓名或工号冲突、日期缺失均列出核实；身份证脱敏或数字存储时不自动补齐。': 'Duplicate onboarding workflows, conflicting names or employee numbers, and missing dates are listed for review. Masked or numeric-stored IDs do not trigger automatic filling.',
 '结果：单独生成核对报告和汇总表副本。双向缺失、字段差异写入预警明细；仅明确匹配的空白字段从流程补入，不增加或删除人员、不覆盖已有值和公式、不改源文件。': 'Outputs are a check report and a summary copy. Missing records in either direction and field differences are reported. Only unambiguously matched blanks are filled; people, existing values, formulas, and source files are preserved.',
 '学历、学校、专业读取最高学历信息，岗位读取岗位，家庭住址读取户籍地址；补入记录保留字段和来源，关闭高亮也能查看。': 'Education, school, and major use the highest qualification; job and registered address supply the corresponding fields. The fill log records fields and sources even when highlighting is off.',
 '将文件的完整原名称与 Excel 中的原文件名列匹配，使用同一行的新名称。': 'Match each full original name to the original-name column in Excel, then use the new name from the same row.',
 '按 Excel 行顺序分配名称，可在预览中调整对应关系。': 'Assign names in Excel row order. You can adjust the assignments in Preview.',
 '请先选择缴费清单、压缩包或文件夹。': 'Select payment lists, archives, or a folder first.',
 '请先选择考勤 / 周报 / 月报文件、压缩包或文件夹。': 'Select attendance files, weekly or monthly reports, archives, or a folder first.',
 '目前没有可用的新版本。': "You're running the latest version.",
 '新建': 'New',
 '当前项目': 'Current Project',
 '社保汇总': 'Contribution Summary',
 '列名在第 {0} 行': 'Headers on row {0}',
 '[文件夹] ': '[Folder] ',
 '[文件] ': '[File] ',
 '第 {0} 列': 'Column {0}','操作未完成': 'Operation Incomplete',
 '支持 .xlsx / .xls / ZIP / RAR / 7Z / TAR / 文件夹 · 可多选': '.xlsx / .xls / ZIP / RAR / 7Z / TAR / folders · '
                                                       'Multiple selections',
 '支持 .xlsx / .xls · 单个文件': '.xlsx / .xls · One file',
 '支持按人员文件夹查找，也支持从无序平铺资料库建立 OCR 索引后按人员检索。': 'Search employee folders, or build an OCR index to find employees '
                                           'in an unorganized flat library.',
 '收起': 'Collapse',
 '收起原表': 'Hide Source',
 '收起左侧栏': 'Collapse Sidebar',
 '收起项目文件': 'Hide Project Files',
 '改名预览格式无效，请重新预览。': 'The rename preview format is invalid. Generate a new preview.',
 '数据所在页': 'Data Worksheet',
 '数据排列方式：': 'Data layout:',
 '数据读取方式': 'Reading Mode',
 '数量不一致、姓名无效、目标重名或目标已存在时会在预览中明确提醒；未配对或冲突项目不会改名，也不会覆盖。': 'Preview identifies count mismatches, invalid names, '
                                                        'duplicates, and existing targets. Unassigned or '
                                                        'conflicting items are not renamed or overwritten.',
 '整理完成': 'Cleanup Complete',
 '文件': 'File',
 '文件夹': 'Folder',
 '文件类型': 'File Type',
 '文件：': 'File:',
 '文字替换只处理第一层，沿用类型筛选并忽略以 . 或 ~$ 开头的项目；“全部”包含任意扩展名文件。目标重名或无效时，先在完整预览中修正或排除；不会覆盖未参与改名的项目。': 'Text replacement '
                                                                                         'processes the '
                                                                                         'first level only, '
                                                                                         'respects the type '
                                                                                         'filter, and '
                                                                                         'ignores names '
                                                                                         'starting with . or '
                                                                                         '~$. All includes '
                                                                                         'every file '
                                                                                         'extension. Resolve '
                                                                                         'or exclude invalid '
                                                                                         'or conflicting '
                                                                                         'names in preview; '
                                                                                         'unselected items '
                                                                                         'are never '
                                                                                         'overwritten.',
 '文档（doc/xls/ppt/txt等）': 'Documents (doc/xls/ppt/txt, etc.)',
 '新名称': 'New Name',
 '新名称列（可选）': 'New Name Column (optional)',
 '新增“地区编号维护”，自定义编号只保存在当前项目；同编号或同地区优先使用自定义配置，删除后恢复内置规则。': 'Added project-specific region codes. Custom codes '
                                                         'override matching built-in codes; deleting them '
                                                         'restores defaults.',
 '新增「公出」列': 'Add Business Duty column',
 '新增「出差」列': 'Add Business Trip column',
 '新建工作项目': 'New Project',
 '新建或打开项目后开始处理': 'Create or open a project to get started',
 '新建项目': 'New Project',
 '新版本为 v': 'New version: v',
 '新版本已准备好，请先点击左下角“重启以更新”。': 'The update is ready. Click Restart to Update at the bottom left.',
 '新版本第一次打开时显示更新内容，也可通过“更新记录”随时查看。': 'Release notes appear on first launch after an update and remain '
                                    'available in Release Notes.',
 '无序平铺资料库（OCR 索引）': 'Unorganized Flat Library (OCR Index)',
 '无法{0}项目': 'Could not {0} project',
 '无法保存': 'Could Not Save',
 '无法准备处理': 'Could Not Prepare Processing',
 '无法创建项目': 'Could Not Create Project',
 '无法删除材料': 'Could Not Delete Material Type',
 '无法删除预设': 'Could Not Delete Preset',
 '无法加载应用图标。': 'Could not load the app icon.',
 '无法恢复自动识别': 'Could Not Restore Automatic Detection',
 '无法打开结果': 'Could Not Open Results',
 '无法打开资料': 'Could Not Open Files',
 '无法打开项目': 'Could Not Open Project',
 '无法放入此区域：\n': 'Cannot drop here:\n',
 '无法更新预设': 'Could Not Update Preset',
 '无法移到项目回收站：{0}': 'Could not move to project Trash: {0}',
 '无法识别绝对文件路径，请重新选择文件。': 'The absolute file path could not be recognized. Select the file again.',
 '无法重新识别列头': 'Could Not Detect Headers Again',
 '日期填写有误': 'Invalid Dates',
 '旧版或跳过记录可直接删除；重新处理文件时再选择。': 'Legacy and skipped mappings can be deleted directly. Select them again when '
                             'reprocessing files.',
 '旧版记录': 'Legacy History',
 '暂不支持': 'Not Supported Yet',
 '暂不更新': 'Not Now',
 '暂无完整结果': 'No Complete Results',
 '暂时无法检查资料，请使用点击选择。': 'Files cannot be checked right now. Use Browse instead.',
 '暂时无法检查资料，请稍后重试。': 'Files cannot be checked right now. Try again later.',
 '更换': 'Change',
 '更新下载失败': 'Update Download Failed',
 '更新下载已取消': 'Update Download Canceled',
 '更新内容，可上下滚动': 'Release notes; scroll to read',
 '更新前可以查看本次新增和修复的内容。': 'Review new features and fixes before updating.',
 '更新前可查看本次更新内容，新版本首次打开会显示更新说明，并可通过“更新记录”随时回看。': 'Review changes before updating. Notes also appear when the '
                                                'new version first opens and remain available in Release '
                                                'Notes.',
 '更新失败': 'Update Failed',
 '更新文件已失效，将重新检查更新': 'The update file is no longer valid. Checking again.',
 '更新程序启动失败': 'Could Not Start Updater',
 '更新花名册': 'Update Roster',
 '更新记录': 'Release Notes',
 '替换': 'Replace',
 '替换为': 'Replace With',
 '替换指定文字': 'Replace Text',
 '替换指定文字：按所选文件类型批量替换名称中的原文字，例如“劳动合同”改为“资金合同”；文件扩展名和内容保持不变，区分大小写并替换所有匹配文字。': 'Replace Text: replace part of '
                                                                            'each name for the selected file '
                                                                            'type, such as Employment '
                                                                            'Contract with Funding Contract. '
                                                                            'Extensions and contents are '
                                                                            'unchanged. Matching is '
                                                                            'case-sensitive and all '
                                                                            'occurrences are replaced.',
 '最大化或还原': 'Maximize or Restore',
 '最小化': 'Minimize',
 '最新版本 {0} · {1}（64 位）\n可直接粘贴发给同事下载。\n\n请务必按接收方电脑的系统使用对应链接：\nWindows 7 必须使用 Win7 安装包，切勿下载或安装 Win10/11 安装包。\nWindows 10/11 请使用对应的 Win10/11 安装包。\n\n此处仅提供 Windows 安装包；Mac 及其他系统的安装包，请联系管理员获取。': 'Latest '
                                                                                                                                                                                              'version '
                                                                                                                                                                                              '{0} '
                                                                                                                                                                                              '· '
                                                                                                                                                                                              '{1} '
                                                                                                                                                                                              '(64-bit)\n'
                                                                                                                                                                                              'Paste '
                                                                                                                                                                                              'this '
                                                                                                                                                                                              'link '
                                                                                                                                                                                              'to '
                                                                                                                                                                                              'share '
                                                                                                                                                                                              'it '
                                                                                                                                                                                              'with '
                                                                                                                                                                                              'a '
                                                                                                                                                                                              'colleague.\n'
                                                                                                                                                                                              '\n'
                                                                                                                                                                                              'Choose '
                                                                                                                                                                                              'the '
                                                                                                                                                                                              'installer '
                                                                                                                                                                                              'for '
                                                                                                                                                                                              'the '
                                                                                                                                                                                              "recipient's "
                                                                                                                                                                                              'computer:\n'
                                                                                                                                                                                              'Windows '
                                                                                                                                                                                              '7 '
                                                                                                                                                                                              'requires '
                                                                                                                                                                                              'the '
                                                                                                                                                                                              'Win7 '
                                                                                                                                                                                              'installer; '
                                                                                                                                                                                              'do '
                                                                                                                                                                                              'not '
                                                                                                                                                                                              'use '
                                                                                                                                                                                              'the '
                                                                                                                                                                                              'Windows '
                                                                                                                                                                                              '10/11 '
                                                                                                                                                                                              'installer.\n'
                                                                                                                                                                                              'Windows '
                                                                                                                                                                                              '10/11 '
                                                                                                                                                                                              'requires '
                                                                                                                                                                                              'the '
                                                                                                                                                                                              'Windows '
                                                                                                                                                                                              '10/11 '
                                                                                                                                                                                              'installer.\n'
                                                                                                                                                                                              '\n'
                                                                                                                                                                                              'Only '
                                                                                                                                                                                              'Windows '
                                                                                                                                                                                              'installers '
                                                                                                                                                                                              'are '
                                                                                                                                                                                              'provided '
                                                                                                                                                                                              'here. '
                                                                                                                                                                                              'Contact '
                                                                                                                                                                                              'your '
                                                                                                                                                                                              'administrator '
                                                                                                                                                                                              'for '
                                                                                                                                                                                              'macOS '
                                                                                                                                                                                              'or '
                                                                                                                                                                                              'other '
                                                                                                                                                                                              'systems.',
 '最近30天': 'Last 30 Days',
 '最近7天': 'Last 7 Days',
 '最近项目': 'Recent Projects',
 '月份规则：增员看入职日期，减员看离职日期，转正看转正日期，调动看调整日期。': 'Month assignment: additions use hire dates, departures use '
                                          'termination dates, confirmations use confirmation dates, and '
                                          'transfers use effective adjustment dates.',
 '月报（可选）': 'Monthly Reports (optional)',
 '未取得可用的本地文件路径；网页或未下载附件请先保存到本地。': 'No usable local path was received. Save web files or attachments locally '
                                  'first.',
 '未处理工作表：': 'Unprocessed worksheets:',
 '未完成': 'Incomplete',
 '未开始': 'Not Started',
 '未归档上传资料': 'Source Files Not Archived',
 '未打开工作项目': 'No Project Open',
 '未生成完整结果': 'No Complete Results Generated',
 '未知界面工具：{0}:{1}': 'Unknown UI tool: {0}:{1}',
 '未能删除选择': 'Could Not Delete Mapping',
 '未能复制下载地址': 'Could Not Copy Download Link',
 '未选择': 'Not selected',
 '未选择材料': 'No Material Types Selected',
 '本周': 'This Week',
 '本地处理 · 不上传数据': 'Local processing · No data uploads',
 '本月': 'This Month',
 '本次不合并这一类文件（结果中会列明）': 'Skip this file type for this run (listed in the results)',
 '本次不读取': 'Skip for This Run',
 '本次为必要更新；不更新将退出程序。': 'This update is required. The app will exit if you decline.',
 '本次处理已安全停止。': 'Processing stopped safely.',
 '本次处理已安全结束，未完成批次可在项目中追溯。': 'Processing ended safely. Unfinished batches remain traceable in the project.',
 '本次文件确认': 'Review Current Files',
 '本次更新': 'This Update',
 '本次未添加，原选择保持不变。\n': 'Nothing was added. The previous selection is unchanged.\n',
 '本次检查已取消，原选择保持不变。': 'Check canceled. The previous selection is unchanged.',
 '本次模板（相同模板只需确认一次）': 'Templates in This Run (review each layout once)',
 '本次没有这类工作表': 'No worksheet of this type for this run',
 '本次跳过这个文件（结果中会列明）': 'Skip this file for this run (listed in the results)',
 '本次选择不会保存到下次。': 'These choices will not be saved for future runs.',
 '本次选择的资料': 'Selected Files',
 '材料已删除': 'Material Type Deleted',
 '材料已添加': 'Material Type Added',
 '松开后{0}：{1}': 'Release to {0}: {1}',
 '查找': 'Search',
 '查找已移除的批次': 'Search removed batches',
 '查找当前资料中的名称，最多显示 100 项': 'Search names in these files; up to 100 results',
 '查找需要对应的内容': 'Find fields to map',
 '查看升级前保存的上传资料和结果；新处理记录请在项目文件中查看。': 'View source files and results saved before the upgrade. New processing '
                                    'records are in Project Files.',
 '查看原表 / 调整行号': 'View Source / Change Header Row',
 '查看已识别和其他可选列': 'Show recognized and optional columns',
 '查看未完成项': 'Show Incomplete Items',
 '校验待恢复项目位置失败': 'Could not verify the project recovery location',
 '核对选择': 'Review Choices',
 '格式不支持': 'Unsupported Format',
 '档案入库': 'Import Archive Records',
 '档案入库与档案表': 'Archive Import & Company Records',
 '档案汇总表': 'Archive Summary',
 '档案移交表': 'Archive Transfer Files',
 '档案表生成': 'Generate Company Archives',
 '检查更新': 'Check for Updates',
 '检查更新失败': 'Update Check Failed',
 '模板 ': 'Template ',
 '模板列名确认窗口新增“已记住的选择”，可查看、修改或删除已记住的列名选择；直接确认时默认仅本次文件生效。': 'Added Saved Mappings to column review, with '
                                                         'editing and deletion. Unsaved choices apply to the '
                                                         'current files only.',
 '模板设置': 'Template Settings',
 '正在下载或校验更新，暂不能开始工具处理，请等待完成后重启以更新。': 'An update is downloading or being verified. Wait for it to finish, '
                                     'then restart to update before processing files.',
 '正在下载更新': 'Downloading Update',
 '正在下载更新…': 'Downloading update…',
 '正在准备 v{0}…': 'Preparing v{0}…',
 '正在准备并检查资料…': 'Preparing and checking files…',
 '正在准备更新…': 'Preparing update…',
 '正在准备重启…': 'Preparing to restart…',
 '正在准备项目资料，总量尚未确定': 'Preparing project files; total workload is not known yet',
 '正在取消…': 'Canceling…',
 '正在取消下载，请稍候…': 'Canceling download. Please wait…',
 '正在取消更新…': 'Canceling update…',
 '正在处理…': 'Processing…',
 '正在处理或保存项目资料，请稍后再添加。': 'Processing or saving project files. Add files after it finishes.',
 '正在安全停止…': 'Stopping safely…',
 '正在安全结束后台任务并关闭…': 'Finishing background tasks safely before closing…',
 '正在打开安装程序…': 'Opening installer…',
 '正在整理历史记录，请稍候…': 'Organizing history. Please wait…',
 '正在校验更新…': 'Verifying update…',
 '正在校验更新文件…': 'Verifying update files…',
 '正在检查上一批资料，请稍后再拖入。': 'The previous selection is being checked. Wait before dropping more files.',
 '正在检查工资表列头；不会修改原表。': 'Checking payroll headers. Source workbooks are unchanged.',
 '正在检查所选资料…': 'Checking selected files…',
 '正在检查更新': 'Checking for Updates',
 '正在检查更新…': 'Checking for updates…',
 '正在检查更新文件…': 'Checking update files…',
 '正在检查资料': 'Checking Files',
 '正在检查资料类型，请稍候再松手…': 'Checking file types. Hold before releasing…',
 '正在生成改名预览…': 'Generating rename preview…',
 '正在确定工作量': 'Determining workload',
 '正在获取地址…': 'Getting link…',
 '正在读取旧版记录…': 'Loading legacy history…',
 '正在读取详情…': 'Loading details…',
 '正在读取，请稍候…': 'Loading. Please wait…',
 '正在连接下载地址…': 'Connecting to download…',
 '正在重启…': 'Restarting…',
 '此名称已经添加。': 'This name has already been added.',
 '此处仅提供 Windows 安装包；Mac 及其他系统的安装包，请联系管理员获取。\n每次获取最新版地址，复制后可直接分享。': 'Only Windows installers are provided '
                                                                   'here. Contact your administrator for '
                                                                   'macOS or other systems.\n'
                                                                   'Each request retrieves the latest link, '
                                                                   'ready to copy and share.',
 '此文件需要处理后重新选择，不能跳过': "Resolve this file's issues and select it again. It cannot be skipped.",
 '此版本尚未提供更新记录。': 'Release notes are not available for this version.',
 '步骤：先打开工作项目，选择工资表文件，再点击“开始拆分”。': 'Open a project, select a payroll workbook, and click Split.',
 '步骤：可选择单个异动表、多个异动表、常见压缩包，或包含这些文件的文件夹。': 'Select one or more personnel-change workbooks, archives, or a '
                                         'folder containing them.',
 '步骤：可选择单个月度工资表、多个工资表、常见压缩包，或包含这些文件的文件夹。': 'Select one or more monthly payroll workbooks, archives, or a '
                                           'folder containing them.',
 '步骤：可选择单个移交表、多个移交表、常见压缩包，或包含这些文件的文件夹。': 'Select one or more archive-transfer workbooks, archives, or a '
                                         'folder containing them.',
 '步骤：选择单个保单清单、多个清单、常见压缩包，或包含清单的文件夹；再选择人力资源分析表。': 'Select policy lists, archives, or a folder, then select '
                                                 'the HR analysis workbook.',
 '步骤：选择单个异动汇总表、多个汇总表，或包含汇总表的文件夹；再选择人力资源花名册。': 'Select personnel-change summaries or a folder, then select '
                                              'the employee roster.',
 '步骤：选择单个文件、多个文件、常见压缩包，或包含这些文件的文件夹。': 'Select one or more files, archives, or a folder containing them.',
 '步骤：选择单个缴费清单、多个清单、常见压缩包，或包含清单的文件夹；再选择参保人员花名册。': 'Select payment lists, archives, or a folder, then select '
                                                 'the insured employee roster.',
 '步骤：选择员工资料库根目录，在第二行选择员工名单表格（Excel），勾选需要的材料类型后点击“开始打包”。': 'Select the employee library folder and an Excel '
                                                          'roster, choose material types, then click Package '
                                                          'Materials.',
 '步骤：选择档案汇总表文件、多个文件、常见压缩包，或包含汇总表的文件夹。': 'Select archive-summary workbooks, archives, or a folder containing '
                                        'them.',
 '每人一行': 'One row per employee',
 '每天一条考勤记录': 'One attendance record per day',
 '没有可添加的本地资料，请先保存到本地后再拖入。': 'No local files can be added. Save them locally before dropping them here.',
 '没有可确认的工资模板，请检查下方文件提示，或返回重新选文件。': 'No payroll template is ready for review. Check the file notices below or '
                                   'go back and select the files again.',
 '没有找到旧版记录。新处理的资料和结果请在“项目文件”中查看。': 'No legacy history found. New files and results are in Project Files.',
 '没有找到相关记录，可以清除查找内容或更换筛选条件。': 'No matching records. Clear the search or change the filters.',
 '没有新版本': "You're Up to Date",
 '没有选择材料': 'No Material Types Selected',
 '沿用系统自动识别': 'Use Automatic Detection',
 '注意：不会清空原花名册；身份证已存在的增员不会重复写入，找不到的减员会在日志提醒。': 'The existing roster is retained. Additions with existing ID '
                                              'numbers are not duplicated; unmatched departures are reported '
                                              'in the log.',
 '注意：人力资源分析表需包含“花名册”工作表；花名册在职但保单没有会提示需加保，保单有但花名册没有或已标记离职会提示需减保。': 'The HR analysis workbook must contain an '
                                                                  'employee roster worksheet. Active '
                                                                  'employees missing from a policy are '
                                                                  'flagged for enrollment; policyholders '
                                                                  'missing from the roster or marked as '
                                                                  'departed are flagged for removal.',
 '注意：公司档案表会自动改公司名，新增行会补边框、居中和公式。': 'Company names are updated automatically in company archives. New rows '
                                   'receive borders, alignment, and formulas.',
 '注意：公积金、残保金、管理费暂无数据时留空；账单识别结果与花名册不一致时会提醒。': 'Housing fund, disability employment fund, and management fees '
                                             'stay blank when unavailable. Differences between detected '
                                             'bills and the roster are reported.',
 '注意：只处理增补表、离职、转正、调整；薪酬、产值和同行对比分析暂不处理。': 'Only additions, departures, employment confirmations, and '
                                         'adjustments are processed. Compensation, output value, and peer '
                                         'comparisons are not processed.',
 '注意：周月报异常只统计次数和明细，不计算扣款金额。': 'Weekly and monthly report exceptions include counts and details, without '
                              'calculating deductions.',
 '注意：工资表文件名或表内日期要能识别月份；重复人员或重复月份会在执行结果里提醒。': 'The month must be recognizable from the payroll filename or '
                                             'workbook dates. Duplicate employees or months are reported in '
                                             'the results.',
 '注意：源工资表不会被修改；如果模板列名或表结构变化，先发给开发确认。': 'Source payroll workbooks are unchanged. Contact the developer before '
                                       'using a changed header layout or template structure.',
 '注意：编号会从文件名或表头标题识别项目地区，如“茂名项目部”自动填 11；识别不到会留空并提醒。': 'Region codes are detected from filenames or header '
                                                     'titles. If the region cannot be detected, the code '
                                                     'stays blank and a notice is shown.',
 '浅色': 'Light',
 '浏览文件 · 选择文件夹': 'Browse Files · Select Folder',
 '深色': 'Dark',
 '添加': 'Add',
 '添加为待处理资料': 'Add as Pending Input',
 '添加文件 / 压缩包': 'Add Files / Archives',
 '添加文件夹': 'Add Folder',
 '添加材料': 'Add Material Type',
 '添加自定义名称，例如名字、name': 'Add a custom alias, such as Name or Employee Name',
 '添加自定义材料': 'Add Custom Material Type',
 '添加页名，例如1、2、增员表': 'Add a worksheet name, such as 1, 2, or Additions',
 '清空': 'Clear',
 '清除': 'Clear',
 '源文件不改；首次建立隐藏索引，未变化文件直接复用': 'Source files are unchanged. A hidden index is created once; unchanged files '
                             'reuse it.',
 '点击“下载更新”后会打开下载地址，请按安装提示完成更新。': 'Download Update opens the download page. Follow the installation '
                                 'instructions to update.',
 '点击“开始合并”后，结果会保存到当前工作项目，源文件请自行保管。': 'Click Merge to save results to the current project. Keep your source '
                                     'files.',
 '点击“开始汇总”后，结果会保存到当前工作项目，源文件请自行保管。': 'Click Consolidate to save results to the current project. Keep your '
                                     'source files.',
 '点击“打开所在文件夹”可直接查看本次生成的结果目录。': "Open the containing folder to view this run's results.",
 '点击“更新花名册”后，结果会保存到当前工作项目，源文件请自行保管。': 'Click Update Roster to save results to the current project. Keep your '
                                      'source files.',
 '点击浏览文件': 'Click to browse files',
 '点击浏览文件夹路径': 'Click to browse folders',
 '点选写着列名的那一行': 'Select the row containing column headers',
 '照片人员归属冲突，未提取：': 'Photo ownership is conflicting; not retrieved:',
 '独立后台进程不可用，已自动切换兼容后台模式继续处理。': 'The separate background process is unavailable. Processing continues in '
                               'compatibility mode.',
 '独立进程': 'separate process',
 '生成 ZIP 压缩包': 'Create ZIP Archive',
 '生成台账': 'Generate Ledger',
 '生成报表': 'Generate Reports',
 '生成档案表': 'Generate Company Archives',
 '生成统计': 'Generate Statistics',
 '生效名称：': 'Active aliases:',
 '用当前勾选更新预设': 'Update Preset from Selection',
 '用户已确认：': 'User confirmed:',
 '界面与布局': 'Interface & Layout',
 '留空使用“原文件名”列': 'Leave blank to use the original-name column',
 '留空使用“新名称”列': 'Leave blank to use the new-name column',
 '留空处理所选文件类型的全部项目': 'Leave blank to process all items of the selected type',
 '目前规则：按身份证关联花名册；费用所属期优先读取明细行和原文件名，文件夹或压缩包名称只辅助识别缴纳地和缴纳单位。': 'Employees are matched to the roster by ID '
                                                             'number. Payment periods come from detail rows '
                                                             'and original filenames; folder and archive '
                                                             'names only help identify payment locations and '
                                                             'organizations.',
 '目标人员': 'Target Employees',
 '相对路径：': 'Relative path:',
 '知道了': 'Got It',
 '确定': 'OK',
 '确定删除自定义材料“{0}”吗？{1}': 'Delete custom material type “{0}”?{1}',
 '确定删除自定义预设“{0}”吗？\n\n材料本身不会被删除。': 'Delete custom preset “{0}”?\n'
                                   '\n'
                                   'The material types themselves will not be deleted.',
 '确认': 'Confirm',
 '确认修改': 'Confirm Changes',
 '确认全部并继续处理': 'Confirm All and Continue',
 '确认列名': 'Confirm Columns',
 '确认删除材料': 'Delete Material Type?',
 '确认删除预设': 'Delete Preset?',
 '确认工作表': 'Confirm Worksheets',
 '确认并执行此方案': 'Confirm and Run This Plan',
 '确认并继续处理': 'Confirm and Continue',
 '确认本次跳过': 'Confirm Skip for This Run',
 '确认跳过并继续': 'Skip and Continue',
 '确认这张工作表不需要处理': 'Confirm this worksheet does not need processing',
 '社保、保险、考勤、工资、异动和档案工具统一提供“模板适配”入口，遇到列名或工作表名称不一致时，可预览原表并手动选择对应内容。': 'Template Mapping is available across '
                                                                   'insurance, attendance, payroll, '
                                                                   'personnel-change, and archive tools. '
                                                                   'Preview the source and select the '
                                                                   'correct fields when column or worksheet '
                                                                   'names differ.',
 '社保与保险': 'Social Insurance',
 '社保明细与汇总': 'Social Insurance Details & Summary',
 '社保明细表新增“补充工伤补差”的基数、比例和金额三列，并计入单位补差合计。': 'Added base, rate, and amount columns for supplemental work-injury '
                                          'insurance adjustments, included in employer adjustment totals.',
 '社保缴费清单': 'Social Insurance Payment Lists',
 '移入：': 'Move into:',
 '移到回收站': 'Move to Trash',
 '移到项目回收站': 'Move to Project Trash',
 '移除': 'Remove',
 '窗口较窄，项目文件将在放大后恢复；点击取消恢复': 'The window is narrow. Project Files will return when resized wider; click to '
                            'cancel.',
 '第 ': 'Row ',
 '第 {0} / {1} 页': 'Page {0} of {1}',
 '筛选原表中的列': 'Filter Source Columns',
 '简体中文': '简体中文',
 '系统会核对完整清单并恢复到原业务目录；如有同名批次会自动使用新名称。': 'The full manifest is verified before restoring to the original '
                                       'business folder. A new name is used if a batch with the same name '
                                       'exists.',
 '系统内置名称始终保留，不能取消、修改或删除。你添加的名称可以修改、删除，点击底部保存后生效；取消则不保存本次修改。同一工具的不同项目共用，不改原文件。': 'Built-in names are always '
                                                                                'retained and cannot be '
                                                                                'changed. Custom aliases can '
                                                                                'be edited or deleted; Save '
                                                                                'applies changes and Cancel '
                                                                                'discards them. Aliases are '
                                                                                'shared across projects for '
                                                                                'the same tool and do not '
                                                                                'change source files.',
 '系统剪贴板暂不可用': 'Clipboard Unavailable',
 '系统原有工作表识别始终保留；自定义名称作为补充。': 'Built-in worksheet detection is always retained. Custom names extend it.',
 '结果位置': 'Results Location',
 '结果已安全保存到当前项目。': 'Results were saved safely to the current project.',
 '结果文件已不存在，请打开结果目录查看。': 'The result file no longer exists. Open the results folder to check.',
 '结果：': 'Results:',
 '结果：按“公司”写入对应工作表；身份证已存在时不重复新增，只补充空白材料字段。': 'Records are written to company worksheets. Existing ID numbers '
                                            'are not duplicated; only blank material fields are filled.',
 '结果：按公司生成独立 Excel；已有身份证不重复新增，只补充空白字段。': 'A separate Excel archive is generated for each company. Existing '
                                         'ID numbers are not duplicated; only blank fields are filled.',
 '结果：按姓名、身份证号、月份合并；没有工资的月份填 0；已存在的人员月份不会覆盖。': 'Payroll is merged by name, ID number, and month. Months '
                                              'without pay are filled with 0; existing employee-month '
                                              'entries are not overwritten.',
 '前几列': 'Previous Columns',
 '功能不可用': 'Feature Unavailable',
 '功能更新': 'New Features',
 '加班/调休单位': 'Overtime / Time-Off Unit',
 '勾选需要处理的项目；直接编辑名称。文件扩展名保持不变。原件保留，结果另存至项目。': 'Select items to include and edit names directly. Extensions '
                                             'are preserved. Originals are kept; results are saved to the '
                                             'project.',
 '包含 ': 'Includes ',
 '历史记录不存在。': 'This history record no longer exists.',
 '历史记录已经整理完成，恢复或修复了 {0} 条记录。': 'History cleanup is complete. Recovered or repaired {0} records.',
 '历史记录暂时无法读取：{0}': 'History is temporarily unavailable: {0}',
 '原因：{0}': 'Reason: {0}',
 '原文件不会被修改。': 'Source files will not be modified.',
 '原文件名': 'Original Name',
 '原文件名 → 新名称映射表': 'Original Name → New Name Mapping',
 '原文件名列（可选）': 'Original Name Column (optional)',
 '原文字': 'Find Text',
 '原模式按姓名文件夹查找': 'Find folders by employee name',
 '原表内容示例：': 'Source examples:',
 '原表列太多？输入列名或内容，缩小下拉选项范围': 'Enter a column name or sample value to narrow the choices',
 '去除名称首尾空格': 'Trim leading and trailing spaces',
 '参保人员花名册': 'Insured Employee Roster',
 '双击可以打开文件；文件夹可展开查看。': 'Double-click to open a file. Expand folders to view their contents.',
 '发现新版本 v{0}': 'Version {0} is available',
 '取消': 'Cancel',
 '取消修改': 'Cancel Changes',
 '取消全选': 'Deselect All',
 '取消勾选「全部」后可按需勾选材料类型（如身份证、劳动合同等）': 'Uncheck All to select specific material types, such as IDs or employment '
                                   'contracts',
 '取消勾选「全部」后，可只提取指定材料；索引仍会覆盖整个资料库': 'Uncheck All to retrieve only selected material types. Indexing still '
                                   'covers the entire library.',
 '取消导入': 'Cancel Import',
 '取消资料检查': 'Cancel File Check',
 '取消项目文件自动恢复': 'Cancel Automatic Panel Restore',
 '另有 ': 'Also ',
 '另有资料待核对，请打开结果中的《资料待确认.xlsx》。': 'Some materials need review. Open the review workbook in the results '
                                 'folder.',
 '只处理所选目录第一层，原目录不会被修改': "Only the selected folder's first level is processed. The source folder is "
                        'unchanged.',
 '只确认工作表位置，不修改原文件。确认后会检查对应列；缺少资料的选择仅本次有效。': 'This confirms worksheet locations without changing the source. '
                                            'Columns will be checked next. Missing-data choices apply to '
                                            'this run only.',
 '可拖入': 'Drop ',
 '可选：留空时使用员工名单 Excel；填写时以此处人员为准': 'Optional: leave blank to use the Excel roster. Names entered here take '
                                  'priority.',
 '合同人员归属冲突，未提取：': 'Contract ownership is conflicting; not retrieved:',
 '合并连续空格和全角空格': 'Collapse repeated and full-width spaces',
 '同一项内容可保存多个名称，例如“姓名、名字、name”，下次使用自动识别，并支持修改、删除自定义名称，系统默认名称保持不变。': 'Save multiple aliases for a field to '
                                                                   'recognize it automatically next time. '
                                                                   'You can edit or delete custom aliases; '
                                                                   'built-in names remain unchanged.',
 '名称包含“明细”或“汇总”的原有识别规则始终保留': 'Existing detection based on detail or summary keywords is always retained',
 '名称已保存': 'Names saved',
 '名称未保存': 'Names not saved',
 '名称规则已保存': 'Naming rules saved',
 '名称规则未保存': 'Naming rules not saved',
 '名称规则未能保存，请重试': 'Could not save naming rules. Try again.',
 '后几列': 'Next Columns',
 '后台更新下载失败，稍后重试：{0}': 'Background update download failed; retrying later: {0}',
 '后台线程': 'background thread',
 '启用 OCR 缓存': 'Enable OCR cache',
 '启用缓存': 'Enable Cache',
 '员工名单 Excel（可选）': 'Employee Roster Excel (optional)',
 '员工资料库路径（只读检索）': 'Employee Library Folder (read-only)',
 '员工资料打包': 'Employee Materials',
 '员工资料智能检索与打包': 'Find & Package Employee Materials',
 '周报统计日期（可选）：填写如 2026-06-02 至 2026-06-30，只统计范围内周一截止的周报；留空按整月统计。适合 1 号正好是周一的月份，避免把上月最后一周重复统计。': 'Weekly '
                                                                                               'report dates '
                                                                                               '(optional): '
                                                                                               'enter a date '
                                                                                               'range to '
                                                                                               'include only '
                                                                                               'reports with '
                                                                                               'Monday '
                                                                                               'deadlines in '
                                                                                               'that range. '
                                                                                               'Leave both '
                                                                                               'dates blank '
                                                                                               'for the '
                                                                                               'whole month. '
                                                                                               'This helps '
                                                                                               'avoid '
                                                                                               'counting the '
                                                                                               'previous '
                                                                                               "month's "
                                                                                               'final week '
                                                                                               'again when '
                                                                                               'the month '
                                                                                               'begins on a '
                                                                                               'Monday.',
 '周报（可选）': 'Weekly Reports (optional)',
 '回收站': 'Trash',
 '回收站为空，或当前筛选没有匹配结果。': 'Trash is empty, or no items match the current filter.',
 '回收站暂时无法读取': 'Trash is temporarily unavailable',
 '固定展开左侧栏': 'Pin Sidebar',
 '图片（jpg/png/gif等）': 'Images (jpg/png/gif, etc.)',
 '地区名称': 'Region Name',
 '地区编号维护': 'Region Codes',
 '处理中': 'Processing',
 '处理失败': 'Processing Failed',
 '处理失败：': 'Processing failed:',
 '处理失败：{0}': 'Processing failed: {0}',
 '处理完成': 'Completed',
 '处理完成 · ': 'Completed · ',
 '处理完成，用时 {0} 秒（{1}）。': 'Completed in {0} seconds ({1}).',
 '处理尚未结束': 'Processing Is Still Running',
 '处理批次已恢复到当前项目，现有资料没有被覆盖。': 'The batch was restored to the current project. Existing files were not '
                            'overwritten.',
 '处理时间：{0}': 'Processed at: {0}',
 '处理结果：{0}': 'Results: {0}',
 '复制': 'Copy',
 '复制下载地址': 'Copy Download Link',
 '复制全部': 'Copy All',
 '复制全部记录': 'Copy All Records',
 '复制失败': 'Copy Failed',
 '复制最新版安装包地址，发给同事下载': 'Copy the latest installer link to share with a colleague',
 '外观与语言': 'Appearance & Language',
 '多月工资合并': 'Merge Monthly Payroll',
 '失败': 'Failed',
 '夹': 'DIR',
 '好': 'OK',
 '如 2026-06-01': 'e.g. 2026-06-01',
 '如 2026-06-02': 'e.g. 2026-06-02',
 '如 2026-06-30': 'e.g. 2026-06-30',
 '如已有前几月汇总表，再选择“已有汇总表”；不选则新建一张汇总表。': 'Select an existing summary to add to previous months, or leave it '
                                     'blank to create a new summary.',
 '如已有月度汇总表，可选择单个汇总表或包含多个汇总表的文件夹；工具会按月份追加，原有记录不会清空。': 'Select a monthly summary or a folder containing '
                                                     'summaries to append by month. Existing records are '
                                                     'retained.',
 '如已有某个公司的档案表，可选择文件、常见压缩包或文件夹；不选或没匹配到时会按内置干净模板新建。': 'Select existing company archive files, an archive, or a '
                                                    'folder. Missing company archives are created from the '
                                                    'built-in blank template.',
 '如果同一文件夹里放了人力资源分析表，工具会自动更新其中的花名册。': 'If the same folder contains an HR analysis workbook, its employee '
                                     'roster is also updated automatically.',
 '如需统计未写周报/月报，请选择“应汇报人员名单”；不选时只能按文件中出现过的人推断。': 'Select an expected reporters roster to identify missing '
                                               'weekly or monthly reports. Without one, only people '
                                               'appearing in the source files can be inferred.',
 '姓名': 'Name',
 '姓名/原名称': 'Name / Original Name',
 '姓名/原名称（可选）': 'Name / Original Name (optional)',
 '姓名或身份证，多人用逗号隔开': 'Names or ID numbers, separated by commas',
 '安全说明：确认后会先把所选文件夹复制进当前项目，再在“处理结果”的副本上改名；电脑上的原文件夹不会被修改。': 'The selected folder is copied into the current '
                                                          'project before renaming the results copy. The '
                                                          'source folder on your computer is unchanged.',
 '安全说明：纯本地处理、不上传外网；源文件不会修改，OCR 索引模式只会新增隐藏缓存文件。': 'Processing is local and does not upload files. Source '
                                                 'files are unchanged; OCR indexing adds only a hidden '
                                                 'cache.',
 '安装更新': 'Install Update',
 '安装程序已启动，正在关闭当前版本…': 'The installer has started. Closing the current version…',
 '完成': 'Done',
 '完成后在处理结果中保存改名记录和 CSV 清单。执行中出错或停止时尝试安全恢复；若无法全部恢复，请保留结果目录和记录，不要手动删除临时项目。': 'The results include a rename log '
                                                                           'and CSV receipt. Errors or '
                                                                           'cancellation trigger a safe '
                                                                           'rollback attempt. If rollback is '
                                                                           'incomplete, keep the results '
                                                                           'folder and logs, including '
                                                                           'temporary items.',
 '完整处理批次已移到当前项目回收站，之后可以恢复。': "The entire batch was moved to this project's Trash and can be restored later.",
 '完整预览：查看全部原名称、新名称、相对路径和问题；可搜索、筛选、排除项目，直接编辑每项名称。全部已选项目校验通过后执行确认方案。': 'Review the entire plan with original '
                                                                     'names, proposed names, paths, and '
                                                                     'issues. Search, filter, exclude items, '
                                                                     'or edit names. Confirmed changes '
                                                                     'execute only after all included items '
                                                                     'pass validation.',
 '定位': 'Go To',
 '定位问题': 'Show Issues',
 '容易疑惑1：如果某人上一期已经交过周报，周二到周四又交了一份，这份算他提前交的下一期，不记超时，下一期也不会记未写。': 'If someone already submitted the previous '
                                                               'weekly report, a new submission from Tuesday '
                                                               'through Thursday counts as an early report '
                                                               'for the next period, not a late report. The '
                                                               'next period will not be marked missing.',
 '容易疑惑2：选了统计日期时，归属期超出范围的周报本次不统计、留给下一次。比如范围选到6.24，6.26（周五）交的属于6.29截止那期，本次不会出现。': 'When dates are selected, '
                                                                                'reports assigned to a '
                                                                                'deadline outside the range '
                                                                                'are left for a future run. '
                                                                                'For example, a June 26 '
                                                                                'submission assigned to the '
                                                                                'June 29 deadline is '
                                                                                'excluded from a range '
                                                                                'ending June 24.',
 '对应关系未保存': 'Mapping not saved',
 '对应关系未能保存，请重试': 'Could not save the mapping. Try again.',
 '对应列': 'Mapped Column',
 '对应设置已保存到当前项目。': 'The mapping was saved to the current project.',
 '导入未完成': 'Import Incomplete',
 '将此姓名映射上移': 'Move this name assignment up',
 '将此姓名映射下移': 'Move this name assignment down',
 '将连续横线和下划线统一为 _': 'Standardize repeated hyphens and underscores as _',
 '尚未打开项目': 'No project open',
 '展开项目文件': 'Show Project Files',
 '工作表或列名行已改变，请先点击“读取这些列名”。': 'The worksheet or header rows changed. Click Read Headers first.',
 '工作表设置': 'Worksheet Settings',
 '工作项目': 'Project',
 '工作项目已变化': 'Project Changed',
 '工具正在退出，暂不能添加资料。': 'The app is closing. Files cannot be added right now.',
 '工资明细': 'Payroll Details',
 '工资明细表': 'Payroll Detail Sheet',
 '工资表拆分': 'Split Payroll',
 '工资表按入职公司拆分': 'Split Payroll by Hiring Company',
 '工资表文件': 'Payroll Workbook',
 '已{0} {1} 项资料，当前共 {2} 项。': '{0} {1} items; {2} selected in total.',
 '已下载 {0} MB': 'Downloaded {0} MB',
 '已下载的更新文件缺失或不完整，工具将重新检查更新。': 'The downloaded update is missing or incomplete. Checking for updates again.',
 '已保存“{0}”。': 'Saved “{0}”.',
 '已停止': 'Stopped',
 '已停止，保留最后实际完成的进度。': 'Stopped. The last completed progress is retained.',
 '已删除自定义材料“{0}”。': 'Deleted custom material type “{0}”.',
 '已取消列头检查': 'Header review canceled',
 '已复制原件但未完成身份核对：': 'Original copied; identity not yet verified:',
 '已完成': 'Completed',
 '已完成核对，可以继续。': 'Review complete. You can continue.',
 '已恢复到项目': 'Restored to Project',
 '已打开下载地址': 'Download Page Opened',
 '已排除': 'Excluded',
 '已提取 {0} 个资料文件。': 'Retrieved {0} material files.',
 '已改名 {0} 项，排除 {1} 项，名称不变 {2} 项。原目录未修改。\n结果目录：{3}\n改名记录和清单已保存到本批次处理结果。': 'Renamed {0} items; excluded {1}; '
                                                                         'unchanged {2}. The source folder '
                                                                         'is unchanged.\n'
                                                                         'Results folder: {3}\n'
                                                                         'The rename log and receipt are '
                                                                         "saved with this batch's results.",
 '已有任务正在处理': 'A Task Is Already Running',
 '已有公司档案表（可选）': 'Existing Company Archive (optional)',
 '已有工资汇总表': 'Existing Payroll Summary',
 '已有档案汇总表可不选；不选时工具会用内置空模板新建一份汇总表。': 'An existing archive summary is optional. Without one, a new summary is '
                                    'created from the built-in blank template.',
 '已有档案汇总表（可选）': 'Existing Archive Summary (optional)',
 '已有汇总表': 'Existing Summary',
 '已有汇总表/文件夹（可选）': 'Existing Summary / Folder (optional)',
 '已有汇总表不能跳过，请完成其列头对应或取消选择该汇总表': 'An existing summary cannot be skipped. Complete its column mapping or '
                                'remove it from the selection.',
 '已有汇总表（可选）': 'Existing Summary (optional)',
 '已核对工作表选择及本次缺少的资料': 'I reviewed the worksheet selections and missing data for this run',
 '已核对本次全部模板及跳过的文件': 'I reviewed all templates and skipped files for this run',
 '已核对：读取方式和所选列的含义正确': 'I verified the reading mode and the meaning of each selected column',
 '已添加自定义材料“{0}”。': 'Added custom material type “{0}”.',
 '已清空选择，原文件未删除。': 'Selection cleared. Source files were not deleted.',
 '已用 ': 'Elapsed ',
 '已确认模板对应关系，继续处理。': 'Template mapping confirmed. Resuming processing.',
 '已移到旧版记录回收站。': 'Moved to legacy history Trash.',
 '已记住的选择': 'Saved Mappings',
 '已记住的选择（': 'Saved Mappings (',
 '已记住，可在“模板设置”中修改或删除。': 'Saved. You can edit or delete it in Template Settings.',
 '已设置': 'Configured',
 '已请求停止，正在安全结束…': 'Stop requested. Finishing safely…',
 '已请求停止，等待当前步骤安全退出…': 'Stop requested. Waiting for the current step to finish safely…',
 '已请求取消，等待当前路径检查退出…': 'Cancellation requested. Waiting for the current path check to finish…',
 '已跳过': 'Skipped',
 '已跳过不可用的更新缓存：{0}': 'Skipped unavailable cached update: {0}',
 '已选齐': 'Complete',
 '带入当前工具': 'Use in Current Tool',
 '常用名称对当前工具长期生效；如“222”含义会变，请使用本次文件确认。': "Saved aliases apply to future runs of this tool. If a name's "
                                        'meaning may change, confirm it for the current file only.',
 '常用组合': 'Presets',
 '应发工资': 'Gross Pay',
 '应汇报人员名单（可选）': 'Expected Reporters Roster (optional)',
 '应用': 'Apply',
 '开始{0}，请稍候…': 'Starting {0}. Please wait…',
 '开始入库': 'Import Records',
 '开始合并': 'Merge',
 '开始处理时，工具会自动检查已选择的资料。能识别的直接使用，需要你确认的会显示在这里。\n\n如果只是想添加、修改或删除列名，请切换到“常用名称管理”。': 'Selected files are checked '
                                                                                'when processing starts. '
                                                                                'Recognized fields are used '
                                                                                'automatically; fields '
                                                                                'needing review appear '
                                                                                'here.\n'
                                                                                '\n'
                                                                                'To add, edit, or delete '
                                                                                'column aliases, open Common '
                                                                                'Names.',
 '开始打包': 'Package Materials',
 '开始拆分': 'Split',
 '开始检查并处理': 'Check and Process',
 '开始汇总': 'Consolidate',
 '异动汇总': 'Personnel Changes',
 '异动汇总表': 'Personnel Changes Summary',
 '异动表文件': 'Personnel Changes Files',
 '异动表汇总': 'Consolidate Personnel Changes',
 '异动表汇总与花名册': 'Personnel Changes & Employee Roster',
 '归类方式：支持“按员工归类”（每人建一个文件夹）、“按材料归类”或“平铺输出”，可选自动生成 ZIP 压缩包。': 'Organize by employee (one folder per person), '
                                                            'by material type, or in a flat folder. ZIP '
                                                            'output is optional.',
 '当前任务或资料保存尚未结束，请完成后再点击重启以更新。': 'Wait for the current task or file save to finish before restarting to '
                                'update.',
 '当前功能': 'Current Tool',
 '当前功能只支持 .xlsx 或 .xls 文件。': 'This tool accepts .xlsx or .xls files only.',
 '当前功能只支持选择一个输入位置。': 'This tool accepts one input location only.',
 '当前功能尚未接入：{0}': 'This feature is not connected yet: {0}',
 '当前功能需要选择一个文件夹。': 'This tool requires a folder.',
 '当前处理或资料保存还没有完全结束。现在退出会先请求安全停止，并把未完成批次留待下次打开时恢复。是否仍要退出？': 'Processing or saving is still in progress. '
                                                           'Exiting will request a safe stop and leave '
                                                           'unfinished batches for recovery next time. Exit '
                                                           'anyway?',
 '当前处理状态已改变，请回到主界面重新开始处理。': 'The processing state changed. Return to the main screen and start again.',
 '当前工具或项目已改变，请重新开始处理': 'The tool or project changed. Start processing again.',
 '当前文件': 'Current File',
 '当前模式没有配套资料输入区。': 'This mode has no supporting-file input.',
 '当前模板还需要选择：': 'This template still needs:',
 '当前模板重复选择了同一列，姓名、身份证和金额必须分别选择。': 'The same column was selected more than once. Name, ID, and amount fields '
                                  'must use separate columns.',
 '当前版本：HR Toolkit v': 'Current version: HR Toolkit v',
 '当前范围还没有项目文件': 'No project files in this view',
 '当前规则：PZDX保额取“每人伤残死亡限额”，按万元显示；PEAC保额固定按60万元。': 'Insurance rules: PZDX coverage uses the per-person '
                                                'disability/death limit and is shown in units of 10,000 '
                                                'yuan. PEAC coverage is fixed at 600,000 yuan.',
 '当前规则：考勤公司默认“总部”；周报截止次周一17:00，周二至周四补交算上一期超时（备注写明提交时间），周五起交的算下一期；月报按次月2日17:01及以后算超时。': 'Attendance defaults '
                                                                                       'to Headquarters. '
                                                                                       'Weekly reports are '
                                                                                       'due Monday at 5:00 '
                                                                                       'PM; late '
                                                                                       'Tuesday–Thursday '
                                                                                       'submissions belong '
                                                                                       'to the previous '
                                                                                       'period, and Friday '
                                                                                       'onward to the next. '
                                                                                       'Monthly reports are '
                                                                                       'late from 5:01 PM on '
                                                                                       'the second day of '
                                                                                       'the next month.',
 '当前选中第 ': 'Selected row: ',
 '当前阶段进度': 'Current Stage Progress',
 '当前项目 / 原名称                         拟用名称（可编辑）                         映射顺序': 'Item / Original '
                                                                              'Name                         '
                                                                              'Proposed Name '
                                                                              '(editable)                         '
                                                                              'Assignment',
 '当前项目 / 本次处理结果': 'Current Project / Batch Results',
 '当前项目 · 只读': 'Current Project · Read-only',
 '当前项目只能查看': 'Project Is Read-only',
 '当前项目处于未恢复状态，写入已锁定。请重新打开当前项目以恢复状态。': 'The project has not recovered and is locked for writing. Reopen it to '
                                      'recover its state.',
 '当前项目处于未恢复状态，禁止切换到其他项目。请先重新打开当前项目以恢复状态。': 'Recover this project by reopening it before switching to another '
                                           'project.',
 '当前项目处于未恢复状态，禁止打开其他项目。请重新打开当前项目以恢复状态。': 'Recover this project by reopening it before opening another '
                                         'project.',
 '当前项目处于未恢复状态，禁止新建项目。请重新打开当前项目以恢复状态。': 'Recover this project by reopening it before creating a project.',
 '当前项目已达到 200 套对应设置，请先恢复不再使用模板的自动识别': 'This project has reached 200 saved mappings. Restore automatic '
                                      'detection for unused templates first.',
 '当前项目或任务状态已变化，请关闭后重新打开维护窗口。': 'The project or task state changed. Close and reopen this settings window.',
 '待改名': 'Ready to Rename',
 '待确认': 'Needs Review',
 '忽略无效 Qt smoke 尺寸：{0}': 'Ignored invalid Qt smoke size: {0}',
 '性能优化': 'Performance Improvements',
 '恢复到当前项目': 'Restore to Current Project',
 '恢复到项目': 'Restore to Project',
 '恢复没有完成': 'Restore Incomplete',
 '恢复自动识别': 'Restore Automatic Detection',
 '悬停展开，点击固定': 'Hover to expand; click to pin',
 '成功': 'Success',
 '所在工作表：': 'Worksheet:',
 '所有文件 (*)': 'All Files (*)',
 '打包设置': 'Packaging Options',
 '打开': 'Open',
 '打开上传资料': 'Open Source Files',
 '打开回收站': 'Open Trash',
 '打开工作项目': 'Open Project',
 '打开工作项目后才能查看项目回收站。': 'Open a project to view its Trash.',
 '打开工作项目失败': 'Could Not Open Project',
 '打开已有': 'Open Existing',
 '打开已有项目': 'Open Existing Project',
 '打开归档资料': 'Open Archived Files',
 '打开报表': 'Open Report',
 '打开结果': 'Open Results',
 '打开结果目录': 'Open Results Folder',
 '打开运行日志': 'Open Run Log',
 '打开项目': 'Open Project',
 '批量改名 · 完整预览': 'Batch Rename · Full Preview',
 '拖入的是快捷方式，请选择它指向的原文件。': 'This is a shortcut. Select the original file it points to.',
 '拖拽元数据：阶段={0}，URL数={1}，候选数={2}，格式={3}': 'Drag metadata: stage={0}, URLs={1}, candidates={2}, formats={3}',
 '拖拽未提供可用文件路径，请点击选择文件；未下载的附件请先保存到本地。': 'No usable file path was supplied. Select the file using Browse; save '
                                       'undownloaded attachments locally first.',
 '拖拽路径解码失败：{0}': 'Could not decode the dropped path: {0}',
 '拟用名称 ': 'Proposed Name ',
 '指定材料': 'Material Types',
 '按 Excel 人名顺序批量重命名': 'Rename in Excel Row Order',
 '按 Excel 人名顺序批量重命名：先按顺序生成方案；在完整预览中用上移/下移调整姓名分配，文件位置和扩展名不变。确认后不再按 Excel 重排。': 'Rename in Excel Row Order: '
                                                                              'generate a plan, then use '
                                                                              'Move Up/Down to reassign '
                                                                              'names. File positions and '
                                                                              'extensions stay unchanged. '
                                                                              'Execution uses the confirmed '
                                                                              'assignments without rereading '
                                                                              'Excel order.',
 '按 Excel 原文件名匹配': 'Match Excel by Original Name',
 '按 Excel 原文件名匹配：准备“原文件名”和“新名称”两列，按完整原文件名匹配而非行序；未匹配项目默认排除，可在预览中补充。': 'Match Excel by Original Name: provide '
                                                                     'original-name and new-name columns. '
                                                                     'Items match by full original filename, '
                                                                     'not row order. Unmatched items are '
                                                                     'excluded by default and can be edited '
                                                                     'in preview.',
 '按人员文件夹查找（原模式）': 'Employee Folders',
 '按功能或文件名查找': 'Search by tool or filename',
 '按周报记录读取': 'Read as Weekly Report Records',
 '按天': 'Days',
 '按小时': 'Hours',
 '按数据的排列方式选择': 'Choose the data layout',
 '按文件名查找': 'Search filenames',
 '按月报记录读取': 'Read as Monthly Report Records',
 '提示': 'Notice',
 '搜索原名称、新名称、路径或问题': 'Search original names, new names, paths, or issues',
 '操作': 'Action',
 '结果：按指定结构导出文件，并自动生成《员工资料提取汇总与缺失清单.xlsx》。': 'Materials are exported in the selected layout, with an employee '
                                            'extraction summary and missing-materials workbook.',
 '结果：根据汇总表里的增员写入花名册，根据减员在花名册中标记离职。': 'Roster updates add employees from the additions summary and mark '
                                     'departures from the removal summary.',
 '结果：每个入职公司生成一个 Excel，保留表头、格式、公式、小计和底部总计。': 'A separate Excel file is generated for each hiring company, '
                                            'preserving headers, formatting, formulas, subtotals, and '
                                            'totals.',
 '结果：生成“保险台账.xlsx”，包含保险台账和人员增减预警两个工作表。': 'An insurance workbook is generated with ledger and '
                                         'enrollment-change alert worksheets.',
 '结果：生成“社保明细表.xlsx”和“社保汇总表.xlsx”，汇总表里含基础数据分析和异常提醒。': 'Social insurance detail and summary workbooks are '
                                                     'generated, including basic analysis and exception '
                                                     'notices.',
 '结果：生成“考勤周月报汇总表.xlsx”，包含考勤统计、周月报统计、考勤异常明细、周月报异常明细。': 'An attendance and reports workbook is generated with '
                                                      'statistics and detailed attendance, weekly-report, '
                                                      'and monthly-report exceptions.',
 '统一各工具的圆角样式，优化更新下载动效，让界面/操作体验更好。': 'Standardized rounded corners and refined update animations for a more '
                                    'consistent interface.',
 '统一更新提示、下载和安装进度窗口；下载、校验、安装分别显示当前状态。': 'Unified update notifications and progress displays, with separate '
                                       'download, verification, and installation states.',
 '继续添加': 'Add More',
 '编号，如 01': 'Code, e.g. 01',
 '缺少人员名单': 'Employee Roster Required',
 '缺少员工信息': 'Employee Information Required',
 '缺少映射表': 'Mapping Workbook Required',
 '缺少输入': 'Input Required',
 '缺少配套文件': 'Supporting File Required',
 '考勤与周月报': 'Attendance & Reports',
 '考勤与周月报数据': 'Attendance & Report Data',
 '考勤与周月报统计': 'Attendance & Weekly/Monthly Reports',
 '考勤与统计': 'Attendance & Statistics',
 '自定义': 'Custom',
 '自定义材料': 'Custom Material Types',
 '自定义材料和预设会保存在本机；应用组合后仍可继续增减勾选。': 'Custom material types and presets are saved on this computer. You can '
                                  'adjust selections after applying a preset.',
 '至': 'to',
 '至少保留一份工资明细表参与合并': 'Keep at least one payroll detail workbook for merging',
 '至少保留一份工资明细表参与合并。': 'Keep at least one payroll detail workbook for merging.',
 '花名册更新': 'Update Employee Roster',
 '花名册身份证重复但姓名不同：': 'Roster ID number duplicated with different names:',
 '薪酬管理': 'Payroll',
 '行': 'row',
 '行，到第': 'through row',
 '表头范围须在 1—200 行内，连续表头最多 6 行': 'Header rows must be within rows 1–200, with no more than 6 consecutive rows',
 '要找哪一项？例如：公司、金额': 'Find a field, such as Company or Amount',
 '规范名称格式': 'Normalize Names',
 '规范名称格式：可去除首尾空格、合并空格，按需统一横线和下划线；不自动删除“作废、补签”等业务文字。': 'Normalize Names: trim outer spaces, collapse spaces, '
                                                      'and optionally standardize hyphens and underscores. '
                                                      'Business words such as Void or Countersigned are not '
                                                      'removed automatically.',
 '记住所选页名，下次自动识别（可在工作表设置中修改、删除）': 'Remember these worksheet names (editable in Worksheet Settings)',
 '记住本项目的选择': 'Remember for This Project',
 '记住相同表头的选择（不勾选仅本次，可随时撤销）': 'Remember for the same headers (otherwise this run only; can be removed later)',
 '设为': 'Set to',
 '设置': 'Settings',
 '设置未能保存；可取消勾选记住设置，仅用于本次合并': 'Could not save settings. Uncheck Remember to use them for this run only.',
 '设置立即生效并自动保存。资料名称、Excel 列名和生成结果保持原样。': 'Changes apply immediately and are saved automatically. Filenames, '
                                        'Excel headers, and generated results remain unchanged.',
 '该工具暂未实现。': 'This tool is not implemented yet.',
 '语言': 'Language',
 '说明：上传资料已保存，但本次没有正常生成完整结果。': 'Source files were saved, but this run did not produce complete results.',
 '说明：这次处理没有正常完成，可以再次使用已保存的资料。': 'This run did not finish normally. The saved files can be used again.',
 '请先{0}。': '{0} first.',
 '请先勾选至少一种材料，再保存为预设。': 'Select at least one material type before saving a preset.',
 '请先在项目文件中选择某个处理批次内的文件或文件夹。': 'Select a file or folder within a processing batch in Project Files first.',
 '请先复制资料': 'Copy the Files First',
 '请先完成当前处理': 'Finish the Current Task First',
 '请先打开工作项目': 'Open a Project First',
 '请先打开工作项目。': 'Open a project first.',
 '请先打开项目': 'Open a Project First',
 '请先新建或打开一个工作项目。': 'Create or open a project first.',
 '请先新建或打开工作项目': 'Create or Open a Project First',
 '请先更新工具': 'Update the App First',
 '请先选择包含姓名列的 Excel 名单。': 'Select an Excel roster containing a name column.',
 '请先选择要删除的自定义材料。': 'Select the custom material type to delete first.',
 '请务必按接收方电脑的系统选择链接：Windows 7 必须使用 Win7 安装包，切勿下载或安装 Win10/11 安装包；Windows 10/11 请使用对应的 Win10/11 安装包。': 'Choose '
                                                                                                     'the '
                                                                                                     'link '
                                                                                                     'for '
                                                                                                     'the '
                                                                                                     "recipient's "
                                                                                                     'operating '
                                                                                                     'system. '
                                                                                                     'Windows '
                                                                                                     '7 '
                                                                                                     'requires '
                                                                                                     'the '
                                                                                                     'Win7 '
                                                                                                     'installer; '
                                                                                                     'do not '
                                                                                                     'use '
                                                                                                     'the '
                                                                                                     'Windows '
                                                                                                     '10/11 '
                                                                                                     'installer. '
                                                                                                     'Windows '
                                                                                                     '10/11 '
                                                                                                     'requires '
                                                                                                     'its '
                                                                                                     'corresponding '
                                                                                                     'installer.',
 '请在当前项目重新选择工资表。': 'Select the payroll files again in the current project.',
 '请处理 {0} 的问题，或明确选择本次不合并该文件': 'Resolve the issues with {0}, or explicitly exclude this file from this run',
 '请完善列头对应': 'Complete the Column Mapping',
 '请按原文核对；条数不代表异常人数。': 'Check the original notices. Their count is not the number of affected employees.',
 '请核对列对应关系': 'Review Column Mapping',
 '请核对后保存修改。': 'Review the changes before saving.',
 '请核对工作表选择。': 'Review the worksheet selections.',
 '请核对工资表对应列': 'Review Payroll Column Mapping',
 '请核对所选列的含义。': 'Check what each selected column represents.',
 '请确认“': 'Confirm ',
 '请确认数据的读取方式': 'Confirm the Reading Mode',
 '请确认这些内容对应的列：': 'Choose the columns for these fields:',
 '请稍候，检查完成后会自动提示。': 'Please wait. You will be notified when the check finishes.',
 '请等待当前任务结束。': 'Wait for the current task to finish.',
 '请等待资料保存完成后再开始处理。': 'Wait for files to finish saving before processing.',
 '请等待资料检查完成，或先取消本次检查。': 'Wait for the file check to finish, or cancel it first.',
 '请至少选择一种材料，或者勾选“全部”。': 'Select at least one material type, or select All.',
 '请补充“': 'Provide ',
 '请输入员工姓名/身份证，或选择员工名单 Excel 表格。': 'Enter employee names or ID numbers, or select an Excel roster.',
 '请选出未识别内容所在的列。下拉选项里有原表内容，方便核对。': 'Choose the columns for unrecognized fields. Source samples are included '
                                  'in the choices to help you check.',
 '请选择 Excel 底部的工作表': 'Select a worksheet from the Excel tabs',
 '请选择“': 'Select ',
 '请选择人员文件夹目录，填写改名内容，然后点击“预览”。': 'Select an employee files folder, enter the rename rule, and click Preview.',
 '请选择保单人员清单和人力资源分析表，然后点击“生成台账”。结果会保存在当前项目，源文件请自行保管。': 'Select policy enrollment lists and an HR analysis '
                                                      'workbook, then click Generate Ledger. Results are '
                                                      'saved to the project; keep your originals.',
 '请选择列表中的工作表': 'Select a worksheet from the list',
 '请选择原表中的列': 'Select a source column',
 '请选择含原文件名和新名称两列的 Excel。': 'Select an Excel file with original-name and new-name columns.',
 '请选择员工资料库根目录，输入目标人员或选择员工名单 Excel，勾选所需材料类型，然后点击“开始打包”。': 'Select the employee library folder, enter target '
                                                         'employees or select an Excel roster, choose '
                                                         'material types, and click Package Materials.',
 '请选择处理批次': 'Select a Processing Batch',
 '请选择工资表文件、压缩包或文件夹，然后点击“开始合并”。已有汇总表是可选项，结果会保存在当前项目，源文件请自行保管。': 'Select payroll workbooks, archives, or a '
                                                               'folder, then click Merge. An existing '
                                                               'summary is optional. Results are saved to '
                                                               'the project; keep your originals.',
 '请选择工资表文件，然后点击“开始拆分”。结果会保存在当前项目，源文件请自行保管。': 'Select a payroll workbook and click Split. Results are saved '
                                             'to the project; keep your originals.',
 '请选择左侧已完成的工具：需求1、需求2、需求4、需求5、需求6、需求7、需求8、需求9。': 'Select an available tool from the sidebar.',
 '请选择异动汇总表和人力资源花名册，然后点击“更新花名册”。结果会保存在当前项目，源文件请自行保管。': 'Select personnel-change summaries and an employee '
                                                      'roster, then click Update Roster. Results are saved '
                                                      'to the project; keep your originals.',
 '请选择异动表文件或文件夹，然后点击“开始汇总”。已有汇总表是可选项，结果会保存在当前项目，源文件请自行保管。': 'Select personnel-change files or a folder, then '
                                                           'click Consolidate. An existing summary is '
                                                           'optional. Results are saved to the project; keep '
                                                           'your originals.',
 '请选择数据的读取方式': 'Choose the reading mode',
 '请选择数据的读取方式。': 'Choose the reading mode.',
 '请选择材料': 'Select Material Types',
 '请选择档案汇总表、压缩包或文件夹，然后点击“生成档案表”。已有公司档案表是可选项，结果会自动留存在当前项目。': 'Select archive summaries, archives, or a folder, '
                                                           'then click Generate Company Archives. Existing '
                                                           'company archives are optional; results are saved '
                                                           'to the project.',
 '请选择社保缴费清单和参保人员花名册，然后点击“生成报表”。结果会保存在当前项目，源文件请自行保管。': 'Select social insurance payment lists and an insured '
                                                      'employee roster, then click Generate Reports. Results '
                                                      'are saved to the project; keep your originals.',
 '请选择移交表文件、压缩包或文件夹，然后点击“开始入库”。已有档案汇总表是可选项，结果会自动留存在当前项目。': 'Select archive-transfer files, archives, or a '
                                                          'folder, then click Import Records. An existing '
                                                          'summary is optional; results are saved to the '
                                                          'project.',
 '请选择考勤结果、周报记录和月报记录，然后点击“生成统计”。应汇报人员名单是可选项，结果会保存在当前项目，源文件请自行保管。': 'Select attendance, weekly-report, and '
                                                                  'monthly-report records, then click '
                                                                  'Generate Statistics. The expected '
                                                                  'reporters roster is optional. Results are '
                                                                  'saved to the project; keep your '
                                                                  'originals.',
 '请选择需要读取的工作表': 'Select Worksheets to Read',
 '请选择需要读取的资料类型': 'Select the data type to read',
 '请选择需要读取的资料类型。': 'Select the data type to read.',
 '请重新打开当前项目后再选择资料。': 'Reopen the current project before selecting files.',
 '请重新点击开始处理。不同工具的设置互不影响。': 'Start processing again. Settings for different tools are independent.',
 '请重新确认列名': 'Confirm Column Names Again',
 '请重新选择列名': 'Select Columns Again',
 '请重新选择工作项目': 'Select the Project Again',
 '请重新预览': 'Generate a New Preview',
 '读取哪个工作表': 'Worksheet to Read',
 '读取哪个工作表（Excel 底部的标签）': 'Worksheet to Read (Excel tab)',
 '读取方式：': 'Reading mode:',
 '读取这些列名': 'Read Headers',
 '读取项目界面设置位置失败': 'Could not locate workspace preferences',
 '读取项目界面设置失败': 'Could not read workspace preferences',
 '读取项目目录失败': 'Could not read the project folder',
 '调整下载和安装进度窗口，清晰显示下载、文件检查和安装状态，并完善取消下载的操作。': 'Refined download and installation progress with clearer '
                                             'verification states and download cancellation.',
 '资料已带入': 'Files Added to Tool',
 '资料库形式': 'Library Layout',
 '资料库形式：已有姓名文件夹选“原模式”；文件无序混放时选“OCR 索引”，首次建立索引后会复用未变化文件。': 'Use Employee Folders when documents are already '
                                                          'organized by employee. Use OCR Index for mixed, '
                                                          'unorganized files. Unchanged files reuse the '
                                                          'index after the first scan.',
 '资料打包在内存较小的电脑上可自动使用省内存识别方式，减少因内存不足而中断的情况。': 'Material retrieval can use a memory-saving recognition mode on '
                                             'low-memory computers to reduce interruptions.',
 '资料文件夹改名': 'Rename Files & Folders',
 '资料检索与打包设置': 'Material Search & Packaging',
 '身份证号码': 'ID Number',
 '输入': 'Input',
 '输入不存在': 'Input Not Found',
 '输入修改后的名称': 'Enter the updated name',
 '输入数量不正确': 'Incorrect Number of Inputs',
 '输入文件只支持 .xlsx、.xls 或 ZIP/RAR/7Z/TAR 压缩包。': 'Supported input files: .xlsx, .xls, ZIP, RAR, 7Z, or TAR '
                                             'archives.',
 '输入文件名': 'Enter a filename',
 '输入新的预设名称': 'Enter a new preset name',
 '输入材料名称（例如：户口本、体检报告）': 'Enter a material type, such as Household Register or Medical Exam',
 '输入预设名称': 'Enter a preset name',
 '运行信息': 'Run Information',
 '运行提醒': 'Run Notices',
 '运行记录': 'Run Log',
 '返回': 'Back',
 '还不能确定哪一行写着列名，请在原表预览中点选；如果文件选错了，请返回重新选择。': 'The header row could not be identified. Select it in the source '
                                            'preview, or go back if you chose the wrong file.',
 '还有 ': 'Remaining: ',
 '还有文件问题未处理，请查看文件提示；可跳过的文件需要明确勾选。': 'Some file issues remain. Review the notices and explicitly select any '
                                    'files to skip.',
 '还没有记住任何选择。确认列名时默认仅本次使用。': 'No saved mappings yet. Column choices apply to the current run by default.',
 '还需要至少选择一项金额；个人和单位的金额不能混用。': 'Select at least one amount field. Individual and employer amounts must not be '
                              'mixed.',
 '还需要选择：': 'Still needed:',
 '这个预设不存在或已经被删除。': 'This preset does not exist or has been deleted.',
 '这些资料已在列表中，未重复添加。': 'These files are already selected and were not added again.',
 '这些选择会用于当前工具中工作表名和表头相同的文件。列的含义变了，请修改或删除；删除后按原有名称识别，不认识的列会重新询问。': 'Saved mappings apply to matching '
                                                                  'worksheet names and headers in this tool. '
                                                                  'Edit or delete them if column meanings '
                                                                  'change. Deleting restores automatic '
                                                                  'detection and prompts for unrecognized '
                                                                  'fields.',
 '这张工作表将不参与本次处理。请确认它不是需要统计的业务数据。': 'This worksheet will be excluded. Confirm it contains no business data '
                                   'needed for this run.',
 '这张工作表没有可预览的内容，请换一张工作表或返回重新选文件。': 'This worksheet has no previewable content. Choose another worksheet or '
                                   'go back and select a different file.',
 '这是系统内置名称，不需要重复添加，也不能修改。': 'This name is built in. It cannot be edited and does not need to be added again.',
 '这条旧记录暂时不能直接再次使用，可以先打开上传资料。': 'This legacy record cannot be reused directly. Open its source files first.',
 '这条记录暂时无法读取': 'This Record Is Temporarily Unavailable',
 '这条选择已删除，请返回重新选择': 'This mapping was deleted. Go back and select another.',
 '这次处理的上传资料和结果会移到 HRToolkit 回收站，不会立即永久删除。是否继续？': "Move this run's source files and results to HR Toolkit "
                                                 'Trash? They will not be permanently deleted immediately.',
 '这里保存从当前项目移走的完整处理批次；恢复时不会覆盖已有资料。': 'Trash holds entire batches removed from this project. Restoring never '
                                    'overwrites existing files.',
 '这里只接收': 'This input accepts only ',
 '这里只能接收一个位置，请一次选择一项资料。': 'This input accepts one location. Select one item at a time.',
 '这里没有可接收资料的区域。': 'There is no available input area here.',
 '这里用于查看升级前由旧版本保存的处理记录。': 'This view contains processing records saved by versions before the upgrade.',
 '追加/删除文字': 'Text to Append / Remove',
 '追加文字': 'Append Text',
 '追加文字：姓名不填就是全部项目追加；填姓名就是只处理这个人。输入内容会原样追加，需要分隔符时请一并输入。': 'Append Text: leave the name blank to process all '
                                                         'items, or enter a name to limit the selection. '
                                                         'Text is appended exactly as entered; include any '
                                                         'desired separator.',
 '退出程序': 'Exit App',
 '适用：一个完整工资表按“入职公司”拆成多个公司工资表。': 'Split a complete payroll workbook into separate workbooks by hiring '
                                'company.',
 '适用：已有月度异动汇总表时，单独更新人力资源花名册。': 'Update the employee roster separately from existing monthly personnel-change '
                               'summaries.',
 '适用：批量修改所选目录下第一层文件夹或文件名称。': 'Batch rename files and folders in the first level of the selected folder.',
 '适用：把 1-12 个月工资表合成一张个人应发工资汇总表。': 'Combine 1–12 months of payroll into a gross-pay summary by employee.',
 '适用：把 HR 系统导出的考勤结果、周报记录、月报记录自动整理成统计表。': 'Turn attendance, weekly-report, and monthly-report exports into '
                                         'statistics.',
 '适用：把一个或多个档案汇总表写入各公司独立档案表。': 'Write one or more archive summaries into separate company archive files.',
 '适用：把各保单人员清单整理成保险台账，并根据需求6的人力资源分析表做增减预警。': 'Build an insurance ledger from policy lists and compare against '
                                            'the HR analysis workbook for enrollment changes.',
 '适用：把各社保账户缴费清单整理成社保明细表和社保汇总表。': 'Consolidate payment lists from social insurance accounts into detail and '
                                 'summary workbooks.',
 '适用：把项目异动表按记录日期分到对应月份汇总表。': 'Group project personnel changes into monthly summaries by record date.',
 '适用：把项目部提交的人事档案移交表写入公司档案汇总表。': 'Import personnel archive transfer sheets from project teams into the '
                                'company archive summary.',
 '适用：根据员工名单从资料库批量提取特定材料（身份证、合同、学历等）并自动打包。': 'Retrieve employee materials such as IDs, contracts, and '
                                            'education certificates from the library and package them '
                                            'automatically.',
 '选择': 'Select',
 '选择“': 'Select ',
 '选择一个包含“汇总表”和“明细表”的工资表，工具会按“入职公司”拆成多个公司文件。': 'Select a payroll workbook containing summary and detail '
                                              'worksheets to split it by hiring company.',
 '选择一条记录查看详情': 'Select a record to view details',
 '选择人员文件夹目录': 'Select Employee Files Folder',
 '选择人员资料目录，先预览，再确认改名。': 'Select the employee files folder, review the preview, then confirm the changes.',
 '选择保单清单、压缩包或文件夹': 'Select Policy Lists, Archives, or Folder',
 '选择其他位置': 'Choose Another Location',
 '选择分析表': 'Select Analysis Workbook',
 '选择各保单人员清单、压缩包或文件夹，再选择需求6的人力资源分析表，自动生成保险台账。': 'Select policy lists, archives, or a folder, then an HR '
                                               'analysis workbook to generate the insurance ledger.',
 '选择同事电脑的系统': "Choose the recipient's operating system",
 '选择名单': 'Select Roster',
 '选择员工资料库路径（只读扫描）': 'Select Employee Library (read-only)',
 '选择处理文件': 'Select Files to Process',
 '选择处理文件夹': 'Select Folder to Process',
 '选择工资表、压缩包或文件夹': 'Select Payroll Files, Archives, or Folder',
 '选择工资表文件': 'Select Payroll Workbook',
 '选择工资表文件、压缩包或文件夹；如已有汇总表，可一并选择后追加新月份。': 'Select payroll workbooks, archives, or a folder. Optionally add an '
                                        'existing summary to append new months.',
 '选择已修改': 'Mapping Updated',
 '选择已齐全，请核对后继续。': 'All fields are selected. Review them before continuing.',
 '选择异动汇总表、压缩包或文件夹': 'Select Personnel-Change Summaries, Archives, or Folder',
 '选择异动汇总表和人力资源花名册，单独更新花名册。': 'Select personnel-change summaries and an employee roster to update the roster '
                             'separately.',
 '选择异动表、压缩包或文件夹': 'Select Personnel-Change Files, Archives, or Folder',
 '选择异动表、压缩包或文件夹；如已有月度汇总表，可选择后按月份追加。': 'Select personnel-change files, archives, or a folder. Optionally '
                                      'select existing monthly summaries to append records by month.',
 '选择文件': 'Select Files',
 '选择文件夹': 'Select Folder',
 '选择本条': 'Select This Item',
 '选择本次处理的文件': 'Select Files for This Run',
 '选择本次处理的文件夹': 'Select Folder for This Run',
 '选择本次需要确认的模板': 'Select a Template to Review',
 '选择档案汇总表、压缩包或文件夹': 'Select Archive Summaries, Archives, or Folder',
 '选择档案汇总表、压缩包或文件夹，按公司写入已有档案表；没有已有表时自动新建。': 'Select archive summaries, archives, or a folder to update '
                                           'company archives. Missing archives are created automatically.',
 '选择档案表': 'Select Company Archive',
 '选择汇总表': 'Select Summary',
 '选择的文件或处理选项已改变，请返回主界面重新开始处理': 'Selected files or options changed. Return to the main screen and start '
                               'processing again.',
 '选择的文件或文件夹不存在：{0}': 'The selected file or folder does not exist: {0}',
 '选择的配套资料不存在：{0}': 'The selected supporting file does not exist: {0}',
 '选择社保缴费清单、压缩包或文件夹，再选择参保人员花名册，自动生成明细和汇总。': 'Select social insurance payment lists, archives, or a folder, '
                                           'then an insured employee roster to generate details and '
                                           'summaries.',
 '选择移交表、压缩包或文件夹': 'Select Transfer Sheets, Archives, or Folder',
 '选择组合后，点击“应用”才会更改材料勾选。': 'Select a preset, then click Apply to change the material selections.',
 '选择缴费清单、压缩包或文件夹': 'Select Payment Lists, Archives, or Folder',
 '选择考勤 / 周报 / 月报文件、压缩包或文件夹': 'Select Attendance / Report Files, Archives, or Folder',
 '选择考勤结果、周报记录、月报记录，或包含这些文件的文件夹/压缩包，自动生成统计表和异常明细。': 'Select attendance, weekly-report, and monthly-report '
                                                   'files, or folders and archives containing them, to '
                                                   'generate statistics and exception details.',
 '选择花名册': 'Select Employee Roster',
 '选择项目保存位置': 'Choose Project Location',
 '选择项目文件': 'Select Project Files',
 '选择项目档案移交表、压缩包或文件夹；可选已有档案汇总表，不选则新建。': 'Select project archive transfer sheets, archives, or a folder. An '
                                       'existing archive summary is optional; otherwise one is created.',
 '配套资料不存在': 'Supporting File Not Found',
 '配套资料只支持 .xlsx 或 .xls 文件。': 'Supporting files must be .xlsx or .xls.',
 '配套资料只支持 .xlsx、.xls 文件或文件夹。': 'Supporting files must be .xlsx, .xls, or a folder.',
 '配套资料只支持 Excel、压缩包或文件夹。': 'Supporting data must be Excel files, archives, or a folder.',
 '重启以更新': 'Restart to Update',
 '重启以更新，版本': 'Restart to update to version',
 '重命名预设': 'Rename Preset',
 '重新整理记录': 'Reorganize History',
 '问题修复': 'Bug Fixes',
 '需处理': 'Issues',
 '需要你确认的列': 'Fields Needing Review',
 '需要文件夹': 'Folder Required',
 '需要确认模板对应关系：': 'Template mapping needs review:',
 '需要重新下载更新': 'Update Must Be Downloaded Again',
 '项目': 'Project',
 '项目为只读状态。': 'The project is read-only.',
 '项目以只读方式打开': 'Project Opened Read-only',
 '项目位置不可用，请重新选择原项目文件夹。': 'The project location is unavailable. Select the original project folder again.',
 '项目位置不完整，请通过“打开项目”重新选择文件夹。': 'The project location is incomplete. Select the folder again using Open '
                              'Project.',
 '项目位置无效。': 'Invalid project location.',
 '项目名称': 'Project Name',
 '项目回收站': 'Project Trash',
 '项目当前为只读状态。': 'The project is currently read-only.',
 '项目或工具已变化，未执行改名。': 'The project or tool changed. No renames were performed.',
 '项目或工具已变化，请重新从项目文件拖入。': 'The project or tool changed. Drag the files from Project Files again.',
 '项目文件': 'Project Files',
 '项目是一套可随时打开、完整留存资料的工作文件夹。': 'A project is a work folder that keeps related files together and can be '
                             'reopened at any time.',
 '项目未安全恢复': 'Project Recovery Required',
 '项目资料正在保存': 'Project Files Are Being Saved',
 '预览': 'Preview',
 '预览为已读取的前几行。列名占多行或位置更靠后时，可在下面调整后读取。': 'This preview shows the first loaded rows. Adjust the range below if '
                                       'headers span multiple rows or start farther down.',
 '预览仅显示前 30 行、前 512 列。这里找不到列名时，请返回检查原文件；不会修改原表。': 'Preview shows the first 30 rows and 512 columns. If '
                                                  'headers are missing here, go back and check the source '
                                                  'file. The source will not be modified.',
 '预览失败': 'Preview Failed',
 '预览已生成：共 {0} 项，请在完整预览中核对和调整。': 'Preview generated: {0} items. Review and adjust the complete plan.',
 '预设不可用': 'Preset Unavailable',
 '预设已保存': 'Preset Saved',
 '预设已更新': 'Preset Updated',
 '预设管理': 'Manage Presets',
 '首次确认文件：': 'First confirmed file:',
 '（原表候选，勾选添加）': '(source candidates; select to add)',
 '（可不选）': '(optional)',
 '（回收站 {0}）': '(Trash {0})',
 '（已记住 ': '(saved: ',
 '（当前阶段 ': '(current stage ',
 '（必须选择）': '(required)',
 '（系统内置）': '(built-in)',
 '（自定义）': '(custom)',
 '，不能一次拖入多项。': '; multiple items cannot be dropped at once.',
 '，也可点击选择': ', or click to browse',
 '，你当前使用的是 v': '; you currently have v',
 '，展开更新内容': ', expand release notes',
 '，收起更新内容': ', collapse release notes',
 '；已填写目标人员时可不选': '; optional when target employees are entered',
 '\n\n删除后会自动清理这些预设中的引用：': '\n\nReferences will also be removed from these presets:',
 '\n双击打开': '\nDouble-click to open',
 '\n另有 {0} 条处理提醒/运行信息，可在结果提醒区查看全部。': '\n{0} more notices are available in Results.',
 '\n另有 {0} 项不符合要求。': '\n{0} more items do not meet the requirements.',
 '\n向左拖入资料区；单击选中，双击打开': '\nDrag left to the input area. Click to select; double-click to open.',
 '\n已删除空预设：': '\nEmpty presets removed:',
 '\n已更新预设：': '\nPresets updated:',
 '\n目前没有可用的新版本。': '\nNo updates are currently available.',
 ' · 已留存 {0} · 磁盘可用 {1}': ' · Saved {0} · Free disk space {1}',
 ' · 正在校验…': ' · Verifying…',
 ' · 第 ': ' · Row ',
 ' · 距上次进度更新 ': ' · Time since last progress update: ',
 ' 个文件 · ': ' files · ',
 ' 条提醒/运行信息': ' notices',
 ' 秒': ' sec',
 ' 秒；单份资料识别期间计数保持不变': ' sec; the count stays unchanged while a document is being recognized',
 ' 类模板需要确认。请在上方模板列表中逐个选择。': ' template types need review. Select each template above.',
 ' 行': ' rows',
 ' 行 · ': ' · Row ',
 ' 行，点击设为列名行': '; click to use as the header row',
 ' 行，请核对。选错了，点另一行即可。': '. Check the selection, or click another row to change it.',
 ' 项已识别，可展开下方选项查看或修改。': ' fields recognized. Expand the options below to review or change them.',
 ' 项）': ' saved)',
 '- Excel 顺序改名支持在预览中通过“上移／下移”调整姓名对应关系，无需修改原始 Excel。': '- Excel rename preview now lets you move names up or '
                                                      'down to adjust assignments without editing the '
                                                      'workbook.',
 '- Windows 更新安装时显示进度窗口，提供安装百分比、当前替换文件及新版启动状态提示。': '- Windows updates display installation progress and the '
                                                   'status of the new app launch.',
 '- “检查更新”移至左侧底部，“使用教程”和“更新记录”并排放在右上角。': '- Check for Updates is now at the bottom left; Help and Release '
                                         'Notes are at the top right.',
 '- 上传的原始资料不再额外保存永久副本，项目只保留处理结果；源文件请自行保管，历史资料仍可正常使用。': '- Projects retain processing results without keeping '
                                                       'permanent copies of uploaded source files. Keep your '
                                                       'originals; existing project files remain available.',
 '- 下载完成后显示“重启以更新”，点击后安装并重新打开工具，不再单独弹出下载进度窗口。': '- Downloaded updates show Restart to Update, which installs '
                                                'the update and reopens the app.',
 '- 主滚动条调整至内容面板右侧，去除项目栏顶部多余留白。': '- Moved the main scroll bar to the right edge and removed excess space '
                                 'above the project panel.',
 '- 优化回收站搜索和结果提醒分类切换，减少重复处理。': '- Reduced repeated processing when searching Trash and filtering result '
                               'notices.',
 '- 优化窄窗口下部分表单、选择框及较长文字的布局。': '- Improved forms, dropdowns, and long labels in narrow windows.',
 '- 优化长更新记录的加载与显示，减少界面控件数量和布局开销。': '- Improved long release-note lists with fewer controls and less layout '
                                   'work.',
 '- 优化项目文件列表刷新，仅更新发生变化的内容，减少整表重建。': '- Project files now refresh only changed items instead of rebuilding '
                                    'the full list.',
 '- 修复 Windows 本地文件拖入时被误提示需要再次保存，以及快速松手导致文件无法带入的问题。': '- Fixed local Windows files being rejected when '
                                                      'dropped, including quick drag-and-drop gestures.',
 '- 修复 Windows 窗口连续缩放时，新露出区域背景色不一致的问题。': '- Fixed inconsistent background colors when resizing a Windows '
                                         'window.',
 '- 修复不同目录下同名文件共用工作表选择、可能漏处理数据的问题，兼容压缩包和旧版 Excel 格式。': '- Fixed different files with the same name sharing '
                                                       'worksheet selections and potentially being skipped. '
                                                       'Archives and legacy Excel files remain supported.',
 '- 修复切换工具时顶部标题和按钮触发布局循环的问题。': '- Fixed header layout loops when switching tools.',
 '- 修复回收站筛选后选中状态不同步的问题。': '- Fixed selections becoming inconsistent after filtering Trash.',
 '- 修复工资工具记住工作表名称后，已有列名对应关系失效的问题，兼容此前保存的选择。': '- Fixed saved payroll column mappings becoming unavailable '
                                              'after saving worksheet names; existing choices remain '
                                              'compatible.',
 '- 修复更新记录初始化时可能出现的显示异常。': '- Fixed display issues when initializing release notes.',
 '- 修复点击侧栏图标后边框一直保留，以及更新弹窗按钮出现深色描边的问题。': '- Fixed persistent sidebar icon borders and dark outlines on '
                                         'update dialog buttons.',
 '- 修复生成结果或刷新项目文件后，已展开的目录自动折叠的问题。': '- Fixed expanded project folders collapsing after processing or '
                                    'refreshing.',
 '- 修复社保各险种补差日期互相串用的问题，分别按实际补差期间显示；无对应补差数据时不显示日期。': '- Fixed adjustment dates being shared between social '
                                                    'insurance types. Each type now shows its own adjustment '
                                                    'period, or no date when no adjustment exists.',
 '- 修复社保明细导出后数据行边框、比例和金额格式丢失的问题。': '- Fixed missing row borders, percentage formats, and currency formats in '
                                   'exported social insurance details.',
 '- 修复系统自动生成的文件导致回收站批次无法恢复的问题，恢复时仍会检查实际资料是否完整、是否被修改。': '- Fixed system-generated files preventing batches '
                                                       'from being restored from Trash. Restoration still '
                                                       'verifies that business files are intact and '
                                                       'unchanged.',
 '- 修复考勤明细排序不符合要求的问题，按“应汇报人员名单”顺序输出。': '- Attendance details now follow the expected reporters roster order.',
 '- 修复输入检查或模板确认尚未完成时提前创建输出目录、重复处理留下空目录的问题。': '- Fixed empty output folders being created before input or '
                                             'template checks finished.',
 '- 修复部分 Excel 导出范围不完整时，社保工具可能跳过主数据页、误读其他工作表的问题。': '- Fixed some Excel exports causing social insurance data '
                                                   'to be skipped or read from the wrong worksheet.',
 '- 修复顶部窗口按钮与折叠图标未对齐的问题。': '- Fixed window buttons and collapse icons being misaligned.',
 '- 修复项目文件列表变化后，选中高亮与操作目标可能不一致的问题。': '- Fixed project-file selection highlighting becoming inconsistent with '
                                     'the operation target after updates.',
 '- 修复项目文件拖动无效、部分表单文案拥挤及对齐不一致的问题。': '- Fixed project-file drag-and-drop and improved form spacing and '
                                    'alignment.',
 '- 修正检查更新时的状态文案，统一显示“正在检查更新…”，避免与下载安装混淆。': '- Update checks consistently show Checking for updates to '
                                            'distinguish them from downloads and installation.',
 '- 减少更新下载期间的重复刷新及动画绘制开销，优化窗口拖动响应。': '- Reduced repeated refreshes and animations during update downloads '
                                     'for smoother window dragging.',
 '- 减少表单重复计算、重复状态通知及相同界面设置的磁盘写入。': '- Reduced repeated form calculations, state notifications, and settings '
                                   'writes.',
 '- 升级批量改名预览，支持查看全部项目的原名称、新名称、相对路径及处理状态，并可搜索、筛选和快速定位冲突；优化大批量列表显示，方便核对数千条资料。': '- Rename preview now shows '
                                                                              'the entire batch with '
                                                                              'original names, proposed '
                                                                              'names, paths, and statuses. '
                                                                              'Search, filters, and issue '
                                                                              'navigation make thousands of '
                                                                              'items easier to review.',
 '- 取消内容区域和资料列表滚动到边缘时的回弹。': '- Removed bounce effects at the edges of scrolling lists.',
 '- 右侧项目文件栏展开后与中间内容共同分配宽度，不再遮挡操作区域；收起后自动释放空间。': '- The project panel now shares space with the main content '
                                                'instead of covering it, and frees that space when '
                                                'collapsed.',
 '- 回收站入口移至项目文件面板底部，放在“移到回收站”右侧，方便查找和恢复已移除的批次。': '- Trash is now at the bottom of the project panel beside '
                                                 'Move to Trash.',
 '- 在“更新记录”右侧新增“复制下载地址”，支持选择 Windows 7 或 Windows 10/11 安装包': '- Added Copy Download Link beside Release '
                                                             'Notes, with separate Windows 7 and Windows '
                                                             '10/11 installers.',
 '- 增大默认窗口尺寸，并根据屏幕可用空间自动适配。': '- Increased the default window size while adapting to available screen space.',
 '- 完善各相关工具的工作表适配，支持选择实际工作表，以及添加、修改、删除常用页名；已找到所需页时，多余页仅提示未处理，不额外弹窗。': '- Added worksheet selection and '
                                                                      'editable saved worksheet names across '
                                                                      'related tools. Extra sheets are '
                                                                      'reported without interrupting '
                                                                      'processing when the required sheets '
                                                                      'are found.',
 '- 完善预览调整后的安全检查，修改名称或调整对应关系后重新检查重名、无效名称、扩展名及大小写冲突；执行前再次核对资料状态，防止覆盖已有文件。': '- Name edits and mapping changes '
                                                                           'now rerun duplicate, '
                                                                           'invalid-name, extension, and '
                                                                           'case-insensitive collision '
                                                                           'checks. Files are checked again '
                                                                           'before execution to prevent '
                                                                           'overwrites.',
 '- 工具自动发现新版本后，在左下角下载并显示进度和百分比，无需手动确认；手动检查更新仍保留更新说明和确认步骤。': '- Available updates download automatically with '
                                                            'progress at the bottom left. Manual checks '
                                                            'still show release notes and confirmation.',
 '- 左侧菜单支持展开和收起，收起后将鼠标移到图标上可临时查看，点击可固定展开，为小屏幕留出更多操作空间。': '- The sidebar can be collapsed for smaller '
                                                         'screens. Hover to view it temporarily, or click to '
                                                         'pin it open.',
 '- 已下载完成的更新包会保留，关闭后重新打开工具，无需重复下载。': '- Downloaded updates are retained across app restarts.',
 '- 恢复并统一可选字段提示，明确追加／删除操作的名称筛选、Excel 映射列名、员工名单及统计日期的留空规则，避免误认为必须填写。': '- Restored consistent optional-field '
                                                                      'guidance for rename filters, Excel '
                                                                      'mapping columns, employee rosters, '
                                                                      'and report date ranges.',
 '- 支持从右侧项目文件拖动或选择资料带入当前工具。': '- Project files can be selected or dragged into the current tool.',
 '- 支持拖入文件、文件夹和压缩包，拖动时提示接收范围及文件类型是否支持。': '- Added file, folder, and archive drag-and-drop with '
                                         'supported-type guidance.',
 '- 整合材料预设管理入口，优化任务状态和处理结果提示。': '- Consolidated material preset controls and improved task and result '
                                'messages.',
 '- 新增“地区编号维护”，支持按项目添加、修改和删除自定义编号；同编号或同地区优先使用自定义配置，删除后恢复内置规则。': '- Added project-specific region codes. '
                                                                'Custom codes override matching built-in '
                                                                'codes; deleting them restores the defaults.',
 '- 新增“已记住的选择”，支持查看、修改和删除列名对应关系；普通列名确认默认仅本次生效，也可选择记住。': '- Added Saved Mappings to review, edit, and delete '
                                                        'column mappings. New selections apply to the '
                                                        'current operation unless saved.',
 '- 新增“按 Excel 原文件名匹配”，通过“原文件名”和“新名称”两列明确指定改名关系，避免文件顺序不同导致对应错误。': '- Added Match Excel by Original Name, '
                                                                  'using explicit original-name and new-name '
                                                                  'columns to avoid ordering errors.',
 '- 新增“替换指定文字”，可批量替换文件或文件夹名称中的部分文字，保留其余名称和文件扩展名；支持按文件夹、PDF、图片、文档或全部类型筛选。': '- Added Replace Text to replace '
                                                                           'part of a file or folder name '
                                                                           'while preserving the rest and '
                                                                           'its extension. Filter by folder, '
                                                                           'PDF, image, document, or all '
                                                                           'types.',
 '- 新增“规范名称格式”，支持去除名称首尾空格、合并连续空格及全角空格，并可按需统一横线和下划线。': '- Added Normalize Names to trim leading and trailing '
                                                      'spaces, collapse repeated and full-width spaces, and '
                                                      'optionally standardize hyphens and underscores.',
 '- 新增批次改名记录和完成清单，保存原名称、新名称及处理结果，方便核对和追溯。': '- Added batch rename logs and completion receipts with original '
                                            'names, final names, and results for review and traceability.',
 '- 新增预览内手动调整，支持直接修改单个项目的新名称，或取消勾选暂不处理的项目；确认后严格按最终预览执行。': '- Rename preview now supports individual name '
                                                          'edits and exclusions. Execution follows the final '
                                                          'confirmed plan.',
 '- 日期支持简写输入，模板适配支持定位待处理项，结果提醒支持分类查看。': '- Added compact date entry, navigation to unresolved template '
                                        'fields, and result-notice filters.',
 '- 更新准备完成后，暂停生成、统计、拆分、汇总、入库、打包和预览等主操作，其他功能仍可使用，正在处理的任务不受影响。': '- When an update is ready, processing '
                                                               'actions are paused until restart. Other '
                                                               'features remain available and running tasks '
                                                               'are unaffected.',
 '- 更新安装失败或新版未正常启动时保留提示，方便了解当前状态。': '- Update installation failures and launch failures remain visible for '
                                    'troubleshooting.',
 '- 更新记录仅显示最近10个版本，默认展开最新版本，其他版本点击后查看。': '- Release Notes shows the latest 10 versions, with the newest '
                                         'expanded by default.',
 '- 窗口较窄时自动收起项目栏，放大后恢复；手动收起后保持关闭。': '- The project panel collapses automatically in narrow windows and '
                                    'returns when space is available. Manual collapse is preserved.',
 '- 简化模板列名确认，优先显示需要补充选择的内容，支持查看原表示例、筛选列名和定位未完成项。': '- Simplified column mapping to prioritize unresolved '
                                                   'fields, with source previews, column search, and issue '
                                                   'navigation.',
 '- 简化重复入口，缩小顶部留白，调整左右区域背景颜色，让界面更加清爽。': '- Removed redundant entry points, reduced header spacing, and '
                                        'refined panel backgrounds.',
 '- 统一复选框圆角样式，优化界面细节与操作体验。': '- Standardized checkbox corners and improved UI details.',
 '- 考勤与周月报中，“新增「公出」列”和“新增「出差」列”移至加班/调休单位右侧，窄窗口下支持横向滚动查看。': '- Added attendance business-duty and '
                                                           'business-trip options beside the '
                                                           'overtime/time-off unit selector, with horizontal '
                                                           'scrolling on narrow screens.',
 '- 考勤与周月报设置区域在窄窗口下支持横向滚动，避免日期输入框等控件被遮挡。': '- Attendance settings scroll horizontally in narrow windows to '
                                           'keep date inputs accessible.',
 '- 调整Windows左右侧栏开关的位置，与窗口控制按钮分开；左侧菜单固定展开时，收起图标显示在菜单右上角，Mac版保持不变。': '- Separated Windows sidebar controls '
                                                                    'from window buttons. The collapse '
                                                                    'control is at the top right of a pinned '
                                                                    'sidebar; macOS behavior is unchanged.',
 '- 调整Windows窗口样式，恢复带有工具Logo和名称的系统标题栏，窗口边框、圆角和阴影随系统支持情况显示。': '- Restored the Windows system title bar with '
                                                             'the app icon and name. Borders, corners, and '
                                                             'shadows follow system support.',
 '- 调整项目文件面板，项目名称居中显示，文件范围切换和搜索更清晰，“添加”和“刷新”保留图标及文字说明。': '- Refined the project panel with a centered '
                                                         'project name, clearer filtering and search, and '
                                                         'labeled Add and Refresh controls.',
 '- 项目文件入口移至右上角，点击图标即可展开或收起，展开后图标会跟随面板位置移动。': '- Moved the project panel toggle to the top right; it follows '
                                              'the panel when expanded.',
 '1 个 Excel 文件': 'One Excel file',
 '1 个 Excel 文件或文件夹': 'One Excel file or folder',
 '1 个 Excel、压缩包或文件夹': 'One Excel file, archive, or folder',
 '1 个文件夹': 'One folder',
 'Excel 工作簿 (*.xlsx *.xls);;所有文件 (*)': 'Excel Workbooks (*.xlsx *.xls);;All Files (*)',
 'Excel 或压缩包 (*.xlsx *.xls {0});;所有文件 (*)': 'Excel Files or Archives (*.xlsx *.xls {0});;All Files (*)',
 'Excel 顺序映射：上移/下移只移动姓名，文件位置和扩展名不变；搜索或筛选时禁用移动。所有已选项目校验通过后才能执行。': 'Excel order: Move Up/Down changes name '
                                                                 'assignments only; file positions and '
                                                                 'extensions stay unchanged. Reordering is '
                                                                 'disabled while filtering or searching. All '
                                                                 'included items must pass validation before '
                                                                 'execution.',
 'Excel、压缩包或文件夹，可多个': 'Excel files, archives, or folders; multiple selections allowed',
 'HR Toolkit 有新版本可用！': 'An HR Toolkit update is available.',
 'HR Workbench v{0} Qt Quick 启动（{1}，{2}，后端 {3}，渲染循环 {4}）': 'HR Workbench v{0} Qt Quick startup ({1}, {2}, '
                                                           'backend {3}, render loop {4})',
 'OCR 索引缓存写入失败：': 'Could not save the OCR index cache:',
 'OCR 缓存写入失败：': 'Could not save the OCR cache:',
 'Qt Quick 主界面加载失败：{0}': 'Could not load the Qt Quick main window: {0}',
 'Qt smoke 截图保存失败：{0}': 'Could not save the Qt smoke screenshot: {0}',
 'Qt smoke 截图失败：{0}': 'Qt smoke screenshot failed: {0}',
 'Windows 10 / 11（64 位）': 'Windows 10 / 11 (64-bit)',
 'Windows 7（64 位）': 'Windows 7 (64-bit)',
 '[文件] ': '[File] ',
 '[文件夹] ': '[Folder] ',
 '{0}\n请联网后重试，本次未复制任何地址。': '{0}\nConnect to the internet and try again. No link was copied.',
 '{0} 原因：{1}': '{0} Reason: {1}',
 '{0} 等 {1} 个': '{0} and {1} items in total',
 '{0} 等 {1} 个文件': '{0} and {1} files in total',
 '“{0}”已按当前勾选更新。': 'Updated “{0}” with the current selection.',
 '“{0}”的处理结果及已有历史资料会一起移到当前项目回收站，不会永久删除。是否继续？': 'Move the results and existing source files for “{0}” to this '
                                               "project's Trash? They will not be permanently deleted.",
 '”不能选同一列。': ' cannot use the same column.',
 '”和“': ' and ',
 '”在原表中的列': ' in the source workbook',
 '”在哪一列': ' column',
 '”对应的工作表。': ' worksheet.',
 '”工作表。': ' worksheet.',
 '”所在列': ' column',
 '✕ 清空': '✕ Clear',
 '。是否现在更新？': '. Update now?',
 '上一页': 'Previous',
 '上传 {0} · 结果 {1} · 补充 {2}': 'Source {0} · Results {1} · Additional {2}',
 '上传的源文件不再在项目中保留永久副本，仅保留结果；源文件请自行保管。': 'Projects retain results without keeping permanent copies of uploaded '
                                       'source files. Keep your originals.',
 '上传资料：{0}': 'Source files: {0}',
 '上周': 'Last week',
 '上月': 'Last month',
 '上次记录的项目位置无效，请通过“打开项目”重新选择。': 'The saved project location is invalid. Select it again using Open Project.',
 '上次运行 {0} · {1}': 'Last run {0} · {1}',
 '上移': 'Move Up',
 '下一页': 'Next',
 '下方几行没有内容，请核对原表': 'The rows below are empty. Check the source workbook.',
 '下次处理工资表时会使用这些名称。': 'These names will be used the next time you process payroll.',
 '下次处理相同表头时使用新选择。': 'The updated choices will be used for the same header layout next time.',
 '下移': 'Move Down',
 '下载地址已复制': 'Download link copied',
 '下载更新': 'Download Update',
 '不变': 'Unchanged',
 '不同资料不能选择同一工作表。': 'Different data types cannot use the same worksheet.',
 '不存在、无法访问或不是普通文件/文件夹': 'Missing, inaccessible, or not a regular file or folder',
 '不指定，保留原来的读取方式': 'Not specified; keep existing detection',
 '不支持此类型，这里只接收 1 个 Excel 文件（.xlsx / .xls）。': 'This input accepts one Excel file (.xlsx or .xls) only.',
 '不能带入回收站或项目内部资料。': 'Items in Trash or internal project data cannot be used as input.',
 '不能带入链接目录，请选择项目中的实际资料。': 'Linked folders cannot be used. Select the actual project files.',
 '不能带入项目根目录或分类栏目。': 'The project root and category headings cannot be used as input.',
 '不选择已有汇总表时，工具会按月份新建干净汇总表。缺少某个月份汇总表时也会自动创建。': 'Without an existing summary, a new summary is created for '
                                              'each month. Missing monthly summaries are also created '
                                              'automatically.',
 '业务核对': 'Business Review',
 '两项均留空不筛选月报': 'Leave both dates blank to include all monthly reports',
 '两项均留空按整月统计': 'Leave both dates blank to include the whole month',
 '为了保护历史原件，文件夹改名记录不能直接再次处理。': 'Rename batches cannot be rerun directly, to protect historical originals.',
 '主题': 'Theme',
 '人力资源分析表': 'HR Analysis Workbook',
 '人力资源花名册': 'Employee Roster',
 '人员与档案': 'People & Records',
 '人员名单 Excel': 'Employee Names Excel File',
 '人员文件夹目录': 'Employee Files Folder',
 '人员资料文件夹改名': 'Rename Employee Files & Folders',
 '仅保存': 'Save Only',
 '仅保存当前项目的自定义配置。同编号或同地区优先使用自定义配置，删除后恢复内置规则。': 'Custom settings apply to this project only. They override '
                                              'matching built-in region names or codes. Deleting them '
                                              'restores the defaults.',
 '仅做本地只读扫描，不复制原资料库，支持上万人超大资料库': 'Read-only local scanning without copying the source library; supports '
                                'libraries with thousands of employees',
 '仅带入选择，不移动原件。灰色选项表示该区域不支持此项。': 'Use as input without moving originals. Disabled options are not supported '
                                'by that input area.',
 '今天': 'Today',
 '今年': 'This year',
 '以前保存的资料已经放回当前功能，请确认后重新处理。': 'Previous files have been restored to this tool. Review them before running '
                              'again.',
 '优化部分操作细节，提升整体使用体验。': 'Improved everyday interactions and overall usability.',
 '使用教程': 'Help',
 '例如写着“姓名、身份证号码、公司”的那一行，不是标题或人员数据。': 'Select the row containing headers such as Name, ID Number, and '
                                     'Company, rather than the title or employee data.',
 '保单人员清单': 'Policy Enrollment Lists',
 '保存': 'Save',
 '保存位置': 'Save Location',
 '保存修改': 'Save Changes',
 '保存名称并重新检查': 'Save Names and Recheck',
 '保存失败，请重试': 'Could not save. Try again.',
 '保存常用名称': 'Save Common Names',
 '保存当前为新预设': 'Save Selection as New Preset',
 '保存自定义预设': 'Save Custom Preset',
 '保存项目界面设置失败': 'Could not save workspace preferences',
 '保留系统标题栏：{0}': 'Keeping the system title bar: {0}',
 '保险台账与增减预警': 'Insurance Ledger & Enrollment Alerts',
 '保险台账与预警': 'Insurance Ledger & Alerts',
 '修复 Mac 版没有可用更新时误报“检查更新失败”的问题。': 'Fixed update checks incorrectly failing on macOS when no update is '
                                  'available.',
 '修复任务尚未开始就创建输出目录、失败后残留空目录的问题。': 'Fixed empty output folders being created before tasks started or left '
                                 'behind after failures.',
 '修复刷新项目文件后，已展开的层级被收起的问题。': 'Fixed expanded folders collapsing after refreshing project files.',
 '修复医疗个人补差未计入个人补差合计的问题，补缴金额仍与补差分别统计。': 'Fixed individual medical insurance adjustments missing from '
                                       'adjustment totals. Back payments and adjustments remain separate.',
 '修复各险种补差表头日期互相串用的问题，每个险种只显示自己的补缴月份。': 'Fixed insurance adjustment headers sharing dates between categories. '
                                       'Each category now uses its own period.',
 '修复工资拆分后仍保留无人员区域、专业的小计行问题，同步调整相关合计。': 'Removed empty-region and empty-specialty subtotal rows from split '
                                       'payroll files and updated related totals.',
 '修复带薪休假漏计及天数换算不正确的问题，婚假、产假、陪护假、丧假、探亲假、工伤假和年假统一按天汇总。': 'Fixed missing paid leave and day conversions. '
                                                       'Marriage, maternity, caregiver, bereavement, home, '
                                                       'work-injury, and annual leave are summarized in '
                                                       'days.',
 '修复拖动文件带入时，只提供文件路径或松手过快导致无法带入的问题。': 'Fixed files failing to load when a drag supplied only paths or was '
                                     'released quickly.',
 '修复社保明细表导出后数据行丢失边框、比例显示成小数、金额没有格式的问题。': 'Fixed missing borders, percentage formats, and currency formats in '
                                         'exported social insurance details.',
 '修复考勤结果未按应汇报名单顺序排列的问题。': 'Attendance results now follow the expected reporters roster order.',
 '修复补缴月份显示为当前账单月份的问题，按实际补缴月份显示，并与当月正常缴费、补差分开列示。': 'Back-payment periods now use the actual months and are '
                                                  'listed separately from regular payments and adjustments.',
 '修复部分社保表中个人缴费金额漏读、个人与单位金额区分不正确的问题。': 'Fixed missed individual social insurance payments and incorrect '
                                      'distinctions between individual and employer amounts.',
 '修改': 'Edit',
 '修改列对应关系': 'Edit Column Mapping',
 '修改单人名称': 'Replace Full Name',
 '修改单人名称：填写原姓名和新名称，例如“张三”改为“章五”。': 'Replace Full Name: enter the exact original name and the new name, such '
                                   'as changing Zhang San to Wang Wu.',
 '修改后仅保存选择，不会开始处理文件。': 'This saves your choices without processing any files.',
 '修改对应列': 'Edit Mapped Column',
 '修改已记住的选择': 'Edit Saved Mapping',
 '修改或删除已记住的选择，不会修改原文件和已有结果。': 'Editing or deleting saved mappings does not change source files or existing '
                              'results.',
 '修改数据读取方式': 'Change Reading Mode',
 '停止处理': 'Stop',
 '全选': 'Select All',
 '全部': 'All',
 '全部功能': 'All Tools',
 '全部处理完成，结果已登记保存。': 'All processing is complete and the results have been saved.',
 '全部文件': 'All Files',
 '全部时间': 'Any Time',
 '全部（提取 OCR 识别到的该人员全部材料）': 'All materials identified for this employee by OCR',
 '全部（直接拷贝匹配到的人员整个文件夹）': 'All materials (copy the entire matching employee folder)',
 '共 {0} 项 · 待改名 {1} · 需处理 {2} · 已排除 {3} · 当前显示 {4}': 'Total {0} · To rename {1} · Issues {2} · Excluded {3} '
                                                     '· Showing {4}',
 '共找到 {0} 次处理记录': 'Found {0} processing records',
 '共有 {0} 条提醒。': 'There are {0} notices.',
 '关闭': 'Close',
 '关闭工作项目失败': 'Could not close the project',
 '关闭旧工作项目失败': 'Could not close the previous project',
 '关闭等待超过 10 秒；保留项目写锁并交由下次启动恢复未完成批次。': 'Shutdown exceeded 10 seconds. The project lock is retained; '
                                      'unfinished batches will be recovered on next startup.',
 '其他提醒': 'Other Notices',
 '内容预览：': 'Preview:',
 '内置': 'Built-in',
 '内置预设不能删除': 'Built-in presets cannot be deleted',
 '内置预设不能重命名': 'Built-in presets cannot be renamed',
 '内置预设会一直保留；自定义预设可以删除。': 'Built-in presets are always retained. Custom presets can be deleted.',
 '内置预设会一直保留；自定义预设可以重命名。': 'Built-in presets are always retained. Custom presets can be renamed.',
 '内置预设保持不变；删除仍需确认。': 'Built-in presets are unchanged. Deletion still requires confirmation.',
 '再次使用': 'Use Again',
 '列': 'columns',
 '列 · ': ' columns · ',
 '列名 / 工作表设置': 'Column & Worksheet Settings',
 '列名从第': 'Headers start at row',
 '列名在第 ': 'Header row: ',
 '列名设置': 'Column Names',
 '列头检查已停止。': 'Header review stopped.',
 '列头检查未完成': 'Header review incomplete',
 '列头设置已保存': 'Header settings saved',
 '创建': 'Create',
 '创建工作项目失败': 'Could not create the project',
 '创建并打开': 'Create and Open',
 '删除': 'Delete',
 '删除未能保存，请重试': 'Could not save the deletion. Try again.',
 '删除材料': 'Delete Material Type',
 '删除结尾文字': 'Remove Trailing Text',
 '删除结尾文字：输入“_劳动合同”，可删除“张三_劳动合同 / 张三-劳动合同 / 张三劳动合同”的结尾文字。': 'Remove Trailing Text: enter _Employment Contract '
                                                           'to remove the ending from names using an '
                                                           'underscore, a hyphen, or no separator.',
 '删除自定义材料': 'Delete Custom Material Type',
 '删除预设': 'Delete Preset',
 '刷新': 'Refresh',
 '确认过的资料内容已变化，确认记录失效，请重新核对': 'Previously confirmed files changed. Review them again.',
 '磁盘空间不足，无法安全解压更新包。': 'Insufficient disk space to extract the update safely.',
 '磁盘空间不足：安装更新约需 {0} MB 可用空间，当前仅剩 {1} MB。请清理磁盘后重试。': 'Update installation needs about {0} MB of free space, '
                                                    'but only {1} MB is available. Free disk space and '
                                                    'retry.',
 '社保报表生成完成': 'Social insurance reports generated',
 '社保数据检查完成': 'Social insurance validation complete',
 '社保明细表已生成，正在生成拆分明细...': 'Social insurance details generated. Creating split details…',
 '社保缴费清单文件、压缩包或文件夹不存在：{0}': 'Social insurance payment file, archive, or folder not found: {0}',
 '社保金额解析失败：{0} 第 {1} 行，列 {2}；已沿用原有空值处理，请核对源表。': 'Could not parse social insurance amount: {0}, row {1}, '
                                                'column {2}. Existing empty-value handling was retained; '
                                                'check the source.',
 '移入回收站时发现两个资料目录。': 'Two material folders found while moving to Trash.',
 '移入回收站未完成，自动恢复也遇到问题；资料仍保留，请关闭其他窗口后重试。': 'Move to Trash was incomplete and automatic recovery encountered a '
                                         'problem. Files are retained. Close other windows and retry.',
 '程序目录不存在：{0}': 'Application folder not found: {0}',
 '程序目录范围过大，已拒绝执行更新。': 'Application folder scope is too broad; update refused.',
 '等待主程序退出超时。': 'Timed out waiting for the app to exit.',
 '结果不是普通文件：{0}': 'Result is not a regular file: {0}',
 '结果文件不存在或是链接：{0}': 'Result file is missing or is a link: {0}',
 '结果文件夹不存在或不安全。': 'Results folder is missing or unsafe.',
 '结果文件已写入，正在交回项目登记': 'Results written; returning them for project registration',
 '编号须为 1 至 12 位数字，前导零会保留。': 'Code must contain 1–12 digits. Leading zeros are preserved.',
 '缺失索引备份不应包含数据库文件。': 'A missing-index backup must not contain database files.',
 '缺少 Windows .xls 转换依赖 pywin32。请在 Windows 打包环境执行 `python -m pip install -r requirements.txt` 后重新打包。': 'Windows '
                                                                                                      '.xls '
                                                                                                      'conversion '
                                                                                                      'requires '
                                                                                                      'pywin32. '
                                                                                                      'Install '
                                                                                                      'the '
                                                                                                      'Windows '
                                                                                                      'build '
                                                                                                      'dependencies '
                                                                                                      'and '
                                                                                                      'rebuild '
                                                                                                      'the '
                                                                                                      'package.',
 '考勤、周报、月报文件、压缩包或文件夹不存在：{0}': 'Attendance/report file, archive, or folder not found: {0}',
 '自定义材料最多可添加 {0} 种。': 'Up to {0} custom material types can be added.',
 '自定义预设最多可保存 {0} 个。': 'Up to {0} custom presets can be saved.',
 '花名册已存在增员身份证 {0}，未重复写入。': 'New employee ID {0} already exists in the roster; not duplicated.',
 '花名册有该在职人员，但保单清单中未找到。': 'This active employee appears in the roster but not in the policy list.',
 '花名册身份证重复但姓名不同：{0}，已保留首次记录 {1}。': 'Roster ID {0} has different names; kept the first record {1}.',
 '表头行不能超过 200': 'Header row cannot exceed 200',
 '表头行号必须大于等于 1。': 'Header row number must be at least 1.',
 '要删除的自定义预设不存在。': 'The custom preset to delete does not exist.',
 '要编辑的自定义预设不存在。': 'The custom preset to edit does not exist.',
 '解压后的文件大小超过安全上限': 'Extracted file exceeds the size limit',
 '识别引擎内存不足，已安全停止；当前资料未完成识别，原始资料未修改': 'Recognition engine ran out of memory. Stopped safely; the current '
                                     'document is incomplete and originals are unchanged.',
 '识别引擎启动时内存不足，已安全停止；当前资料未完成识别，原始资料未修改': 'Insufficient memory to start recognition. Stopped safely; the '
                                        'current document is incomplete and originals are unchanged.',
 '识别时可用内存不足，已安全停止；当前资料未完成识别，原始资料未修改': 'Insufficient memory during recognition. Stopped safely; the current '
                                      'document is incomplete and originals are unchanged.',
 '识别资料': 'Recognize Materials',
 '该名称是 Windows 系统保留名称，请换一个名称。': 'This name is reserved by Windows. Choose another name.',
 '该名称是项目保留名称，请换一个名称。': 'This name is reserved by the project. Choose another name.',
 '该文件夹名称属于项目保留名称，请换一个名称。': 'This folder name is reserved by the project. Choose another name.',
 '该文件夹未登记为本次处理来源。': 'This folder is not registered as a source for this run.',
 '请先选择本次工作表并点击重新读取列头': "Select this run's worksheet and click Read Headers again",
 '请填写原名称，例如：张三': 'Enter the original name, such as Zhang San',
 '请填写替换后的名称': 'Enter the new name',
 '请填写替换后的名称，例如：章五': 'Enter the new name, such as Wang Wu',
 '请填写替换后的文字': 'Enter the replacement text',
 '请填写要删除的结尾文字，例如：劳动合同、-劳动合同 或 _身份证': 'Enter the trailing text to remove, including any desired separator',
 '请填写要处理的原文字': 'Enter the original text to process',
 '请填写要替换的原文字': 'Enter the text to find',
 '请填写要追加的文字，建议以 - 或 _ 开头，例如：-劳动合同': 'Enter the text to append, including a separator such as - or _ if '
                                    'needed',
 '请至少选择一个{0}的列名': 'Select at least one column for {0}',
 '请至少选择一项金额对应列；个人、单位及险种不同的金额请分别选择': 'Select at least one amount column. Individual, employer, and different '
                                    'insurance amounts must use separate columns.',
 '请选择 1—200 行内的表头，连续表头最多 6 行': 'Select headers within rows 1–200, with no more than 6 consecutive rows',
 '请选择 Excel 名单或映射表': 'Select an Excel roster or mapping workbook',
 '请选择 Windows 7 或 Windows 10 / 11。': 'Select Windows 7 or Windows 10/11.',
 '请选择{0}对应的原表列': 'Select the source column for {0}',
 '请选择“{0}”在原表中的列': 'Select the source column for “{0}”',
 '请选择“{0}”对应的工作表': 'Select the worksheet for “{0}”',
 '请选择对应工作表': 'Select the corresponding worksheet',
 '请选择文件夹作为处理资料：{0}': 'Select a folder as input: {0}',
 '请选择本次文件中的工作表与表头行': 'Select the worksheet and header rows in this file',
 '请选择要复用的项目文件或文件夹。': 'Select the project file or folder to reuse.',
 '请选择要导入的文件夹。': 'Select a folder to import.',
 '请选择要导入的文件或文件夹。': 'Select files or folders to import.',
 '读取 .xls 参保人员花名册需要 xlrd，请先安装依赖。': 'Reading a legacy .xls roster requires xlrd. Install the dependencies '
                                   'first.',
 '读取 .xls 社保清单需要 xlrd，请先安装依赖。': 'Reading legacy .xls social insurance files requires xlrd. Install the '
                                'dependencies first.',
 '资料仍在整理中，请稍后再试。': 'Files are still being organized. Try again later.',
 '资料只能导入到上传资料或补充资料。': 'Files can be imported only as sources or additional materials.',
 '资料处理结束': 'Material Processing Finished',
 '资料库不能放在程序安装目录内。': 'The library cannot be inside the app installation folder.',
 '资料库位置不能是链接目录。': 'The library location cannot be a linked folder.',
 '资料库位置已被其他文件占用，请使用 HRToolkit 专用文件夹。': 'Another file occupies the library location. Use a dedicated HR '
                                       'Toolkit folder.',
 '资料库位置过于宽泛，请选择专用文件夹。': 'The library location is too broad. Choose a dedicated folder.',
 '资料库标记不匹配，为保护现有文件，已停止使用该目录。': 'Library marker mismatch. Access stopped to protect existing files.',
 '资料库目录不存在：{0}': 'Library folder not found: {0}',
 '资料库空间不足，需要约 {0} GB，当前可用 {1} GB。': 'Library needs about {0} GB of free space; {1} GB is available.',
 '资料库路径包含链接或系统重定向目录。': 'Library path contains a link or redirected system folder.',
 '资料库路径无效。': 'Invalid library path.',
 '资料库路径越界。': 'Library path is outside the allowed location.',
 '资料快照不完整：{0}': 'Incomplete material snapshot: {0}',
 '资料快照位置无效：{0}': 'Invalid material snapshot location: {0}',
 '资料文件在检索后无法读取，已跳过：{0}': 'Material file could not be read after retrieval; skipped: {0}',
 '资料文件在索引后发生变化，已跳过并请重新运行：{0}': 'Material file changed after indexing; skipped. Run again: {0}',
 '资料文件复制后校验不一致，已移除结果并请重新运行：{0}': 'Copied material failed verification. The result was removed; run again: '
                                 '{0}',
 '资料识别失败，已跳过 {0}：{1}': 'Recognition failed; skipped {0}: {1}',
 '路径不存在：{0}': 'Path not found: {0}',
 '身份证 {0} {1} 已存在金额，未覆盖（来源：{2} 第 {3} 行）': 'ID {0}, {1}: an amount already exists and was not overwritten '
                                          '(source: {2}, row {3})',
 '身份证 {0} 出现多个姓名：{1} / {2}': 'ID {0} has multiple names: {1} / {2}',
 '身份证 {0} 在 {1} 出现重复记录，金额已累加': 'Duplicate records for ID {0} in {1}; amounts added together',
 '输入文件不存在：{0}': 'Input file not found: {0}',
 '这条旧版记录未保存列名，请删除后重新处理原文件，重新选择对应列': 'This legacy record has no saved columns. Delete it and reprocess the '
                                    'source to select columns again.',
 '这条选择已不存在，请重新打开设置': 'This mapping no longer exists. Reopen settings.',
 '远程更新配置不能引用本机文件。': 'Remote update configuration cannot refer to local files.',
 '退出码 {0}': 'Exit code {0}',
 '部分历史任务缺少清单或目录结构异常，已停止发布新索引。': 'Some historical tasks have missing manifests or invalid folder structures. '
                                'A new index was not created.',
 '部分历史清单未通过完整校验，已停止发布新索引。': 'Some historical manifests failed verification. A new index was not created.',
 '部分图片或扫描版 PDF 暂时无法完成 OCR，未写入负缓存；下次查询会自动重试。': 'Some images or scanned PDFs could not complete OCR. No '
                                              'negative cache was saved; the next query will retry them.',
 '部分输入未能完整读取，请处理后重新合并：\n': 'Some inputs could not be fully read. Resolve these issues and merge again:\n',
 '部分输入未能完整读取，请检查：\n': 'Some inputs could not be fully read. Check:\n',
 '重建后的历史索引关联校验失败。': 'Rebuilt history index failed relationship verification.',
 '需减保': 'Remove Coverage',
 '需加保': 'Add Coverage',
 '需要文件夹资料：{0}': 'Folder input required: {0}',
 '项目不能放在程序安装目录。': 'Projects cannot be inside the app installation folder.',
 '项目临时目录包含不安全项目。': 'Project temporary folder contains unsafe items.',
 '项目位置不是安全的普通文件夹。': 'Project location is not a safe regular folder.',
 '项目位置不能是链接或系统重定向目录。': 'Project location cannot be a link or redirected system folder.',
 '项目位置过于宽泛，请选择专用子文件夹。': 'Project location is too broad. Choose a dedicated subfolder.',
 '项目名称不能为空': 'Project name cannot be empty',
 '项目名称不能为空。': 'Project name cannot be empty.',
 '项目名称不能使用英文句点。': 'Project name cannot consist of a period.',
 '项目名称不能包含 \\ / : * ? " < > |。': 'Project name cannot contain \\ / : * ? " < > |.',
 '项目名称不能包含换行或控制字符。': 'Project name cannot contain line breaks or control characters.',
 '项目名称不能超过 {0} 个字。': 'Project name cannot exceed {0} characters.',
 '项目名称末尾不能使用句点。': 'Project name cannot end in a period.',
 '项目回收站包含不安全项目。': 'Project Trash contains unsafe items.',
 '项目已经关闭。': 'The project is closed.',
 '项目批次仍未进入安全结束状态。': 'The batch has not reached a safe finished state.',
 '项目文件与批次不一致。': 'Project file does not match the batch.',
 '项目文件分类无效。': 'Invalid project file category.',
 '项目文件夹与批次不一致。': 'Project folder does not match the batch.',
 '项目文件夹结构与原清单不一致，不能作为新批次输入。': 'Project folder structure differs from the original manifest and cannot be '
                              'used as new input.',
 '项目文件夹路径不属于批次目录。': 'Project folder path does not belong to the batch folder.',
 '项目文件夹路径不能指向批次目录本身。': 'Project folder path cannot point to the batch folder itself.',
 '项目文件校验值无效。': 'Invalid project file checksum.',
 '项目文件路径不属于批次目录。': 'Project file path does not belong to the batch folder.',
 '项目文件路径不能指向批次目录本身。': 'Project file path cannot point to the batch folder itself.',
 '项目来源不存在或是链接：{0}': 'Project source is missing or is a link: {0}',
 '项目来源不是普通文件或文件夹：{0}': 'Project source is not a regular file or folder: {0}',
 '项目标记缺少 {0}。': 'Project marker is missing {0}.',
 '项目标记缺少必要信息。': 'Project marker is missing required information.',
 '项目根目录不安全。': 'Unsafe project root.',
 '项目正在另一个 HRToolkit 窗口中使用。': 'The project is in use in another HR Toolkit window.',
 '项目清单格式无效：{0}': 'Invalid project manifest format: {0}',
 '项目版本无效，不能安全打开。': 'Invalid project version; cannot open safely.',
 '项目目录不存在：{0}': 'Project folder not found: {0}',
 '项目相对路径无效。': 'Invalid project-relative path.',
 '项目空间不足，需要约 {0} GB，当前可用 {1} GB。': 'Project needs about {0} GB of free space; {1} GB is available.',
 '项目资料与原清单不一致，不能作为新批次输入。': 'Project files differ from the original manifest and cannot be used as new input.',
 '项目资料与原清单不一致，不能复用：{0}': 'Project files differ from the original manifest and cannot be reused: {0}',
 '项目资料已发生变化：{0}': 'Project files changed: {0}',
 '项目资料批量快照数量不完整。': 'Batch material snapshot count is incomplete.',
 '项目路径不能经过链接或系统重定向目录。': 'Project path cannot traverse links or redirected system folders.',
 '项目路径包含链接或系统重定向目录。': 'Project path contains links or redirected system folders.',
 '项目路径越界。': 'Project path is outside the allowed location.',
 '项目隐藏管理目录不能作为处理资料。': 'Hidden project management files cannot be used as processing input.',
 '预览存在冲突，请修正或排除后重试：': 'Preview contains conflicts. Resolve or exclude them before trying again:',
 '预设“{0}”已经存在。': 'Preset “{0}” already exists.',
 '预设包含不存在的材料：{0}。': 'Preset contains nonexistent material types: {0}.',
 '预设至少需要选择一种材料。': 'A preset must include at least one material type.',
 '（后台线程）': '(background thread)',
 '（独立进程）': '(separate process)',
 '（退出码 {0}）。': '(exit code {0}).',
 '，缓存文件：{0}': '; cache file: {0}',
 '人力资源花名册目前只支持 .xlsx 或 .xls 文件。': 'The employee roster must be .xlsx or .xls.',
 '人员资料文件夹不存在或是链接。': 'The employee folder is missing or is a link.',
 '人员资料文件夹快照不完整。': 'The employee folder snapshot is incomplete.',
 '仅支持 .xlsx 或 .xls 文件。': 'Only .xlsx and .xls files are supported.',
 '以下档案工作表没有“离职时间”或“离职日期”列，已自动追加“离职时间”列：{0}': 'These archive sheets had no departure-date column; one was '
                                             'added automatically: {0}',
 '保单人员清单、压缩包或文件夹不存在：{0}': 'Policy list, archive, or folder not found: {0}',
 '保单清单有该人员，但人力资源分析表花名册中未找到。': 'This policyholder was not found in the HR analysis roster.',
 '保单清单有该人员，但花名册状态为“{0}”。': "This policyholder's roster status is “{0}”.",
 '保单身份证 {0} 出现不同姓名：{1}、{2}，已保留首次姓名。': 'Policy ID {0} has different names: {1}, {2}. The first name was kept.',
 '保存待确认清单': 'Save Review List',
 '保存汇总报告': 'Save Summary Report',
 '保存目录不能在资料库目录内部（会导致循环嵌套复制）：\n资料库：{0}\n保存目录：{1}\n请选择一个位于资料库外部的独立文件夹作为保存目录。': 'The output folder cannot be '
                                                                             'inside the library; that would '
                                                                             'cause recursive copying.\n'
                                                                             'Library: {0}\n'
                                                                             'Output: {1}\n'
                                                                             'Choose a separate folder '
                                                                             'outside the library.',
 '保存识别缓存': 'Save Recognition Cache',
 '关联合同页面': 'Link Contract Pages',
 '内置和自定义名称合计不能超过 100 个': 'Built-in and custom aliases together cannot exceed 100 names',
 '内置材料不能删除。': 'Built-in material types cannot be deleted.',
 '内置预设不能删除。': 'Built-in presets cannot be deleted.',
 '内置预设不能覆盖，请使用其他名称。': 'Built-in presets cannot be overwritten. Use another name.',
 '准备改名 {0}/{1}': 'Preparing rename {0}/{1}',
 '准备资料': 'Prepare Files',
 '减员人员未在花名册找到：{0}': 'Departing employee not found in roster: {0}',
 '加班/调休单位只支持 day（按天）或 hour（按小时）。': 'The overtime/time-off unit must be day or hour.',
 '匹配人员资料': 'Match Employee Materials',
 '单份资料的 OCR 文字超过安全上限，请拆分后重试': 'OCR text for one document exceeds the limit. Split the document and try '
                              'again.',
 '历史任务信息无效': 'Invalid historical task metadata',
 '历史任务状态无效': 'Invalid historical task status',
 '历史任务目录层级无效': 'Invalid historical task folder hierarchy',
 '历史任务索引不存在': 'Historical task index missing',
 '历史任务编号与目录不一致': 'Historical task ID does not match its folder',
 '历史任务编号无效': 'Invalid historical task ID',
 '历史任务编号无效。': 'Invalid historical task ID.',
 '历史任务编号重复': 'Duplicate historical task ID',
 '历史原件已发生变化，不能继续使用：{0}': 'A historical original changed and cannot be reused: {0}',
 '历史原件已被移动或删除：{0}': 'A historical original was moved or deleted: {0}',
 '历史原件校验不一致，不能再次使用：{0}': 'A historical original failed verification and cannot be reused: {0}',
 '历史原件缺少校验记录，不能再次使用：{0}': 'A historical original has no verification record and cannot be reused: {0}',
 '历史文件不存在或不安全': 'Historical file missing or unsafe',
 '历史文件不属于当前任务': 'Historical file does not belong to this task',
 '历史文件不属于待恢复任务': 'Historical file does not belong to the task being recovered',
 '历史文件信息无效': 'Invalid historical file metadata',
 '历史文件列表无效': 'Invalid historical file list',
 '历史文件大小不一致': 'Historical file size mismatch',
 '历史文件校验不一致': 'Historical file verification mismatch',
 '历史文件校验值无效': 'Invalid historical file checksum',
 '历史文件类型无效': 'Invalid historical file type',
 '历史文件类型无效。': 'Invalid historical file type.',
 '历史文件词法路径不属于当前任务': 'Historical file path does not belong to this task',
 '历史文件路径包含链接或无效层级': 'Historical file path contains a link or invalid hierarchy',
 '历史文件路径同时指向两个位置': 'Historical file path points to two locations',
 '历史文件路径无效': 'Invalid historical file path',
 '历史清单不存在或不安全': 'Historical manifest missing or unsafe',
 '历史清单与任务不一致': 'Historical manifest does not match the task',
 '历史清单位置无法确认': 'Historical manifest location cannot be verified',
 '历史清单版本无效': 'Invalid historical manifest version',
 '历史目录位置无法唯一确认': 'Historical folder location cannot be uniquely identified',
 '历史索引与文件位置不一致': 'Historical index and file location do not match',
 '历史索引仍在变化，请关闭其他 HRToolkit 窗口后重试。': 'The history index is still changing. Close other HR Toolkit windows and '
                                    'try again.',
 '历史索引发布路径无效。': 'Invalid history index destination.',
 '历史索引已损坏，原索引已安全备份在 {0}，但自动整理失败：{1}': 'The damaged history index was safely backed up to {0}, but automatic '
                                      'repair failed: {1}',
 '历史索引恢复标记无法核对，为保护资料已停止恢复：{0}': 'The history recovery marker could not be verified. Recovery stopped to '
                                'protect files: {0}',
 '历史索引检查临时目录不安全。': 'Unsafe temporary folder for history index checks.',
 '历史记录清单与任务不一致，为保护其他资料，已停止移动。': 'The history manifest does not match the task. Moving stopped to protect '
                                'other files.',
 '历史记录清单无法核对，为保护其他资料，已停止移动。': 'The history manifest could not be verified. Moving stopped to protect other '
                              'files.',
 '历史记录目录不安全，已停止写入。': 'Unsafe history folder; writing stopped.',
 '历史记录目录无效。': 'Invalid history folder.',
 '历史记录目录无效，为保护其他资料，已停止移动。': 'Invalid history folder; moving stopped to protect other files.',
 '历史记录锁文件不安全。': 'Unsafe history lock file.',
 '历史记录锁目录不安全。': 'Unsafe history lock folder.',
 '历史资料库不是 HRToolkit 创建的，为保护现有数据，已停止使用。': 'This history library was not created by HR Toolkit. Access stopped '
                                         'to protect existing data.',
 '历史资料库版本不兼容：{0}': 'Incompatible history library version: {0}',
 '历史资料库结构不匹配，为保护现有数据，已停止使用。': 'History library structure mismatch. Access stopped to protect existing data.',
 '历史资料库结构无法识别，为保护现有数据，已停止使用。': 'Unrecognized history library structure. Access stopped to protect existing '
                               'data.',
 '历史资料库缺少必要数据表，为保护现有数据，已停止使用。': 'Required history tables are missing. Access stopped to protect existing '
                                'data.',
 '压缩包上下文目录名称无效': 'Invalid archive context folder name',
 '压缩包包含文件与目录路径冲突：{0}': 'Archive contains a file/folder path conflict: {0}',
 '压缩包包含无效的文件大小': 'Archive contains an invalid file size',
 '压缩包包含重复路径：{0}': 'Archive contains duplicate paths: {0}',
 '压缩包成员名称包含不支持的换行符': 'Archive member name contains unsupported line breaks',
 '压缩包成员实际大小不一致：{0}': "Archive member's actual size differs from its metadata: {0}",
 '压缩包成员路径不安全：{0}': 'Unsafe archive member path: {0}',
 '压缩包文件数量超过 {0} 个安全上限': 'Archive exceeds the limit of {0} files',
 '压缩包的整体压缩比例异常': "Archive's overall compression ratio is outside the allowed range",
 '压缩包解压后的总大小超过安全上限': 'Total extracted archive size exceeds the limit',
 '压缩资料': 'Compress Files',
 '原历史目录无效': 'Invalid original history folder',
 '原始文件不存在或是链接：{0}': 'Source file is missing or is a link: {0}',
 '参保人员花名册不存在：{0}': 'Insured employee roster not found: {0}',
 '参保人员花名册中未识别到人员数据。': 'No employee data recognized in the insured roster.',
 '参保人员花名册仅支持 .xlsx 或 .xls 文件。': 'The insured roster must be .xlsx or .xls.',
 '只有已成功完成批次的处理结果可以复用。': 'Only results from successfully completed batches can be reused.',
 '只有正在处理的批次可以写入结果。': 'Results can be written only for a running batch.',
 '只有正在处理的批次可以建立结果副本。': 'A results copy can be created only for a running batch.',
 '只有正在处理的批次可以登记结果。': 'Results can be registered only for a running batch.',
 '只有正在处理的批次可以结束。': 'Only a running batch can be finalized.',
 '只有草稿批次可以开始处理。': 'Only a draft batch can start processing.',
 '只能从本次批次的上传资料建立结果副本。': "Results copies must be created from this batch's uploaded files.",
 '只能写入当前项目中的普通目录。': 'Only regular folders in the current project can be written to.',
 '只能创建清单中声明的补充资料目录。': 'Only additional-material folders declared in the manifest can be created.',
 '只能复用共用资料或批次中的上传、补充、已完成结果。': 'Only shared files, uploaded files, additional materials, or completed results '
                              'can be reused.',
 '只能复用清单中已登记且未改动的项目文件。': 'Only registered, unchanged project files can be reused.',
 '只能登记当前批次结果目录中的文件。': "Only files in this batch's results folder can be registered.",
 '只能重命名自定义预设。': 'Only custom presets can be renamed.',
 '合同': 'Contract',
 '合同人员归属冲突，未提取：{0}': 'Conflicting contract ownership; not retrieved: {0}',
 '合同分组待确认：{0} 有 {1} 张候选，未进行全量两两比较': 'Contract grouping needs review: {0} has {1} candidates; exhaustive '
                                    'pairwise comparison was not performed',
 '同一批次的资料目录不在一起。': "The batch's material folders are not together.",
 '同名恢复记录过多，请先整理该功能下的项目文件。': "Too many recovery records share this name. Organize this tool's project files "
                            'first.',
 '同名批次过多，请调整业务说明或期间。': 'Too many batches share this name. Change the description or period.',
 '同名文件过多，无法导入：{0}': 'Too many files share this name; cannot import: {0}',
 '同名文件过多，无法归档：{0}': 'Too many files share this name; cannot archive: {0}',
 '名单中存在同名人员；无身份证号可核对的同名资料不会自动归属，请补充身份证号后重试。': 'The roster has duplicate names. Documents without an ID '
                                              'number will not be assigned automatically. Add ID numbers and '
                                              'try again.',
 '名单比筛选后的项目多 {0} 人；以下姓名没有对应项目：{1}': 'The roster has {0} more names than matching items. Unassigned names: '
                                    '{1}',
 '名单比筛选后的项目少 {0} 个；以下项目保持原名：{1}': 'The roster has {0} fewer names than matching items. These items keep '
                                  'their names: {1}',
 '名称规则包含当前工具不支持的字段或工作表': 'Naming rules include fields or worksheets unsupported by this tool',
 '名称规则格式无效': 'Invalid naming-rule format',
 '名称规则格式无效，请重新设置': 'Invalid naming-rule format. Configure the rules again.',
 '名称须为不超过 200 字的非空文字': 'Names must be nonempty text with no more than 200 characters',
 '后台处理已开始，但工作进程通信意外中断': 'Background processing started, but communication with the worker was interrupted',
 '后台处理没有返回结果。': 'Background processing returned no result.',
 '后台处理进程尚未就绪，通信已中断': 'Worker communication was interrupted before it became ready',
 '后台处理进程异常退出（退出码 {0}）。': 'Background worker exited unexpectedly (exit code {0}).',
 '后台处理进程未就绪即退出（退出码 {0}）。': 'Background worker exited before becoming ready (exit code {0}).',
 '员工【{0}】：{1}': 'Employee {0}: {1}',
 '周报': 'Weekly Report',
 '周报统计的开始日期不能晚于结束日期。': 'The weekly report start date cannot be after the end date.',
 '周报统计的开始日期和结束日期需要同时填写，或同时留空。': 'Enter both weekly report dates, or leave both blank.',
 '周报超时': 'Late Weekly Report',
 '回收站中已存在同一批次。': 'This batch already exists in Trash.',
 '回收站中的批次资料不存在。': 'Batch files are missing from Trash.',
 '回收站原位置与批次信息不一致。': 'The original Trash location does not match batch metadata.',
 '回收站恢复名称与目标位置不一致。': 'The restored name does not match the target location.',
 '回收站恢复路径越界。': 'The restore path is outside the allowed location.',
 '回收站批次目录与编号不一致。': 'The Trash batch folder does not match its ID.',
 '回收站清单包含重复的登记文件。': 'The Trash manifest contains duplicate registered files.',
 '回收站清单缺少原位置。': 'The Trash manifest is missing the original location.',
 '回收站清单缺少移入时间。': 'The Trash manifest is missing the removal time.',
 '回收站目录无效': 'Invalid Trash folder',
 '回收站移动恢复标记名称无效。': 'Invalid Trash recovery marker name.',
 '回收站资料中存在未登记文件：{0}{1}': 'Unregistered files in Trash: {0}{1}',
 '图片展开尺寸超过安全上限，未执行 OCR；请缩小或拆页后重试': 'Image dimensions exceed the limit; OCR was not run. Resize or split the '
                                   'image and try again.',
 '图片超过 1200 万像素安全上限，未执行 OCR；请缩小或拆页后重试': 'Image exceeds 12 megapixels; OCR was not run. Resize or split the '
                                        'image and try again.',
 '图片超过 32 MB 安全上限，未执行 OCR；请缩小或拆页后重试': 'Image exceeds 32 MB; OCR was not run. Resize or split the image and '
                                      'try again.',
 '图片过长，未执行 OCR；请将长图拆成普通页面后重试': 'Image is too long; OCR was not run. Split it into standard pages and try '
                               'again.',
 '地区名称不能为空，且不能包含控制字符。': 'Region name cannot be blank or contain control characters.',
 '地区编号配置格式无效，请修正后再处理。': 'Invalid region-code configuration format. Correct it before processing.',
 '地区编号配置版本无效，请修正后再处理。': 'Invalid region-code configuration version. Correct it before processing.',
 '处理失败，且项目未能安全结案：{0}；{1}': 'Processing failed and the project could not be finalized safely: {0}; {1}',
 '处理期间源文件发生变化，请关闭源文件后重新处理。': 'A source file changed during processing. Close it and try again.',
 '处理结果中仍有未登记文件：{0}{1}': 'Results still contain unregistered files: {0}{1}',
 '处理结果只能由工具生成并登记。': 'Results must be generated and registered by the tool.',
 '处理结果目录中已存在同名文件夹：{0}': 'A folder with the same name already exists in results: {0}',
 '备份期间历史索引仍在变化，请关闭其他 HRToolkit 窗口后重试。': 'The history index is changing during backup. Close other HR Toolkit '
                                        'windows and retry.',
 '备份期间历史索引发生变化。': 'The history index changed during backup.',
 '复制失败：{0} → {1}: {2}': 'Copy failed: {0} → {1}: {2}',
 '复制期间文件发生变化，请关闭文件后重试：{0}': 'File changed while being copied. Close it and retry: {0}',
 '复制期间来源文件被移动：{0}': 'Source file moved during copying: {0}',
 '多页文档中的文件在索引后发生变化，整组已跳过并请重新运行：{0}': 'A file in a multi-page document changed after indexing. The entire '
                                     'group was skipped; run again: {0}',
 '姓名、身份证号码和应发工资必须对应不同的列': 'Name, ID number, and gross pay must use different columns',
 '安装已完成，但未找到新版本主程序：{0}': 'Installation finished, but the new executable was not found: {0}',
 '安装已完成，但未检测到新版本窗口，请手动打开工具。': 'Installation finished, but no new app window was detected. Open the app '
                              'manually.',
 '安装程序执行失败（退出码 {0}）': 'Installer failed (exit code {0})',
 '完成 {0}，耗时 {1} 秒': 'Completed {0} in {1} seconds',
 '完成后的项目已变化，保留现场': 'A completed item changed; preserving the current state',
 '客户端更新仅使用 Gitee，不会访问 GitHub。': 'In-app updates use Gitee only and do not access GitHub.',
 '宽表中未识别险种金额列。': 'No insurance amount columns recognized in the wide-format table.',
 '导入临时文件不完整：{0}': 'Temporary import file is incomplete: {0}',
 '导入临时路径越界。': 'Temporary import path is outside the allowed location.',
 '导入恢复文件与批次不一致。': 'Import recovery file does not match the batch.',
 '导入恢复文件信息无效。': 'Invalid import recovery file metadata.',
 '导入恢复文件分类无效。': 'Invalid import recovery file category.',
 '导入恢复文件列表无效。': 'Invalid import recovery file list.',
 '导入恢复文件夹不属于当前批次。': 'Import recovery folder does not belong to this batch.',
 '导入恢复文件夹与批次不一致。': 'Import recovery folder does not match the batch.',
 '导入恢复文件夹信息无效。': 'Invalid import recovery folder metadata.',
 '导入恢复文件夹分类无效。': 'Invalid import recovery folder category.',
 '导入恢复文件夹列表无效。': 'Invalid import recovery folder list.',
 '导入恢复目标不属于当前批次。': 'Import recovery target does not belong to this batch.',
 '导入恢复记录无效。': 'Invalid import recovery record.',
 '导入文件夹目标发生冲突：{0}': 'Imported folder target conflict: {0}',
 '导入文件路径越界。': 'Import file path is outside the allowed location.',
 '导入目标发生冲突，未覆盖：{0}': 'Import target conflict; nothing overwritten: {0}',
 '导入目标发生冲突：{0}': 'Import target conflict: {0}',
 '导入目标路径越界。': 'Import target path is outside the allowed location.',
 '工作表没有关联的工作簿，无法解析样式下标。': 'The worksheet has no associated workbook; style indexes cannot be resolved.',
 '工具信息不能为空。': 'Tool information cannot be empty.',
 '工资明细和工资汇总不能选择同一工作表': 'Payroll details and summary cannot use the same worksheet',
 '工资表文件、压缩包或文件夹不存在：{0}': 'Payroll file, archive, or folder not found: {0}',
 '已使用当前选择的汇总表，原文件由用户自行保存。': 'Using the selected summary. Keep the original file yourself.',
 '已保存 {0} 档案表：{1}/{2}': 'Saved {0} archive: {1}/{2}',
 '已保存的对应列无效': 'Invalid saved column mapping',
 '已保存的模板对应关系无效': 'Invalid saved template mapping',
 '已发现 {0} 个文件': 'Found {0} files',
 '已启用省内存识别，处理速度可能稍慢，原始资料保持不变': 'Memory-saving recognition enabled. Processing may be slower; source files '
                               'are unchanged.',
 '已复制原件但未完成身份核对：{0}；{1}': 'Original copied; identity not verified: {0}; {1}',
 '已按 Windows 进程信息校正启动路径（GetModuleFileNameW）。': 'Corrected the startup path using Windows process information '
                                               '(GetModuleFileNameW).',
 '已改名 {0}/{1}': 'Renamed {0}/{1}',
 '已有公司档案表文件、压缩包或文件夹不存在：{0}': 'Existing company archive file, archive, or folder not found: {0}',
 '已有汇总表不存在：{0}': 'Existing summary not found: {0}',
 '已有汇总表中身份证 {0} 出现重复行，仅保留第一行': 'Duplicate rows for ID {0} in the existing summary; kept the first',
 '已有汇总表未找到月份列，请确认表头包含 202601 这类月份': 'No month columns found in the existing summary. Check for headers such '
                                    'as 202601.',
 '已检查列头 {0}/{1}': 'Checked headers {0}/{1}',
 '已登记结果发生变化，请保存为新文件：{0}': 'A registered result changed. Save it as a new file: {0}',
 '已确认多页劳动合同边界，但未识别到可核对的姓名、证件号或手机号，未自动归属员工：{0}': 'Multi-page contract boundaries confirmed, but no verifiable '
                                                'name, ID, or phone number was recognized. No employee '
                                                'assigned: {0}',
 '已读取 {0} 条档案，开始生成公司档案表...': 'Read {0} archive records. Generating company archives…',
 '应汇报人员名单不存在：{0}': 'Expected reporters roster not found: {0}',
 '应汇报人员名单只支持 .xlsx 或 .xls 文件。': 'The expected reporters roster must be .xlsx or .xls.',
 '建立结果副本期间源文件变化：{0}': 'Source changed while creating the results copy: {0}',
 '开始 {0}（{1} 个资料来源，仅读取原文件，项目只保存结果）': 'Starting {0} ({1} sources; originals are read-only and only results '
                                     'are saved to the project)',
 '开始 {0}（资料库只读检索，原件保留在原目录）': 'Starting {0} (read-only library search; originals stay in place)',
 '异动汇总表文件或文件夹不存在：{0}': 'Personnel-change summary file or folder not found: {0}',
 '异动汇总表缺少工作表：{0}': 'Personnel-change summary is missing a worksheet: {0}',
 '异动表文件、压缩包或文件夹不存在：{0}': 'Personnel-change file, archive, or folder not found: {0}',
 '异动记录非空字段冲突：{0}，{1}第 {2} 行，对应汇总表第 {3} 行，列 {4}；已保留原值。': 'Conflicting nonempty personnel-change field: {0}, '
                                                        '{1} row {2}, summary row {3}, column {4}. Original '
                                                        'value retained.',
 '当前安装包缺少 PDF 文字解析组件，请重新安装完整版本': 'The app is missing PDF text components. Reinstall the complete package.',
 '当前安装包缺少 PDF 页面解析组件，请重新安装完整版本': 'The app is missing PDF page components. Reinstall the complete package.',
 '当前工资拆分工具仅支持 .xlsx 或 .xls 文件': 'Payroll splitting supports .xlsx or .xls files only',
 '当前平台使用手动安装包，不能交给自动更新器。': 'This platform requires manual installation and cannot use the automatic updater.',
 '当前批次不支持直接读取源文件。': 'This batch does not support direct source-file access.',
 '当前批次状态不允许继续导入资料。': "The batch's current status does not allow further imports.",
 '当前版本无法安全建立文件夹处理副本。': 'This version cannot safely create a working folder copy.',
 '当前版本无法安全留存文件夹结构。': 'This version cannot safely retain folder structure.',
 '当前版本暂时不能复用项目内资料，请从原文件位置重新选择。': 'This version cannot reuse project files yet. Select them from their '
                                 'original locations.',
 '当前系统不支持安全的排他改名，本次未改名': 'This system does not support safe exclusive renaming. Nothing was renamed.',
 '待改名目录或人员名单在预览确认后发生了变化，本次未执行。请重新预览并确认。': 'The folder or roster changed after preview confirmation. Nothing '
                                          'was executed. Preview and confirm again.',
 '待改名项目在预览确认后发生了变化，本次未执行。请重新预览并确认。': 'Items changed after preview confirmation. Nothing was executed. '
                                     'Preview and confirm again.',
 '待确认清单中的人员无法唯一对应当前名单，未应用：{0}': 'Review-list employees cannot be uniquely matched to the current roster; '
                                'choices not applied: {0}',
 '待确认清单存在失效的选择，未应用：{0}': 'Review list contains expired selections; not applied: {0}',
 '待确认清单存在相互冲突的选择，未应用：{0}': 'Review list contains conflicting selections; not applied: {0}',
 '待确认清单无法读取，保留待确认状态：{0}；{1}': 'Review list could not be read; review is still required: {0}; {1}',
 '待确认清单累计超过 20000 行，请在最近一次清单中分批确认': 'Review lists exceed 20,000 rows. Confirm them in batches using the '
                                    'latest list.',
 '待确认清单超过 8 MB，未读取：{0}': 'Review list exceeds 8 MB and was not read: {0}',
 '待确认清单：{0}；原图预览：{1}。{2}': 'Review list: {0}; source-image preview: {1}. {2}',
 '待移入回收站的批次目录不存在。': 'The batch folder to move to Trash does not exist.',
 '必须指定 --installer 或 --zip 参数。': 'An --installer or --zip argument is required.',
 '恢复临时索引名无效': 'Invalid temporary recovery index name',
 '恢复备份不属于历史资料库': 'Recovery backup does not belong to the history library',
 '恢复备份路径无效': 'Invalid recovery backup path',
 '恢复批次时发现两个资料目录。': 'Two material folders found while recovering the batch.',
 '恢复标记任务编号不一致': 'Recovery marker task ID mismatch',
 '恢复标记版本无效': 'Invalid recovery marker version',
 '恢复路径无效': 'Invalid recovery path',
 '所有更新源均不可用，已按顺序尝试：': 'All update sources are unavailable. Tried in order:',
 '所选工作表已不存在，请重新选择': 'The selected worksheet no longer exists. Select it again.',
 '所选文件夹内没有可导入的资料。': 'The selected folder has no importable files.',
 '所选文件夹包含资料库，不能作为原始资料归档。': 'The selected folder contains the library and cannot be archived as source data.',
 '所选文件夹包含链接，未导入：{0}': 'The selected folder contains a link and was not imported: {0}',
 '所选日期范围内没有周一，本期未统计周报。': 'The selected date range contains no Monday. Weekly reports were not counted.',
 '所选表头超出工作表范围': 'Selected header rows are outside the worksheet',
 '所选资料在列头确认后发生变化，请重新点击开始合并并确认列头': 'Selected files changed after header confirmation. Start the merge again '
                                  'and confirm headers.',
 '所选项目资料中没有可复用的文件。': 'No reusable files in the selected project materials.',
 '打包后台进程没有返回预期结果。': 'The packaging worker did not return the expected result.',
 '打包程序缺少 README.md。': 'The packaged app is missing README.md.',
 '扫描人员目录': 'Scan Employee Folders',
 '扫描压缩文件': 'Scan Archives',
 '扫描型 PDF 未找到可安全提取的页面图片：{0}；如该文件由特殊渲染器生成，请先另存为标准 PDF 或逐页图片后重试': 'No safely extractable images in scanned '
                                                                'PDF: {0}. Save it as a standard PDF or '
                                                                'individual page images and retry.',
 '扫描待提取资料': 'Scan Materials to Retrieve',
 '扫描待识别资料': 'Scan Materials to Recognize',
 '扫描资料': 'Scan Files',
 '批次不存在。': 'Batch not found.',
 '批次业务分组目录无效。': 'Invalid batch business-group folder.',
 '批次工具目录无效。': 'Invalid batch tool folder.',
 '批次改名恢复发现两个目录，已停止写入。': 'Two folders found during batch rename recovery. Writing stopped.',
 '批次改名恢复找不到原资料目录。': 'Original material folder not found during batch rename recovery.',
 '批次文件分类无效。': 'Invalid batch file category.',
 '批次文件夹分类无效。': 'Invalid batch folder category.',
 '批次文件夹已移动或不安全：{0}': 'Batch folder moved or unsafe: {0}',
 '批次文件夹清单包含重复编号。': 'Batch folder manifest contains duplicate IDs.',
 '批次文件夹清单包含重复路径。': 'Batch folder manifest contains duplicate paths.',
 '批次文件夹清单无效。': 'Invalid batch folder manifest.',
 '批次文件夹路径与待恢复改名不一致。': 'Batch folder path does not match the pending rename recovery.',
 ' 候选表头：{0}': ' Candidate headers: {0}',
 '.xls 转换失败，未生成文件：{0}': 'Legacy Excel conversion failed; no file generated: {0}',
 '7-Zip 处理失败（退出码 {0}）': '7-Zip failed (exit code {0})',
 '7-Zip 文件列表包含无效压缩大小：{0}': 'Invalid compressed size in 7-Zip file list: {0}',
 '7-Zip 文件列表包含无效成员名称': 'Invalid member name in 7-Zip file list',
 '7-Zip 文件列表包含无法解析的成员': 'Unparseable member in 7-Zip file list',
 '7-Zip 文件列表包含重复字段：{0}': 'Duplicate field in 7-Zip file list: {0}',
 '7-Zip 文件列表缺少有效大小：{0}': 'Missing valid size in 7-Zip file list: {0}',
 '7-Zip 无法启动或执行超时：{0}': '7-Zip could not start or timed out: {0}',
 '7-Zip 未解压预期成员：{0}': '7-Zip did not extract the expected member: {0}',
 '7-Zip 未返回可验证的文件列表': '7-Zip did not return a verifiable file list',
 '7-Zip 解压了未通过安全校验的成员：{0}': '7-Zip extracted a member that failed safety checks: {0}',
 '7-Zip 解压结果包含特殊文件：{0}': 'Special file in 7-Zip output: {0}',
 '7-Zip 解压结果包含链接：{0}': 'Link in 7-Zip output: {0}',
 '7Z 文件列表不完整': 'Incomplete 7Z file list',
 '7Z 文件列表顺序不一致': 'Inconsistent 7Z file list order',
 '7Z 未解压预期成员：{0}': '7Z did not extract the expected member: {0}',
 '7Z 解压组件未安装完整': '7Z extraction components are not fully installed',
 '7Z 解压组件版本过旧，且未找到兼容运行时': '7Z extraction components are outdated and no compatible runtime was found',
 '7Z 解压组件运行检查失败：warnings={0}，files={1}': '7Z runtime check failed: warnings={0}, files={1}',
 '7Z 返回未通过安全校验的成员：{0}': '7Z returned a member that failed safety checks: {0}',
 'Excel 中没有可用姓名': 'No usable employee names in Excel',
 'Excel 共 {0} 个姓名，所选类型共 {1} 项；未配对项目已排除，可手动编辑后勾选。': 'Excel has {0} names; the selected type has {1} items. '
                                                   'Unassigned items are excluded; edit and select them to '
                                                   'include them.',
 'Excel 前 20 行未找到唯一的“{0}”和“{1}”列': 'Unique “{0}” and “{1}” columns were not found in the first 20 rows',
 'Excel 原文件名未匹配所选类型：{0}': 'Excel original name did not match the selected type: {0}',
 'Excel 原文件名重复：{0}': 'Duplicate original name in Excel: {0}',
 'Excel 文件仅支持 .xlsx 或 .xls：{0}': 'Excel files must be .xlsx or .xls: {0}',
 'Excel 文件缺少必要样式结构：{0}': 'Required Excel style structure is missing: {0}',
 'Excel 映射列必须各有一个且不能相同': 'Each mapping column must appear exactly once, and the two columns must differ',
 'Excel 第 {0} 行缺少原文件名': 'Missing original filename in Excel row {0}',
 'Excel 绘图缺少 a 命名空间：{0}': 'Excel drawing is missing the a namespace: {0}',
 'Excel 输出兼容性校验失败：{0}': 'Excel output compatibility check failed: {0}',
 'Excel 输出缺少必要样式结构。': 'Required styles are missing from the Excel output.',
 'Excel文件不存在：{0}': 'Excel file not found: {0}',
 'Excel文件中未找到“{0}”列或该列无数据。': 'Excel column “{0}” is missing or empty.',
 'Gitee 发行版与更新配置的版本不一致。': 'The Gitee release version differs from the update configuration.',
 'Gitee 尚未上传此平台安装包，请稍后重试。': 'The Gitee installer for this platform is not available yet. Try again later.',
 'Gitee 更新配置不能指向 GitHub。': 'Gitee update configuration cannot point to GitHub.',
 'HTTPS 证书校验未正确启用。': 'HTTPS certificate verification is not correctly enabled.',
 'OCR 引擎未能启动，请检查依赖后重启软件。': 'The OCR engine could not start. Check dependencies and restart the app.',
 'OCR 引擎版本变更（{0} → {1}），缓存已全量失效，本次将重新 OCR 识别所有图片。': 'OCR engine changed ({0} → {1}). The cache is '
                                                    'invalidated; all images will be recognized again.',
 'OCR 智能索引缓存：命中 {0} 次，实时识别 {1} 次': 'OCR cache: {0} hits, {1} newly recognized',
 'OCR 索引缓存写入失败：{0}；本次仍使用内存索引完成检索，下次会重新建立。': 'Could not save OCR index: {0}. This run uses the in-memory '
                                            'index; it will be rebuilt next time.',
 'OCR 索引超过 64 MB 安全读取上限，已停止处理并保留原缓存；请按资料批次分库': 'The OCR index exceeds the 64 MB read limit. Processing '
                                               'stopped and the cache was retained. Split the library into '
                                               'batches.',
 'OCR 缓存写入失败：{0}（资料库目录可能为只读），本次未持久化识别结果。': 'Could not save OCR cache: {0}. The library may be read-only; '
                                           'recognition results were not persisted.',
 'OCR资源 文件={0} 识别单元={1} 图片={2}x{3} 模式={4} 可用MB={5} 预算MB={6} 状态={7}': 'OCR resources: file={0}, unit={1}, '
                                                                     'image={2}x{3}, mode={4}, available '
                                                                     'MB={5}, budget MB={6}, status={7}',
 'Office XML 包含不支持的实体声明': 'Office XML contains unsupported entity declarations',
 'Office XML 条目体积异常': 'Office XML entry size is outside the allowed range',
 'Office XML 条目压缩比异常': 'Office XML entry compression ratio is outside the allowed range',
 'Office XML 条目实际体积异常': 'Actual Office XML entry size is outside the allowed range',
 'Office 文档包含过多压缩条目': 'Office document contains too many archive entries',
 'PDF 单页图像对象数量超过安全上限': 'PDF page contains too many image objects',
 'PDF 图片解码组件不可用，请重新安装完整版本后重试': 'PDF image decoder unavailable. Reinstall the complete app and try again.',
 'PDF 扫描页解码数量异常：{0} != 1': 'Unexpected number of decoded PDF page images: {0} != 1',
 'PDF 扫描页解码结果为空': 'Decoded PDF page image is empty',
 'PDF 文件为空或已损坏：{0}': 'PDF is empty or damaged: {0}',
 'PDF 文件体积超过安全上限：{0}，允许不超过 {1} MB': 'PDF exceeds the size limit: {0}; maximum {1} MB',
 'PDF 文件已加密，无法自动识别：{0}；请先在可信的 PDF 工具中解除密码后重试': 'PDF is encrypted and cannot be recognized: {0}. Remove the '
                                               'password using a trusted PDF tool first.',
 'PDF 文件损坏或格式异常：{0}': 'PDF is damaged or malformed: {0}',
 'PDF 文件损坏，无法读取页面结构：{0}': 'Cannot read the damaged PDF page structure: {0}',
 'PDF 文件无法读取：{0}': 'Cannot read PDF: {0}',
 'PDF 文件没有可读取页面：{0}': 'PDF has no readable pages: {0}',
 'PDF 文字量超过安全上限：{0}，允许不超过 {1} 个字符': 'PDF text exceeds the limit: {0}; maximum {1} characters',
 'PDF 第 {0} 页估算解码内存超过安全上限：{1} > {2} bytes': 'PDF page {0} estimated decoding memory exceeds the limit: {1} > '
                                            '{2} bytes',
 'PDF 第 {0} 页图像为空：{1}': 'PDF page {0} image is empty: {1}',
 'PDF 第 {0} 页图像估算解码内存超过安全上限：{1} > {2} bytes': 'PDF page {0} image decoding memory exceeds the limit: {1} > '
                                              '{2} bytes',
 'PDF 第 {0} 页图像像素超过安全上限：{1} > {2}': 'PDF page {0} image pixel count exceeds the limit: {1} > {2}',
 'PDF 第 {0} 页图像损坏或格式不受支持：{1}': 'PDF page {0} image is damaged or unsupported: {1}',
 'PDF 第 {0} 页图像数量超过安全上限：{1} > {2}': 'PDF page {0} image count exceeds the limit: {1} > {2}',
 'PDF 第 {0} 页尺寸无效：{1}': 'PDF page {0} has invalid dimensions: {1}',
 'PDF 第 {0} 页损坏或无法安全渲染：{1}': 'PDF page {0} is damaged or cannot be rendered safely: {1}',
 'PDF 第 {0} 页文字层损坏：{1}': 'PDF page {0} text layer is damaged: {1}',
 'PDF 第 {0} 页渲染像素超过安全上限：{1} > {2}': 'PDF page {0} render pixel count exceeds the limit: {1} > {2}',
 'PDF 第 {0} 页渲染图像体积超过安全上限：{1} > {2} bytes': 'PDF page {0} rendered image exceeds the size limit: {1} > {2} '
                                            'bytes',
 'PDF 第 {0} 页渲染结果为空：{1}': 'PDF page {0} rendered image is empty: {1}',
 'PDF 第 {0} 页解码后图像体积超过安全上限：{1} > {2} bytes': 'PDF page {0} decoded image exceeds the size limit: {1} > {2} '
                                             'bytes',
 'PDF 累计估算解码内存超过安全上限：{0}': 'Total estimated PDF decoding memory exceeds the limit: {0}',
 'PDF 累计图像像素超过安全上限：{0}': 'Total PDF image pixel count exceeds the limit: {0}',
 'PDF 累计页面像素超过安全上限：{0}': 'Total PDF page pixel count exceeds the limit: {0}',
 'PDF 识别组件未能提取完整文字层': 'The PDF component could not extract the complete text layer',
 'PDF 识别组件运行检查失败：{0}': 'PDF runtime check failed: {0}',
 'PDF 识别能力已升级，已安全失效 {0} 条旧 PDF 缓存；图片和其他文档缓存保持不变。': 'PDF recognition was upgraded. Invalidated {0} old PDF '
                                                   'cache entries; other cached documents are unchanged.',
 'PDF 页数超过安全上限：{0}，共 {1} 页，允许不超过 {2} 页': 'PDF exceeds the page limit: {0}; {1} pages, maximum {2}',
 'PDF 页面图像对象损坏': 'Damaged image object on PDF page',
 'PDF 页面图像尺寸无效': 'Invalid image dimensions on PDF page',
 'PDF 页面图像缺少有效尺寸': 'Missing valid image dimensions on PDF page',
 'PDF 页面对象嵌套层级超过安全上限': 'PDF page object nesting exceeds the limit',
 'PDF 页面资源结构损坏': 'Damaged PDF page resource structure',
 'RAR 未解压预期成员：{0}': 'RAR did not extract the expected member: {0}',
 'RAR 解压组件未安装完整': 'RAR extraction components are not fully installed',
 'RAR 解压组件运行检查失败：warnings={0}，files={1}': 'RAR runtime check failed: warnings={0}, files={1}',
 'WAL 日志无法完整校验': 'The write-ahead log could not be fully verified',
 'WAL 日志无法校验': 'The write-ahead log could not be verified',
 'WAL 日志校验失败': 'Write-ahead log verification failed',
 'WAL 校验数据长度无效': 'Invalid write-ahead log checksum length',
 'Win7 更新运行库缺失或不是普通文件：{0}': 'Win7 update runtime is missing or not a regular file: {0}',
 '{0} {1} 第 {2} 行缺少可识别日期，已跳过。': '{0} {1}, row {2}: no recognizable date; skipped.',
 '{0} {1}来源明确为补差，但模板没有对应补差明细列；金额已保留在普通缴费区，请人工确认。': '{0} {1}: the source explicitly indicates an adjustment, '
                                                   'but the template has no matching detail column. The '
                                                   'amount is retained under regular payments; review it '
                                                   'manually.',
 '{0} {1}补差含多种基数或比例，基数/比例留空，金额按源表汇总。': '{0} {1}: multiple adjustment bases or rates. Base and rate are '
                                       'blank; amounts are totaled from the source.',
 '{0} {1}补差未识别有效期间，补差表头不显示日期。': '{0} {1}: no valid adjustment period; no date is shown in the adjustment '
                                'header.',
 '{0} {1}，金额已保留在普通缴费区，未自动归入补差。': '{0} {1}. The amount is retained under regular payments and was not '
                                 'automatically classified as an adjustment.',
 '{0} → {1} 改名失败，已停止：{2}。已完成 {3} 项：{4}；未处理 {5} 项：{6}。请检查结果并重新预览。': 'Rename stopped: {0} → {1}: {2}. '
                                                                   'Completed {3}: {4}; not processed {5}: '
                                                                   '{6}. Check the results and preview '
                                                                   'again.',
 '{0} → {1}：{2}；本批次未执行': '{0} → {1}: {2}; this batch was not executed',
 '{0} → {1}：目标已存在；本批次未执行，未覆盖任何项目': '{0} → {1}: target exists; batch not executed and nothing overwritten',
 '{0} 不是受支持的压缩包，已跳过': '{0} is not a supported archive; skipped',
 '{0} 不是可识别的社保缴费清单，已跳过：{1}': '{0} is not a recognized social insurance payment list; skipped: {1}',
 '{0} 不是有效月度工资表，已跳过：{1}': '{0} is not a valid monthly payroll workbook; skipped: {1}',
 '{0} 不是档案移交表，已跳过。': '{0} is not an archive transfer sheet; skipped.',
 '{0} 中存在不安全路径，已跳过：{1}': 'Unsafe path in {0}; skipped: {1}',
 '{0} 中存在特殊文件，已跳过：{1}': 'Special file in {0}; skipped: {1}',
 '{0} 中存在链接文件，已跳过：{1}': 'Link in {0}; skipped: {1}',
 '{0} 人员 {1} 的{2}与花名册不一致：账单/文件夹识别为“{3}”，花名册为“{4}”。已按账单/文件夹识别结果写入。': '{0}: employee {1}, {2} differs from the '
                                                                    'roster. Bill/folder value: “{3}”; '
                                                                    'roster: “{4}”. The bill/folder value '
                                                                    'was used.',
 '{0} 删除后名称为空，已跳过': '{0} would have an empty name after removal; skipped',
 '{0} 匹配到多个已有档案表，已使用第一个：{1}': '{0} matched multiple existing archives; using the first: {1}',
 '{0} 在检查期间变化，请重新预览': '{0} changed during validation. Generate a new preview.',
 '{0} 在预览后已变化，请重新预览': '{0} changed after preview. Generate a new preview.',
 '{0} 对应姓名“{1}”不能用于改名，已跳过：{2}': '{0}: assigned name “{1}” is invalid; skipped: {2}',
 '{0} 工作表「{1}」未找到已知表头，已跳过。': '{0}, worksheet “{1}”: no recognized headers; skipped.',
 '{0} 工作表「{1}」的导出范围 {2} 不完整，已自动扫描并恢复为 {3}。': '{0}, worksheet “{1}”: incomplete export range {2} was scanned '
                                             'and recovered as {3}.',
 '{0} 工作表「{1}」表头不在已知考勤/周月报模板内，已跳过。 识别到的表头（{2}）：{3}{4}': '{0}, worksheet “{1}”: headers do not match '
                                                        'attendance or report templates; skipped. Detected '
                                                        'headers ({2}): {3}{4}',
 '{0} 已不存在，已跳过': '{0} no longer exists; skipped',
 '{0} 已不是普通文件或文件夹，请重新预览': '{0} is no longer a regular file or folder. Generate a new preview.',
 '{0} 已包含后缀，已跳过': '{0} already has the suffix; skipped',
 '{0} 已存在，{1} 已跳过': '{0} exists; skipped {1}',
 '{0} 执行前已存在，{1} 已跳过，未覆盖原项目': '{0} existed before execution; skipped {1} without overwriting',
 '{0} 改名前后相同，已跳过': '{0} has no name change; skipped',
 '{0} 改名失败：{1}': 'Could not rename {0}: {1}',
 '{0} 无效。': 'Invalid {0}.',
 '{0} 无法使用本机表格组件完整保留格式，已自动切换兼容模式继续生成；数据会正常输出，但原表颜色、边框、换行和公式格式可能简化。': '{0}: the spreadsheet component could '
                                                                     'not fully preserve formatting. '
                                                                     'Compatibility mode is being used; data '
                                                                     'is retained, but colors, borders, '
                                                                     'wrapping, or formula formatting may be '
                                                                     'simplified.',
 '{0} 是链接或重解析点，不能进行文字替换': '{0} is a link or reparse point and cannot be processed',
 '{0} 未在前 20 行找到“{1}”表头': '{0}: header “{1}” was not found in the first 20 rows',
 '{0} 未完成合并，本次未生成汇总结果：{1}': '{0}: merge incomplete; no summary generated: {1}',
 '{0} 未找到表头：{1}': '{0}: headers not found: {1}',
 '{0} 未能判断是周报还是月报，已跳过。': '{0}: could not identify weekly or monthly report type; skipped.',
 '{0} 未识别到保单人员，已跳过。': '{0}: no policyholders recognized; skipped.',
 '{0} 未识别到公司档案表表头，已跳过。': '{0}: company archive headers not recognized; skipped.',
 '{0} 未识别到应汇报人员名单，请确认表头包含“姓名”或“汇报人”。': '{0}: expected reporters roster not recognized. Check that it '
                                       'contains a name or reporter column.',
 '{0} 未识别到档案表表头，已跳过。': '{0}: archive headers not recognized; skipped.',
 '{0} 的 {1} 未识别到档案表表头，已跳过。': '{0}, {1}: archive headers not recognized; skipped.',
 '{0} 的 {1} 格式底稿精简失败，已使用原工作簿保留格式：{2}': '{0}, {1}: could not simplify the formatting template; using the '
                                       'original workbook: {2}',
 '{0} 的 {1} 第 {2} 行缺少姓名或身份证，已跳过。': '{0}, {1}, row {2}: name or ID missing; skipped.',
 '{0} 的保单 {1} 未找到“每人伤残死亡限额”，该行保额无法计算。': '{0}, policy {1}: per-person disability/death limit missing; '
                                        'coverage cannot be calculated.',
 '{0} 的压缩比例异常': '{0} has an abnormal compression ratio',
 '{0} 的已有档案表未识别到表头。': '{0}: headers in the existing archive were not recognized.',
 '{0} 的旧版 Excel 格式兼容增强未完成，结果文件已正常生成。': '{0}: legacy Excel format enhancement was incomplete, but results '
                                       'were generated successfully.',
 '{0} 的部分高级格式无法恢复，已使用兼容格式继续生成。': '{0}: some advanced formatting could not be restored; using compatible '
                                 'formatting.',
 '{0} 的高级格式兼容信息无法读取，已继续生成结果；部分格式可能简化。': '{0}: advanced formatting metadata could not be read. Results were '
                                        'generated; some formatting may be simplified.',
 '{0} 目标名称重复，{1} 已跳过': '{0}: duplicate target name; skipped {1}',
 '{0} 第 {1} 行 {2} {3}（身份证 {4}）的{5}数量冲突：原值“{6}”，新值“{7}”，已保留原值。': '{0}, row {1}, {2} {3} (ID {4}): conflicting '
                                                                '{5} counts. Kept “{6}” instead of “{7}”.',
 '{0} 第 {1} 行人员 {2} 未在参保人员花名册中找到，已跳过。': '{0}, row {1}: employee {2} not found in the insured roster; '
                                        'skipped.',
 '{0} 第 {1} 行增员缺少身份证号码，未写入花名册。': '{0}, row {1}: new employee ID missing; not added to the roster.',
 '{0} 第 {1} 行月份 {2} 不在输出月份中，已跳过': '{0}, row {1}: month {2} is outside the output months; skipped',
 '{0} 第 {1} 行未识别保额，已跳过。': '{0}, row {1}: coverage amount not recognized; skipped.',
 '{0} 第 {1} 行未识别到应发工资，按 0 处理': '{0}, row {1}: gross pay not recognized; using 0',
 '{0} 第 {1} 行未识别账单期，已写入“未识别账单期”。': '{0}, row {1}: billing period not recognized; recorded as unknown.',
 '{0} 第 {1} 行未识别项目地区，编号已留空。': '{0}, row {1}: project region not recognized; code left blank.',
 '{0} 第 {1} 行缺少公司、姓名或身份证，已跳过。': '{0}, row {1}: company, name, or ID missing; skipped.',
 '{0} 第 {1} 行缺少身份证号码，已跳过': '{0}, row {1}: ID number missing; skipped',
 '{0} 第 {1} 行身份证 {2} 姓名与花名册不同：{3} / {4}。': '{0}, row {1}, ID {2}: name differs from roster: {3} / {4}.',
 '{0} 缺少字段：{1}': '{0}: missing fields: {1}',
 '{0} 缺少工作表：{1}': '{0}: missing worksheet: {1}',
 '{0} 解压后超过单文件安全上限': '{0} exceeds the single-file extraction limit',
 '{0} 解压失败，已跳过：{1}': 'Could not extract {0}; skipped: {1}',
 '{0} 身份证 {1} 在本次导入中重复，已跳过后续记录。': '{0}: ID {1} is duplicated in this import; subsequent records skipped.',
 '{0} 身份证 {1} 在汇总表中重复，已合并为一条。': '{0}: duplicate summary records for ID {1} merged into one.',
 '{0} 身份证 {1} 已存在，但姓名不同：{2}': '{0}: ID {1} already exists with a different name: {2}',
 '{0}!{1} 应发工资公式没有可用缓存且无法安全计算，请用 Excel/WPS 重新计算并保存后再合并': '{0}!{1}: gross-pay formula has no usable cached '
                                                         'value and cannot be calculated safely. Recalculate '
                                                         'and save in Excel/WPS before merging.',
 '{0}!{1}{2} 未读到有效金额，请核对所选应发工资列及公式计算结果': '{0}!{1}{2}: no valid amount found. Check the gross-pay column and '
                                         'formula results.',
 '{0}、{1} → {2}：目标名称重复；本批次未执行': '{0}, {1} → {2}: duplicate target name; batch not executed',
 '{0}不存在。': '{0} does not exist.',
 '{0}不存在或无法读取。': '{0} does not exist or cannot be read.',
 '{0}不是安全的文件夹名称，请换一个名称。': '{0} is not a safe folder name. Choose another name.',
 '{0}不是安全的普通文件。': '{0} is not a safe regular file.',
 '{0}不是安全的普通文件夹。': '{0} is not a safe regular folder.',
 '{0}不是普通文件。': '{0} is not a regular file.',
 '{0}不是普通目录。': '{0} is not a regular folder.',
 '{0}不能为空。': '{0} cannot be empty.',
 '{0}不能包含逗号或 Windows 文件名不支持的字符。': '{0} cannot contain commas or characters prohibited in Windows filenames.',
 '{0}不能是链接或系统重定向目录。': '{0} cannot be a link or redirected system folder.',
 '{0}不能添加空名称': '{0} cannot contain empty names',
 '{0}不能超过 {1} 个字符。': '{0} cannot exceed {1} characters.',
 '{0}包含不支持的控制字符。': '{0} contains unsupported control characters.',
 '{0}名称属于项目保留名称，请换一个名称。': '{0} is a reserved project name. Choose another name.',
 '{0}明细表缺少必要字段：{1}': '{0}: required detail fields missing: {1}',
 '{0}最多设置 100 个名称': '{0} supports up to 100 names',
 '{0}的名称须为不超过 200 字的文字': '{0}: names must be text with no more than 200 characters',
 '{0}缺少必要字段：{1}': '{0}: required fields missing: {1}',
 '{0}：“{1}”不能同时对应{2}和{3}': '{0}: “{1}” cannot map to both {2} and {3}',
 '{0}：“{1}”是其他字段的内置名称，不能改作{2}': '{0}: “{1}” is a built-in alias for another field and cannot be assigned to '
                                '{2}',
 '{0}：带薪休假总计为{1}天，已识别的假别合计为{2}天，本次按假别合计填写，请核对原表。': '{0}: total paid leave is {1} days, but identified leave '
                                                   'categories total {2} days. The category total was used; '
                                                   'check the source.',
 '“{0}”不能同时对应{1}和{2}': '“{0}” cannot map to both {1} and {2}',
 '⚠️ 证件号码【{0}】与目标【{1}】不一致': '⚠ ID number {0} does not match target {1}',
 '⚠️ 证件姓名【{0}】与目标【{1}】不一致': '⚠ Document name {0} does not match target {1}',
 '【登记结果】已完成 0/2 项；正在登记结果文件': 'Saving results: 0/2 complete; registering output files',
 '【登记结果】已完成 1/2 项；正在保存批次状态': 'Saving results: 1/2 complete; saving batch status',
 '【登记结果】已完成 2/2 项；结果文件和批次状态均已保存': 'Saving results: 2/2 complete; files and batch status saved',
 '上传文件夹结构与本次清单不一致，已停止建立处理副本。': 'The uploaded folder structure differs from the manifest. Stopped creating '
                               'the working copy.',
 '上传资料与本次清单不一致，已停止建立处理副本。': 'Uploaded files differ from the manifest. Stopped creating the working copy.',
 '上传资料包含链接，已停止处理：{0}': 'Uploaded data contains a link; processing stopped: {0}',
 '上传资料已发生变化，不能继续处理：{0}': 'Uploaded data changed; processing cannot continue: {0}',
 '上次移入回收站的操作无法安全续做：{0}': 'The previous move to Trash cannot be safely resumed: {0}',
 '上次移入回收站的文件无法在索引恢复前核对：{0}': 'The previous move to Trash cannot be verified before index recovery: {0}',
 '不同字段不能选择同一列': 'Different fields cannot use the same column',
 '不同资料不能选择同一工作表': 'Different data types cannot use the same worksheet',
 '不支持的历史状态：{0}': 'Unsupported history status: {0}',
 '不支持的归类模式：{0}，可选值：{1}': 'Unsupported organization mode: {0}; valid values: {1}',
 '不支持的批次状态：{0}': 'Unsupported batch status: {0}',
 '不支持的改名模式：{0}': 'Unsupported rename mode: {0}',
 '不支持的改名预览版本，请重新预览': 'Unsupported preview version. Generate a new preview.',
 '不支持的文件类型：{0}': 'Unsupported file type: {0}',
 '不支持的更新地址协议：{0}。': 'Unsupported update URL scheme: {0}.',
 '不支持的资料库形式：{0}，可选值：{1}': 'Unsupported library layout: {0}; valid values: {1}',
 '不能写入项目隐藏管理目录。': 'Cannot write to the hidden project management folder.',
 '不能在另一个 HRToolkit 项目中创建子项目。': 'Cannot create a project inside another HR Toolkit project.',
 '不能把当前目标批次自身作为输入资料。': 'The target batch cannot be used as its own input.',
 '不能把资料库自身作为原始资料归档。': 'The library cannot be archived as its own source.',
 '不能把资料库自身作为结果来源。': 'The library cannot be used as its own results source.',
 '不能把项目自身或包含项目的文件夹再次导入。': 'Cannot import the project itself or a folder containing it.',
 '不能直接向项目根目录导入文件。': 'Cannot import files directly into the project root.',
 '个文件': 'files',
 '临时历史索引未完整生成。': 'The temporary history index is incomplete.',
 '临时磁盘空间不足，无法安全解压压缩包': 'Insufficient temporary disk space to extract the archive safely',
 '为保护电脑安全，不能导入此类文件：{0}': 'This file type cannot be imported for security reasons: {0}',
 '主程序文件名不合法。': 'Invalid application executable name.',
 '人力资源分析表不存在：{0}': 'HR analysis workbook not found: {0}',
 '人力资源分析表仅支持 .xlsx 或 .xls 文件。': 'The HR analysis workbook must be .xlsx or .xls.',
 '人力资源分析表的“花名册”未识别到姓名和身份证号码，请确认表头。': 'The employee roster in the HR analysis workbook has no recognized name '
                                     'or ID columns. Check its headers.',
 '人力资源分析表目前只支持 .xlsx 或 .xls 文件。': 'The HR analysis workbook must be .xlsx or .xls.',
 '人力资源分析表缺少“花名册”工作表。': 'The HR analysis workbook is missing the employee roster worksheet.',
 '人力资源花名册不存在：{0}': 'Employee roster not found: {0}',
 '批次文件已发生变化：{0}': 'Batch file changed: {0}',
 '批次文件已移动或不安全：{0}': 'Batch file moved or unsafe: {0}',
 '批次文件清单无效。': 'Invalid batch file manifest.',
 '批次文件路径与待恢复改名不一致。': 'Batch file path does not match the pending rename recovery.',
 '批次清单与编号不一致。': 'Batch manifest does not match its ID.',
 '批次清单版本无效。': 'Invalid batch manifest version.',
 '批次清单目录包含不安全项目。': 'Batch manifest folder contains unsafe items.',
 '批次清单缺少任务信息。': 'Batch manifest is missing task metadata.',
 '批次状态无效。': 'Invalid batch status.',
 '批次目录不属于正确分类。': 'Batch folder is not in the correct category.',
 '批次目录与业务信息不一致。': 'Batch folder does not match business metadata.',
 '批次目录信息无效。': 'Invalid batch folder metadata.',
 '批次目录名称无效。': 'Invalid batch folder name.',
 '批次编号无效。': 'Invalid batch ID.',
 '批次资料目录包含链接，已停止导入。': 'Batch materials contain a link; import stopped.',
 '拆分明细已生成，正在生成社保汇总表...': 'Split details generated. Creating social insurance summary…',
 '损坏索引备份原因无效。': 'Invalid reason recorded for damaged-index backup.',
 '损坏索引备份文件不存在或不安全。': 'Damaged-index backup file missing or unsafe.',
 '损坏索引备份文件名无效。': 'Invalid damaged-index backup filename.',
 '损坏索引备份校验失败。': 'Damaged-index backup verification failed.',
 '损坏索引备份清单不存在或不安全。': 'Damaged-index backup manifest missing or unsafe.',
 '损坏索引备份清单为空。': 'Damaged-index backup manifest is empty.',
 '损坏索引备份清单内容无效。': 'Invalid damaged-index backup manifest contents.',
 '损坏索引备份清单版本无效。': 'Invalid damaged-index backup manifest version.',
 '损坏索引备份目录不存在或不安全。': 'Damaged-index backup folder missing or unsafe.',
 '提取全部资料': 'Retrieve All Materials',
 '提取资料': 'Retrieve Materials',
 '改名已完成，但 CSV 清单保存失败。请查看完整改名记录：{0}。原因：{1}': 'Renaming finished, but the CSV receipt could not be saved. See '
                                            'the full rename log: {0}. Reason: {1}',
 '改名未全部完成，已尝试安全恢复原名；{0} 项尚未恢复。请保留结果目录（含临时项目）并查看改名记录：{1}。原因：{2}': 'Renaming was incomplete and a safe '
                                                                 'rollback was attempted. {0} items remain '
                                                                 'unrestored. Keep the results folder, '
                                                                 'including temporary items, and check the '
                                                                 'log: {1}. Reason: {2}',
 '改名项目编号无效，请重新预览': 'Invalid rename item ID. Generate a new preview.',
 '文件内容不是有效的 ZIP、RAR、7Z 或 TAR 压缩包': 'File contents are not a valid ZIP, RAR, 7Z, or TAR archive',
 '文件名中未识别险种。': 'Insurance type not recognized in filename.',
 '文件在索引过程中发生变化，已跳过：{0}': 'File changed during indexing; skipped: {0}',
 '文件夹不存在：{0}': 'Folder not found: {0}',
 '文件夹名称不合法：{0}': 'Invalid folder name: {0}',
 '文件夹名称不能为空': 'Folder name cannot be empty',
 '文件夹名称不能以空格或句点结尾：{0}': 'Folder name cannot end in a space or period: {0}',
 '文件夹名称包含 Windows 不支持的字符：{0}': 'Folder name contains characters unsupported by Windows: {0}',
 '文件夹名称包含 Windows 不支持的控制字符：{0}': 'Folder name contains control characters unsupported by Windows: {0}',
 '文件夹名称是 Windows 保留名称：{0}': 'Folder name is reserved by Windows: {0}',
 '文件夹已存在：{0}': 'Folder already exists: {0}',
 '文件夹快照不完整：{0}': 'Incomplete folder snapshot: {0}',
 '文件夹结构在保存期间发生变化，请重新预览后再执行。': 'Folder structure changed while saving. Preview again before running.',
 '文件夹资料层级不完整，已停止导入。': 'Incomplete folder hierarchy; import stopped.',
 '文件夹资料快照不完整。': 'Incomplete folder snapshot.',
 '文件或文件夹名称不能使用项目隐藏管理目录名称。': 'File and folder names cannot use the hidden project management folder name.',
 '文件读取异常 {0}: {1}': 'File read error {0}: {1}',
 '文件锁正在被当前进程占用：{0}': 'The current process already holds this file lock: {0}',
 '新处理批次不再保存源文件副本，请直接选择原文件。': 'New batches do not retain source copies. Select the original files directly.',
 '新建项目必须使用空目录：{0}': 'A new project requires an empty folder: {0}',
 '新项目必须使用空文件夹，避免覆盖已有资料。': 'Use an empty folder for a new project to avoid overwriting existing files.',
 '无序平铺资料库必须启用 OCR 索引缓存，避免每次查询重复识别全部文件': 'Flat libraries require OCR index caching to avoid recognizing every '
                                        'file on each query',
 '无序资料 OCR 索引：复用 {0} 个，新增识别 {1} 个': 'Flat-library OCR index: {0} reused, {1} newly recognized',
 '无法保存项目清单 {0}：{1}': 'Could not save project manifest {0}: {1}',
 '无法加载 HTTPS 根证书：{0}': 'Could not load HTTPS root certificates: {0}',
 '无法启动独立后台进程：{0}': 'Could not start background worker: {0}',
 '无法安全发布文件：{0}': 'Could not safely finalize file: {0}',
 '无法安全备份损坏的历史索引：{0}': 'Could not safely back up the damaged history index: {0}',
 '无法安全隔离未完成结果，请关闭文件后重试：{0}': 'Could not safely quarantine unfinished results. Close the files and retry: {0}',
 '无法完整写入解压文件：{0}': 'Could not fully write extracted file: {0}',
 '无法核对{0}：{1}': 'Could not verify {0}: {1}',
 '无法核对历史资料目录：{0}': 'Could not verify historical materials folder: {0}',
 '无法检查资料库剩余空间：{0}': 'Could not check library free space: {0}',
 '无法检查项目剩余空间：{0}': 'Could not check project free space: {0}',
 '无法清理历史索引检查临时目录：{0}': 'Could not remove temporary history-index check folder: {0}',
 '无法记录历史索引缺失状态：{0}': 'Could not record missing history-index status: {0}',
 '无法访问文件夹 {0}: {1}': 'Cannot access folder {0}: {1}',
 '无法识别工资表月份：{0}。请在文件名中包含 202604 或 2026年4月': 'Could not identify payroll month: {0}. Include a month such as '
                                            '202604 in the filename.',
 '无法读取 Excel 样式结构：{0}': 'Could not read Excel styles: {0}',
 '无法读取历史资料目录 {0}：{1}': 'Could not read historical materials folder {0}: {1}',
 '无法读取压缩包成员：{0}': 'Could not read archive member: {0}',
 '无法读取原始资料：{0}': 'Could not read source materials: {0}',
 '无法读取当前程序的实际安装位置，请关闭后从安装目录重新启动。': 'Could not locate the installed application. Close it and launch it from '
                                   'the installation folder.',
 '无法读取当前账户的用户文件夹，请检查账户目录和磁盘连接。': 'Could not read the user folder. Check the account folder and disk '
                                 'connection.',
 '无法读取更新配置：{0}': 'Could not read update configuration: {0}',
 '无法读取资料库位置：{0}': 'Could not read library location: {0}',
 '无法读取资料文件，已跳过：{0}': 'Could not read material file; skipped: {0}',
 '无法读取项目清单 {0}：{1}': 'Could not read project manifest {0}: {1}',
 '无法读取项目配置：{0}': 'Could not read project configuration: {0}',
 '无法锁定项目：{0}': 'Could not lock project: {0}',
 '日期不存在：{0}': 'Date does not exist: {0}',
 '日期格式不正确，应填写完整日期，如 2026-06-02：{0}': 'Invalid date format. Enter a full date such as 2026-06-02: {0}',
 '明细表缺少“入职公司”字段': 'Detail sheet is missing the hiring company field',
 '明细表缺少“姓名”字段': 'Detail sheet is missing the name field',
 '明细表缺少“身份证号码”字段': 'Detail sheet is missing the ID number field',
 '普通目录导入临时位置无效。': 'Invalid temporary folder-import location.',
 '普通目录导入临时文件不完整：{0}': 'Temporary folder-import file is incomplete: {0}',
 '普通目录导入临时文件路径越界。': 'Temporary folder-import path is outside the allowed location.',
 '普通目录导入恢复文件信息无效。': 'Invalid folder-import recovery file metadata.',
 '普通目录导入恢复文件列表无效。': 'Invalid folder-import recovery file list.',
 '普通目录导入恢复文件大小无效。': 'Invalid folder-import recovery file size.',
 '普通目录导入恢复校验信息无效。': 'Invalid folder-import recovery checksum metadata.',
 '普通目录导入恢复版本无效。': 'Invalid folder-import recovery version.',
 '普通目录导入恢复状态无效。': 'Invalid folder-import recovery status.',
 '普通目录导入恢复目标越界。': 'Folder-import recovery target is outside the allowed location.',
 '普通目录导入恢复编号不一致。': 'Folder-import recovery ID mismatch.',
 '普通目录导入恢复记录不属于当前项目。': 'Folder-import recovery record does not belong to this project.',
 '普通目录导入恢复记录包含重复文件。': 'Folder-import recovery record contains duplicate files.',
 '普通目录导入恢复记录格式不受支持。': 'Unsupported folder-import recovery record format.',
 '暂不支持带密码的压缩包': 'Password-protected archives are not supported',
 '暂时无法确认最新正式版本，请稍后重试。': 'The latest stable release could not be confirmed. Try again later.',
 '更新包 SHA256 校验失败。': 'Update SHA-256 verification failed.',
 '更新包下载失败，已按顺序尝试：': 'Update download failed. Tried in order:',
 '更新包不是有效的 zip 文件。': 'The update package is not a valid ZIP file.',
 '更新包中单个文件体积异常，已拒绝解压。': 'An update file exceeds the size limit; extraction refused.',
 '更新包中存在异常压缩条目，已拒绝解压。': 'An update archive entry is invalid; extraction refused.',
 '更新包中的独立更新程序不是普通文件，已拒绝执行。': 'The updater in the package is not a regular file; execution refused.',
 '更新包中的独立更新程序体积异常，已拒绝执行。': 'The updater exceeds the size limit; execution refused.',
 '更新包中的独立更新程序压缩比异常，已拒绝执行。': "The updater's compression ratio is invalid; execution refused.",
 '更新包中的独立更新程序数据不完整。': 'The packaged updater is incomplete.',
 '更新包包含重复或大小写冲突的路径。': 'The update contains duplicate or case-colliding paths.',
 '更新包包含链接或特殊文件，已拒绝解压。': 'The update contains links or special files; extraction refused.',
 '更新包包含非法路径。': 'The update contains an invalid path.',
 '更新包地址均不可用，已按顺序尝试：': 'All update download addresses are unavailable. Tried in order:',
 '更新包文件数量异常，已拒绝解压。': 'The update file count exceeds the limit; extraction refused.',
 '更新包条目实际体积与声明不一致。': "An update entry's actual size differs from its metadata.",
 '更新包条目数据不完整。': 'An update entry is incomplete.',
 '更新包缺少 _internal 目录。': 'The update is missing the _internal folder.',
 '更新包缺少主程序：{0}': 'The update is missing the application executable: {0}',
 '更新包解压后总体积异常，已拒绝解压。': 'The extracted update exceeds the total size limit; extraction refused.',
 '更新包超过允许的最大体积，已停止下载。': 'The update exceeds the maximum size; download stopped.',
 '更新后目录缺少 HRToolkit 主程序。': 'The updated folder is missing the HR Toolkit executable.',
 '更新后目录缺少 _internal 目录。': 'The updated folder is missing _internal.',
 '更新文件不存在：{0}': 'Update file not found: {0}',
 '更新缓存正在使用或暂不可用，请稍后重试。': 'The update cache is in use or unavailable. Try again later.',
 '更新运行检查未能正确读取测试配置。': 'Update runtime check could not read the test configuration.',
 '更新运行检查的平台安装包解析异常。': 'Update runtime check could not resolve the platform installer.',
 '更新运行检查错误地提示重复升级。': 'Update runtime check incorrectly offered a repeated upgrade.',
 '更新配置不是有效的 JSON。': 'Update configuration is not valid JSON.',
 '更新配置中没有 {0} 平台的安装包。': 'No installer for platform {0} in the update configuration.',
 '更新配置中的 update_mode 只能是 auto 或 manual。': 'The update_mode must be auto or manual.',
 '更新配置包含不支持的地址协议：{0}。': 'Update configuration contains an unsupported URL scheme: {0}.',
 '更新配置文件过大，已拒绝读取。': 'Update configuration exceeds the size limit; reading refused.',
 '更新配置格式不正确。': 'Invalid update configuration format.',
 '更新配置没有可用的 Gitee 下载地址。': 'No usable Gitee download URL in the update configuration.',
 '更新配置缺少 file_url。': 'Update configuration is missing file_url.',
 '更新配置缺少 sha256。': 'Update configuration is missing sha256.',
 '更新配置缺少 version。': 'Update configuration is missing version.',
 '替换后会改变文件扩展名': 'The change would alter the file extension',
 '最多保存 200 套模板的手动对应关系': 'Up to 200 manual template mappings can be saved',
 '最新 Release 缺少 latest.json 附件。': 'The latest release is missing latest.json.',
 '最新版本 {0} 的所选安装包尚未上传，请稍后重试。': 'The selected installer for version {0} is not uploaded yet. Try again later.',
 '月报': 'Monthly Report',
 '月报统计的开始日期不能晚于结束日期。': 'The monthly report start date cannot be after the end date.',
 '月报统计的开始日期和结束日期需要同时填写，或同时留空。': 'Enter both monthly report dates, or leave both blank.',
 '月报超时': 'Late Monthly Report',
 '有 {0} 张合同页面需要确认归属或完整性，详见待确认资料清单': '{0} contract pages need ownership or completeness review. See the '
                                    'review list.',
 '未写周报': 'Missing Weekly Report',
 '未写月报': 'Missing Monthly Report',
 '未在{0}前 20 行找到字段：{1}': 'Fields not found in the first 20 rows of {0}: {1}',
 '未在所选路径中找到 .xlsx 或 .xls 工资表': 'No .xlsx or .xls payroll workbooks in the selected locations',
 '未在明细表前 20 行找到字段：{0}': 'Fields not found in the first 20 detail rows: {0}',
 '未完成结果隔离位置冲突：{0}': 'Unfinished-results quarantine location conflict: {0}',
 '未找到 .xlsx 或 .xls 保单人员清单。': 'No .xlsx or .xls policy enrollment lists found.',
 '未找到 .xlsx 或 .xls 异动汇总表': 'No .xlsx or .xls personnel-change summaries found',
 '未找到 .xlsx 或 .xls 异动表': 'No .xlsx or .xls personnel-change workbooks found',
 '未找到 .xlsx 或 .xls 数据文件。': 'No .xlsx or .xls data files found.',
 '未找到 .xlsx 或 .xls 档案汇总表。': 'No .xlsx or .xls archive summaries found.',
 '未找到 .xlsx 或 .xls 档案移交表。': 'No .xlsx or .xls archive transfer sheets found.',
 '未找到 .xlsx 或 .xls 社保缴费清单。': 'No .xlsx or .xls social insurance payment lists found.',
 '未找到 Excel 或 WPS COM 组件：{0}': 'Excel or WPS COM component not found: {0}',
 '未找到包含“{0}”的工作表': 'No worksheet containing “{0}” found',
 '未找到包含“公司、姓名、身份证”的档案移交表。': 'No archive transfer sheet with company, name, and ID fields found.',
 '未找到包含姓名和证件号码的表头。': 'No header with name and identification number fields found.',
 '未找到包含姓名和身份证的表头。': 'No header with name and ID fields found.',
 '未找到或不能唯一确定需要的工作表。页名有变化请选择实际工作表；本次没有的可明确标记。': 'Required worksheets could not be uniquely identified. Select '
                                               'the actual sheets, or explicitly mark types unavailable for '
                                               'this run.',
 '未找到更新程序 HRToolkitUpdater，请重新打包发布。': 'HRToolkitUpdater was not found. Rebuild the release package.',
 '未找到要替换的项目：{0}': 'Item to rename not found: {0}',
 '未找到需要的工作表': 'Required Worksheet Not Found',
 '未找到项目标记文件，非有效项目：{0}': 'Project marker missing; not a valid project: {0}',
 '未知': 'Unknown',
 '未能从周报文件名或汇报时间推断周报截止周期，周报未写统计可能不完整。': 'Weekly deadlines could not be inferred from filenames or submission '
                                       'times. Missing-report counts may be incomplete.',
 '未能解析出有效的员工信息，请输入员工姓名/身份证，或上传员工名单表格': 'No valid employee information found. Enter names or IDs, or upload '
                                       'an employee roster.',
 '未识别到保单人员，请确认保单清单格式。': 'No policyholders recognized. Check the policy-list format.',
 '未识别到可拆分的员工数据，请检查明细表的“入职公司”列': 'No employee data available to split. Check the hiring company column.',
 '未识别到明细表中的数据或小计分段': 'No detail data or subtotal sections recognized',
 '未识别险种：{0}': 'Insurance type not recognized: {0}',
 '本地 OCR 引擎运行检查失败：{0}': 'Local OCR runtime check failed: {0}',
 '本地 OCR 引擎返回格式无效：{0}': 'Local OCR engine returned an invalid format: {0}',
 '本地项目工作区运行检查失败。': 'Local project workspace runtime check failed.',
 '本次临时资料暂未清理，将在重新打开项目时重试：{0}': 'Temporary files were not cleaned up. Cleanup will retry when the project '
                               'reopens: {0}',
 '本次历史记录已经结束，不能继续写入资料。': 'This history record has ended and cannot accept more files.',
 '本次处理已停止。': 'Processing stopped.',
 '本次处理批次无法读取。': 'This processing batch could not be read.',
 '本次导入已停止。': 'Import stopped.',
 '本次工作表名称无效': 'Invalid worksheet name for this run',
 '本次工作表选择无效': 'Invalid worksheet selection for this run',
 '本次源文件校验记录已失效，请重新导入。': 'Source verification records expired. Import the files again.',
 '本次识别预计还需约 {0} MB，当前可用约 {1} MB，已安全停止；当前资料未完成识别，原始资料未修改': 'Recognition needs about {0} MB more, but only {1} '
                                                          'MB is available. Stopped safely; the current '
                                                          'document is incomplete and source files are '
                                                          'unchanged.',
 '本阶段工作项已处理完毕': 'All items in this stage have been processed',
 '本阶段结束：已核对 {0} 个；材料已满足，另有 {1} 个无需识别': 'Stage complete: {0} checked; required materials found, so {1} more '
                                       'items do not need recognition',
 '材料“{0}”已经存在。': 'Material type “{0}” already exists.',
 '来源不存在或是链接：{0}': 'Source is missing or is a link: {0}',
 '来源不是普通文件或文件夹：{0}': 'Source is not a regular file or folder: {0}',
 '校验期间文件发生变化：{0}': 'File changed during verification: {0}',
 '核对人员材料': 'Verify Employee Materials',
 '档案数据检查完成：{0} 条': 'Archive validation complete: {0} records',
 '档案汇总表不存在：{0}': 'Archive summary not found: {0}',
 '档案汇总表中没有可生成档案表的公司数据。': 'The archive summary has no company data for generating archives.',
 '档案汇总表文件、压缩包或文件夹不存在：{0}': 'Archive summary file, archive, or folder not found: {0}',
 '档案汇总表目前只支持 .xlsx 或 .xls 文件。': 'Archive summaries must be .xlsx or .xls.',
 '档案汇总表缺少工作表：{0}，已按模板自动创建。': 'Archive summary missing worksheet {0}; created from the template.',
 '档案移交表文件、压缩包或文件夹不存在：{0}': 'Archive transfer file, archive, or folder not found: {0}',
 '档案移交表路径不存在：{0}': 'Archive transfer path not found: {0}',
 '模板对应设置格式无效': 'Invalid template mapping format',
 '模板资源不是有效的 xlsx：{0}': 'Template resource is not a valid .xlsx file: {0}',
 '正在保存 {0} 档案表...': 'Saving {0} archive…',
 '正在保存已完成的索引': 'Saving Completed Index',
 '正在合并 {0} 档案：{1}/{2}': 'Merging {0} archive: {1}/{2}',
 '正在处理的批次不能移到回收站。': 'A running batch cannot be moved to Trash.',
 '正在处理的记录不能移到回收站。': 'A running record cannot be moved to Trash.',
 '正在处理：': 'Processing:',
 '正在检查列头 {0}/{1}：{2}': 'Checking headers {0}/{1}: {2}',
 '正在生成 {0} 档案：{1}/{2}': 'Generating {0} archive: {1}/{2}',
 '正在识别扫描 PDF：{0}（{1}/{2}）': 'Recognizing scanned PDF: {0} ({1}/{2})',
 '正在读取 PDF 文字层：{0}（{1}/{2}）': 'Reading PDF text: {0} ({1}/{2})',
 '正在读取档案汇总数据：已读取 {0} 条': 'Reading archive summary: {0} records read',
 '正在读取档案汇总表...': 'Reading archive summary…',
 '正在读取社保缴费清单：0/{0}': 'Reading social insurance payment lists: 0/{0}',
 '正在读取社保缴费清单：{0}/{1}': 'Reading social insurance payment lists: {0}/{1}',
 '正常': 'Normal',
 '此入口只能复用当前项目中的资料。': 'Only files from the current project can be reused here.',
 '此平台尚无可用的 Gitee 安装包，请联系发布者补充后重试。': 'No Gitee installer is available for this platform. Contact the '
                                    'publisher.',
 '每个字段或工作表最多设置 100 个名称': 'Each field or worksheet supports up to 100 aliases',
 '没有任何历史清单通过安全校验，已停止发布新索引。': 'No historical manifest passed safety checks. A new index was not created.',
 '没有可用的 {0} 原始资料，请重新选择。': 'No usable {0} source files. Select them again.',
 '没有可留存的资料：{0}': 'No files to retain: {0}',
 '没有已选中且需要改名的项目': 'No selected items require renaming',
 '没有找到自定义材料“{0}”。': 'Custom material type “{0}” not found.',
 '没有找到需要恢复的历史索引文件。': 'No history index file to recover.',
 '活动项目中已存在位置不同的同一批次。': 'The active project contains the same batch at another location.',
 '源文件不存在：{0}': 'Source file not found: {0}',
 '源文件校验记录失效，请重新选择资料。': 'Source verification records expired. Select the files again.',
 '照片人员归属冲突，未提取：{0}': 'Conflicting photo ownership; not retrieved: {0}',
 '用户已取消更新包下载。': 'Update download canceled by the user.',
 '用户选择不合并：{0}': 'Excluded by user: {0}',
 '用户配置中地区或编号重复，请先修改已有条目。': 'Duplicate region or code in custom settings. Edit the existing entry first.',
 '留存源文件的批次不能延迟创建资料目录。': 'Batches that retain sources cannot defer creating their material folders.',
 '疑似多页劳动合同未自动合并（无法确认结束页）：{0}；请保留连续页码或签字页标记': 'Possible multi-page contract not merged because the final page '
                                             'could not be confirmed: {0}. Keep consecutive page numbers or '
                                             'signature-page markers.',
 '目标 {0} 执行前已存在，未覆盖': 'Target {0} existed before execution; not overwritten',
 '目标位置不是有效目录：{0}': 'Target is not a valid folder: {0}',
 '目标名称超过 Windows 单个名称长度限制，请缩短': 'Target name exceeds the Windows filename length limit. Shorten it.',
 '目标文件已存在，不能覆盖：{0}': 'Target file exists and cannot be overwritten: {0}',
 '目标目录已存在，不能覆盖：{0}': 'Target folder exists and cannot be overwritten: {0}',
 '省内存': 'Memory-saving',
 '省内存识别结果尺寸异常，当前资料未完成识别': 'Unexpected memory-saving recognition dimensions; document recognition is '
                          'incomplete',
 '省内存识别结果数量异常，当前资料未完成识别': 'Unexpected memory-saving recognition result count; document recognition is '
                          'incomplete',
 '省内存识别返回了不支持的结果结构，当前资料未完成识别': 'Unsupported memory-saving recognition result structure; document recognition '
                               'is incomplete',
 '确认表历史达到保留上限，请在最近一次结果的《资料待确认.xlsx》中填写确认': 'Review history reached its limit. Enter decisions in the latest '
                                           'results review workbook.',
 '确认表在读取时发生修改，请保存关闭后重试：{0}': 'Review workbook changed while being read. Save and close it, then retry: {0}',
 '可拖入{0}，也可点击选择': 'Drop {0}, or click to browse',
 '可拖入{0}；已填写目标人员时可不选': 'Drop {0}; optional when target employees are entered',
 '可拖入{0}': 'Drop {0}',
 '第 {0} 行': 'Row {0}',
 '文件：{0}': 'File: {0}',
 '结果：{0}': 'Results: {0}',
 '移入：{0}': 'Moved on: {0}',
 '当前版本：HR Toolkit v{0}': 'Current version: HR Toolkit v{0}',
 '当前选中第 {0} 行，请核对。选错了，点另一行即可。': 'Selected row: {0}. Check it, or click a different row to change it.',
 '第 {0} 行，点击设为列名行': 'Row {0}; click to use as headers',
 '另有 {0} 项已识别，可展开下方选项查看或修改。': '{0} more fields recognized. Expand the options below to review them.',
 '原表内容示例：{0}': 'Source sample: {0}',
 '所在工作表：{0}': 'Worksheet: {0}',
 '相对路径：{0}': 'Relative path: {0}',
 '首次确认文件：{0}': 'First confirmed file: {0}',
 '包含 {0}': 'Include {0}',
 '拟用名称 {0}': 'Proposed name for {0}',
 '模板设置（已记住 {0} 项）': 'Template Settings ({0} saved)',
 '已记住的选择（{0}）': 'Saved Mappings ({0})',
 '已用 {0} 秒': 'Elapsed: {0} sec',
 '已用 {0} 秒 · 距上次进度更新 {1} 秒；单份资料识别期间计数保持不变': 'Elapsed: {0} sec · Last progress update: {1} sec ago. Counts '
                                            'stay unchanged while recognizing a document.',
 '处理完成 · {0} 条提醒/运行信息': 'Completed · {0} notices',
 '新版本为 v{0}，你当前使用的是 v{1}。是否现在更新？': 'Version {0} is available. You have version {1}. Update now?',
 '重启以更新，版本{0}': 'Restart to update to version {0}',
 '{0}对应列（必须选择）': '{0} column (required)',
 '{0}对应列（可不选）': '{0} column (optional)',
 '{0}数据所在页': 'Worksheet for {0}',
 '数据排列方式：{0}': 'Data layout: {0}',
 '读取方式：{0}': 'Reading mode: {0}',
 '生效名称：{0}': 'Active aliases: {0}',
 '内容预览：{0}': 'Preview: {0}',
 '请确认“{0}”在哪一列': 'Select the column for “{0}”',
 '请确认这些内容对应的列：{0}': 'Select columns for: {0}',
 '还需要选择：{0}': 'Still needed: {0}',
 '还有 {0} 类模板需要确认。请在上方模板列表中逐个选择。': '{0} template types still need review. Select each one above.',
 '当前模板还需要选择：{0}': 'This template still needs: {0}',
 '请补充“{0}”工作表。': 'Provide the “{0}” worksheet.',
 '请选择“{0}”对应的工作表。': 'Select the worksheet for “{0}”.',
 '“{0}”和“{1}”不能选同一列。': '“{0}” and “{1}” cannot use the same column.',
 '选择“{0}”在原表中的列': 'Select the source column for “{0}”',
 '未设置': 'Not set',
 'Excel 没有对应姓名': 'No name assigned from Excel',
 'Excel 未提供此项目的映射': 'No Excel mapping for this item',
 '源项目重复': 'Duplicate source item',
 '目标名称重复': 'Duplicate target name',
 '目标已存在': 'Target already exists',
 ' · 工作表名称': ' · Worksheet name',
 ' 列': ' column',
 '*参保单位.名称': '*Insurance company.Name',
 '*参保方案.名称': '*Insurance plan.Name',
 '*参保日期': '*Enrollment date',
 '*参保状态': '*Enrollment status',
 '*姓名.简体中文': '*Name.Simplified Chinese',
 '*责任部门.名称': '*Responsible department.Name',
 '*身份证': '*ID number',
 '不参与处理': 'Exclude from processing',
 '丧假': 'Bereavement leave',
 '个人': 'Employee',
 '事假': 'Personal leave',
 '事假\n(天)': 'Personal leave\n(days)',
 '事假\n(小时)': 'Personal leave\n(hours)',
 '事假（天）': 'Personal leave (days)',
 '产假天数': 'Maternity leave days',
 '人员姓名': 'Employee name',
 '伤残死亡限额': 'Disability and death coverage limit',
 '入职公司': 'Employer at hire',
 '入职材料': 'Onboarding documents',
 '公出': 'Off-site work',
 '公司': 'Company',
 '公司档案数据页': 'Company records worksheet',
 '其他': 'Other',
 '养老': 'Pension',
 '加班计调休时长': 'Overtime credited as comp time',
 '劳动合同': 'Employment contract',
 '医疗': 'Medical',
 '单位': 'Organization',
 '原名称': 'Original name',
 '原名称存在 Windows 大小写冲突': 'Original name has a Windows case-insensitive conflict',
 '原有工作表自动识别规则（始终保留）': 'Built-in worksheet recognition rules (always retained)',
 '参保单位': 'Insurance company',
 '参保方案': 'Insurance plan',
 '参保日期': 'Enrollment date',
 '参保状态': 'Enrollment status',
 '参保费种': 'Insurance contribution type',
 '名称不变': 'No change',
 '员工姓名': 'Employee name',
 '员工状态': 'Employee status',
 '在职状态': 'Employment status',
 '备注': 'Notes',
 '外出': 'Out of office',
 '失业': 'Unemployment',
 '婚假': 'Marriage leave',
 '实出勤小时数': 'Hours worked',
 '实际出勤天数': 'Days worked',
 '工伤': 'Work injury',
 '工作日出差': 'Weekday business travel',
 '工资汇总': 'Payroll summary',
 '已恢复原名': 'Original name restored',
 '已暂存待恢复': 'Staged for recovery',
 '带薪休假': 'Paid leave',
 '年假天数': 'Annual leave days',
 '序号': 'No.',
 '应出勤小时数': 'Scheduled hours',
 '应汇报人员名单': 'Expected reporter list',
 '应缴费额(元)': 'Contribution due (CNY)',
 '当日刷卡记录': 'Daily clock records',
 '当月加班时长': 'Monthly overtime hours',
 '当月加班（小时）': 'Monthly overtime (hours)',
 '征收品目': 'Contribution category',
 '总调休': 'Total comp time',
 '总调休\n(小时)': 'Total comp time\n(hours)',
 '总调休（小时）': 'Total comp time (hours)',
 '成本中心': 'Cost center',
 '成本中心.名称': 'Cost center.Name',
 '所属公司': 'Company',
 '所属部门': 'Department',
 '执行状态': 'Execution status',
 '按人汇总的考勤': 'Attendance by employee',
 '探亲假': 'Family visit leave',
 '文件扩展名必须保持不变': 'File extensions must remain unchanged',
 '日期': 'Date',
 '早退': 'Early departures',
 '早退分钟数': 'Minutes left early',
 '早退次数': 'Early departure count',
 '早退（次）': 'Early departures (count)',
 '旷工天数': 'Unexcused absence days',
 '未执行': 'Not executed',
 '本人工资': 'Employee salary',
 '本期应缴费额': 'Current contribution due',
 '材料名称': 'Document name',
 '正在处理，总量尚未确定': 'Processing; total not yet available',
 '此工作表不参与处理': 'This worksheet will be excluded',
 '此工作表不是本次业务数据，不参与处理': 'This worksheet does not contain the required business data and will be excluded',
 '死亡伤残限额': 'Death and disability coverage limit',
 '每人伤残死亡限额': 'Per-person disability and death coverage limit',
 '每日考勤': 'Daily attendance',
 '汇报人': 'Reporter',
 '汇报人部门': "Reporter's department",
 '汇报时间': 'Submission time',
 '汇报编号': 'Report ID',
 '漏打卡': 'Missed clock entries',
 '漏打卡次数': 'Missed clock entry count',
 '漏打卡（次）': 'Missed clock entries (count)',
 '特种证书': 'Special certifications',
 '状态': 'Status',
 '病假': 'Sick leave',
 '病假\n(天)': 'Sick leave\n(days)',
 '病假天数': 'Sick leave days',
 '病假（天）': 'Sick leave (days)',
 '目标位置存在 Windows 大小写冲突': 'Target path has a Windows case-insensitive conflict',
 '目标名称重复（不区分大小写）': 'Duplicate target names (case-insensitive)',
 '目标已存在，且该项目未参与改名': 'Target already exists and is not included in this rename batch',
 '相对路径': 'Relative path',
 '确认名称': 'Confirmed name',
 '离职时间': 'Termination date',
 '缴费基数': 'Contribution base',
 '缴费工资': 'Contribution salary',
 '缺卡记录': 'Missing clock records',
 '花名册': 'Employee roster',
 '被保险人姓名': "Insured employee's name",
 '计划上下班时间': 'Scheduled start/end times',
 '证书材料': 'Certificates',
 '证件号': 'ID number',
 '证件号码': 'ID number',
 '请确认对应列：': 'Confirm the matching columns:',
 '请选择原表对应的列': 'Select the matching source column',
 '调休': 'Comp time',
 '调休（小时）': 'Comp time (hours)',
 '责任部门': 'Responsible department',
 '责任部门.名称': 'Responsible department.Name',
 '费率': 'Contribution rate',
 '资格证书': 'Professional certifications',
 '身份证': 'National ID',
 '身份证件号码': 'Identity document number',
 '身份证号': 'National ID number',
 '迟到': 'Late arrivals',
 '迟到分钟数': 'Minutes late',
 '迟到次数': 'Late arrival count',
 '迟到（次）': 'Late arrivals (count)',
 '部门': 'Department',
 '部门/项目': 'Department / project',
 '部门名称': 'Department name',
 '部门片区': 'Department region',
 '部门（片区）': 'Department (region)',
 '险种': 'Insurance type',
 '陪护假': 'Caregiver leave',
 '雇员姓名': 'Employee name',
 '项': 'items',
 '项目.项目名称': 'Project.Project name',
 '项目/部门': 'Project / department',
 '预设名称': 'Profile name',
 'Excel 顺序改名支持在预览中通过“上移／下移”调整姓名对应关系，无需修改原始 Excel。': 'Excel rename preview now lets you move names up or down '
                                                    'to adjust assignments without editing the workbook.',
 'Windows 更新安装时显示进度窗口，提供安装百分比、当前替换文件及新版启动状态提示。': 'Windows updates display installation progress and the '
                                                 'status of the new app launch.',
 '“检查更新”移至左侧底部，“使用教程”和“更新记录”并排放在右上角。': 'Check for Updates is now at the bottom left; Help and Release Notes '
                                       'are at the top right.',
 '上传的原始资料不再额外保存永久副本，项目只保留处理结果；源文件请自行保管，历史资料仍可正常使用。': 'Projects retain processing results without keeping '
                                                     'permanent copies of uploaded source files. Keep your '
                                                     'originals; existing project files remain available.',
 '下载完成后显示“重启以更新”，点击后安装并重新打开工具，不再单独弹出下载进度窗口。': 'Downloaded updates show Restart to Update, which installs the '
                                              'update and reopens the app.',
 '主滚动条调整至内容面板右侧，去除项目栏顶部多余留白。': 'Moved the main scroll bar to the right edge and removed excess space above '
                               'the project panel.',
 '优化回收站搜索和结果提醒分类切换，减少重复处理。': 'Reduced repeated processing when searching Trash and filtering result notices.',
 '优化窄窗口下部分表单、选择框及较长文字的布局。': 'Improved forms, dropdowns, and long labels in narrow windows.',
 '优化长更新记录的加载与显示，减少界面控件数量和布局开销。': 'Improved long release-note lists with fewer controls and less layout work.',
 '优化项目文件列表刷新，仅更新发生变化的内容，减少整表重建。': 'Project files now refresh only changed items instead of rebuilding the '
                                  'full list.',
 '修复 Windows 本地文件拖入时被误提示需要再次保存，以及快速松手导致文件无法带入的问题。': 'Fixed local Windows files being rejected when dropped, '
                                                    'including quick drag-and-drop gestures.',
 '修复 Windows 窗口连续缩放时，新露出区域背景色不一致的问题。': 'Fixed inconsistent background colors when resizing a Windows window.',
 '修复不同目录下同名文件共用工作表选择、可能漏处理数据的问题，兼容压缩包和旧版 Excel 格式。': 'Fixed different files with the same name sharing '
                                                     'worksheet selections and potentially being skipped. '
                                                     'Archives and legacy Excel files remain supported.',
 '修复切换工具时顶部标题和按钮触发布局循环的问题。': 'Fixed header layout loops when switching tools.',
 '修复回收站筛选后选中状态不同步的问题。': 'Fixed selections becoming inconsistent after filtering Trash.',
 '修复工资工具记住工作表名称后，已有列名对应关系失效的问题，兼容此前保存的选择。': 'Fixed saved payroll column mappings becoming unavailable after '
                                            'saving worksheet names; existing choices remain compatible.',
 '修复更新记录初始化时可能出现的显示异常。': 'Fixed display issues when initializing release notes.',
 '修复点击侧栏图标后边框一直保留，以及更新弹窗按钮出现深色描边的问题。': 'Fixed persistent sidebar icon borders and dark outlines on update '
                                       'dialog buttons.',
 '修复生成结果或刷新项目文件后，已展开的目录自动折叠的问题。': 'Fixed expanded project folders collapsing after processing or refreshing.',
 '修复社保各险种补差日期互相串用的问题，分别按实际补差期间显示；无对应补差数据时不显示日期。': 'Fixed adjustment dates being shared between social '
                                                  'insurance types. Each type now shows its own adjustment '
                                                  'period, or no date when no adjustment exists.',
 '修复社保明细导出后数据行边框、比例和金额格式丢失的问题。': 'Fixed missing row borders, percentage formats, and currency formats in '
                                 'exported social insurance details.',
 '修复系统自动生成的文件导致回收站批次无法恢复的问题，恢复时仍会检查实际资料是否完整、是否被修改。': 'Fixed system-generated files preventing batches from '
                                                     'being restored from Trash. Restoration still verifies '
                                                     'that business files are intact and unchanged.',
 '修复考勤明细排序不符合要求的问题，按“应汇报人员名单”顺序输出。': 'Attendance details now follow the expected reporters roster order.',
 '修复输入检查或模板确认尚未完成时提前创建输出目录、重复处理留下空目录的问题。': 'Fixed empty output folders being created before input or '
                                           'template checks finished.',
 '修复部分 Excel 导出范围不完整时，社保工具可能跳过主数据页、误读其他工作表的问题。': 'Fixed some Excel exports causing social insurance data to '
                                                 'be skipped or read from the wrong worksheet.',
 '修复顶部窗口按钮与折叠图标未对齐的问题。': 'Fixed window buttons and collapse icons being misaligned.',
 '修复项目文件列表变化后，选中高亮与操作目标可能不一致的问题。': 'Fixed project-file selection highlighting becoming inconsistent with the '
                                   'operation target after updates.',
 '修复项目文件拖动无效、部分表单文案拥挤及对齐不一致的问题。': 'Fixed project-file drag-and-drop and improved form spacing and alignment.',
 '修正检查更新时的状态文案，统一显示“正在检查更新…”，避免与下载安装混淆。': 'Update checks consistently show Checking for updates to '
                                          'distinguish them from downloads and installation.',
 '减少更新下载期间的重复刷新及动画绘制开销，优化窗口拖动响应。': 'Reduced repeated refreshes and animations during update downloads for '
                                   'smoother window dragging.',
 '减少表单重复计算、重复状态通知及相同界面设置的磁盘写入。': 'Reduced repeated form calculations, state notifications, and settings '
                                 'writes.',
 '升级批量改名预览，支持查看全部项目的原名称、新名称、相对路径及处理状态，并可搜索、筛选和快速定位冲突；优化大批量列表显示，方便核对数千条资料。': 'Rename preview now shows the '
                                                                            'entire batch with original '
                                                                            'names, proposed names, paths, '
                                                                            'and statuses. Search, filters, '
                                                                            'and issue navigation make '
                                                                            'thousands of items easier to '
                                                                            'review.',
 '取消内容区域和资料列表滚动到边缘时的回弹。': 'Removed bounce effects at the edges of scrolling lists.',
 '右侧项目文件栏展开后与中间内容共同分配宽度，不再遮挡操作区域；收起后自动释放空间。': 'The project panel now shares space with the main content '
                                              'instead of covering it, and frees that space when collapsed.',
 '回收站入口移至项目文件面板底部，放在“移到回收站”右侧，方便查找和恢复已移除的批次。': 'Trash is now at the bottom of the project panel beside Move '
                                               'to Trash.',
 '在“更新记录”右侧新增“复制下载地址”，支持选择 Windows 7 或 Windows 10/11 安装包': 'Added Copy Download Link beside Release Notes, '
                                                           'with separate Windows 7 and Windows 10/11 '
                                                           'installers.',
 '增大默认窗口尺寸，并根据屏幕可用空间自动适配。': 'Increased the default window size while adapting to available screen space.',
 '完善各相关工具的工作表适配，支持选择实际工作表，以及添加、修改、删除常用页名；已找到所需页时，多余页仅提示未处理，不额外弹窗。': 'Added worksheet selection and editable '
                                                                    'saved worksheet names across related '
                                                                    'tools. Extra sheets are reported '
                                                                    'without interrupting processing when '
                                                                    'the required sheets are found.',
 '完善预览调整后的安全检查，修改名称或调整对应关系后重新检查重名、无效名称、扩展名及大小写冲突；执行前再次核对资料状态，防止覆盖已有文件。': 'Name edits and mapping changes now '
                                                                         'rerun duplicate, invalid-name, '
                                                                         'extension, and case-insensitive '
                                                                         'collision checks. Files are '
                                                                         'checked again before execution to '
                                                                         'prevent overwrites.',
 '工具自动发现新版本后，在左下角下载并显示进度和百分比，无需手动确认；手动检查更新仍保留更新说明和确认步骤。': 'Available updates download automatically with '
                                                          'progress at the bottom left. Manual checks still '
                                                          'show release notes and confirmation.',
 '左侧菜单支持展开和收起，收起后将鼠标移到图标上可临时查看，点击可固定展开，为小屏幕留出更多操作空间。': 'The sidebar can be collapsed for smaller screens. '
                                                       'Hover to view it temporarily, or click to pin it '
                                                       'open.',
 '已下载完成的更新包会保留，关闭后重新打开工具，无需重复下载。': 'Downloaded updates are retained across app restarts.',
 '恢复并统一可选字段提示，明确追加／删除操作的名称筛选、Excel 映射列名、员工名单及统计日期的留空规则，避免误认为必须填写。': 'Restored consistent optional-field '
                                                                    'guidance for rename filters, Excel '
                                                                    'mapping columns, employee rosters, and '
                                                                    'report date ranges.',
 '支持从右侧项目文件拖动或选择资料带入当前工具。': 'Project files can be selected or dragged into the current tool.',
 '支持拖入文件、文件夹和压缩包，拖动时提示接收范围及文件类型是否支持。': 'Added file, folder, and archive drag-and-drop with supported-type '
                                       'guidance.',
 '整合材料预设管理入口，优化任务状态和处理结果提示。': 'Consolidated material preset controls and improved task and result messages.',
 '新增“地区编号维护”，支持按项目添加、修改和删除自定义编号；同编号或同地区优先使用自定义配置，删除后恢复内置规则。': 'Added project-specific region codes. Custom '
                                                              'codes override matching built-in codes; '
                                                              'deleting them restores the defaults.',
 '新增“已记住的选择”，支持查看、修改和删除列名对应关系；普通列名确认默认仅本次生效，也可选择记住。': 'Added Saved Mappings to review, edit, and delete '
                                                      'column mappings. New selections apply to the current '
                                                      'operation unless saved.',
 '新增“按 Excel 原文件名匹配”，通过“原文件名”和“新名称”两列明确指定改名关系，避免文件顺序不同导致对应错误。': 'Added Match Excel by Original Name, using '
                                                                'explicit original-name and new-name columns '
                                                                'to avoid ordering errors.',
 '新增“替换指定文字”，可批量替换文件或文件夹名称中的部分文字，保留其余名称和文件扩展名；支持按文件夹、PDF、图片、文档或全部类型筛选。': 'Added Replace Text to replace part '
                                                                         'of a file or folder name while '
                                                                         'preserving the rest and its '
                                                                         'extension. Filter by folder, PDF, '
                                                                         'image, document, or all types.',
 '新增“规范名称格式”，支持去除名称首尾空格、合并连续空格及全角空格，并可按需统一横线和下划线。': 'Added Normalize Names to trim leading and trailing '
                                                    'spaces, collapse repeated and full-width spaces, and '
                                                    'optionally standardize hyphens and underscores.',
 '新增批次改名记录和完成清单，保存原名称、新名称及处理结果，方便核对和追溯。': 'Added batch rename logs and completion receipts with original '
                                          'names, final names, and results for review and traceability.',
 '新增预览内手动调整，支持直接修改单个项目的新名称，或取消勾选暂不处理的项目；确认后严格按最终预览执行。': 'Rename preview now supports individual name edits '
                                                        'and exclusions. Execution follows the final '
                                                        'confirmed plan.',
 '日期支持简写输入，模板适配支持定位待处理项，结果提醒支持分类查看。': 'Added compact date entry, navigation to unresolved template fields, '
                                      'and result-notice filters.',
 '更新准备完成后，暂停生成、统计、拆分、汇总、入库、打包和预览等主操作，其他功能仍可使用，正在处理的任务不受影响。': 'When an update is ready, processing actions '
                                                             'are paused until restart. Other features '
                                                             'remain available and running tasks are '
                                                             'unaffected.',
 '更新安装失败或新版未正常启动时保留提示，方便了解当前状态。': 'Update installation failures and launch failures remain visible for '
                                  'troubleshooting.',
 '更新记录仅显示最近10个版本，默认展开最新版本，其他版本点击后查看。': 'Release Notes shows the latest 10 versions, with the newest expanded '
                                       'by default.',
 '窗口较窄时自动收起项目栏，放大后恢复；手动收起后保持关闭。': 'The project panel collapses automatically in narrow windows and returns '
                                  'when space is available. Manual collapse is preserved.',
 '简化模板列名确认，优先显示需要补充选择的内容，支持查看原表示例、筛选列名和定位未完成项。': 'Simplified column mapping to prioritize unresolved fields, '
                                                 'with source previews, column search, and issue navigation.',
 '简化重复入口，缩小顶部留白，调整左右区域背景颜色，让界面更加清爽。': 'Removed redundant entry points, reduced header spacing, and refined '
                                      'panel backgrounds.',
 '统一复选框圆角样式，优化界面细节与操作体验。': 'Standardized checkbox corners and improved UI details.',
 '考勤与周月报中，“新增「公出」列”和“新增「出差」列”移至加班/调休单位右侧，窄窗口下支持横向滚动查看。': 'Added attendance business-duty and business-trip '
                                                         'options beside the overtime/time-off unit '
                                                         'selector, with horizontal scrolling on narrow '
                                                         'screens.',
 '考勤与周月报设置区域在窄窗口下支持横向滚动，避免日期输入框等控件被遮挡。': 'Attendance settings scroll horizontally in narrow windows to keep '
                                         'date inputs accessible.',
 '调整Windows左右侧栏开关的位置，与窗口控制按钮分开；左侧菜单固定展开时，收起图标显示在菜单右上角，Mac版保持不变。': 'Separated Windows sidebar controls from '
                                                                  'window buttons. The collapse control is '
                                                                  'at the top right of a pinned sidebar; '
                                                                  'macOS behavior is unchanged.',
 '调整Windows窗口样式，恢复带有工具Logo和名称的系统标题栏，窗口边框、圆角和阴影随系统支持情况显示。': 'Restored the Windows system title bar with the '
                                                           'app icon and name. Borders, corners, and shadows '
                                                           'follow system support.',
 '调整项目文件面板，项目名称居中显示，文件范围切换和搜索更清晰，“添加”和“刷新”保留图标及文字说明。': 'Refined the project panel with a centered project '
                                                       'name, clearer filtering and search, and labeled Add '
                                                       'and Refresh controls.',
 '项目文件入口移至右上角，点击图标即可展开或收起，展开后图标会跟随面板位置移动。': 'Moved the project panel toggle to the top right; it follows the '
                                            'panel when expanded.',
 'Sage': 'Sage',
 'Sage 设置': 'Sage Settings',
 '历史对话': 'Chat History',
 '新对话': 'New Chat',
 '开始新对话（当前对话会存入历史）': 'Start a new chat (the current one is saved to history)',
 '删除': 'Delete',
 '复制': 'Copy',
 '已复制': 'Copied',
 '重新生成': 'Regenerate',
 '正在读取表格…': 'Reading the tables...',
 '正在思考…': 'Thinking...',
 '正在整理结论…': 'Organizing the answer...',
 '正在核对数字…': 'Checking the numbers...',
 '正在理解你的问题…': 'Working out what you asked...',
 '正在看你问的是什么…': 'Looking at your question...',
 '正在拆解你的问题…': 'Breaking down your question...',
 '正在看这张图…': 'Looking at the image...',
 '正在读你发的截图…': 'Reading your screenshot...',
 '正在辨认图里的内容…': 'Making out what is in the image...',
 '正在看图上的文字…': 'Reading the text in the image...',
 '正在读这份表格…': 'Reading the spreadsheet...',
 '正在核对表头…': 'Checking the column headers...',
 '正在扫一遍数据…': 'Scanning the data...',
 '正在看图，同时翻表格…': 'Going through the image and the spreadsheet...',
 '正在对着图核表格…': 'Checking the spreadsheet against the image...',
 '正在把图和表格对上…': 'Matching the image to the spreadsheet...',
 '正在理思路…': 'Working through it...',
 '正在对比…': 'Comparing...',
 '正在推演…': 'Reasoning it out...',
 '正在权衡几种说法…': 'Weighing a few readings...',
 '正在把线索串起来…': 'Connecting the dots...',
 '正在找规律…': 'Looking for the pattern...',
 '正在组织语言…': 'Finding the words...',
 '正在写成答案…': 'Writing it up...',
 '正在收束成结论…': 'Pulling it into a conclusion...',
 '其他设置…': 'Other settings...',
 '未配置': 'Not configured',
 '智能助手': 'AI Assistant',
 '智能助手（Ctrl+K）': 'AI Assistant (Ctrl+K)',
 '智能助手设置': 'AI Assistant Settings',
 '清空': 'Clear',
 '弹出': 'Pop Out',
 '尚未配置 AI 服务。': 'The AI service is not configured yet.',
 '尚未配置 {0} 的 API Key，请先在设置中填写。': 'No API key for {0} yet — add one in Settings.',
 '去配置 API Key': 'Configure API Key',
 '可以直接提问，也可以把表格或截图粘贴／拖进来让我分析。': 'Ask a question, or paste/drop in tables and screenshots for analysis.',
 '对比我附加的两张表的差异': 'Compare the two tables I attached',
 '谁的增长值更好？': 'Which one grew faster?',
 '工资怎么按入职公司拆分？': 'How do I split payroll by hiring company?',
 '周报几点算超时？': 'When is a weekly report considered late?',
 '移除附件': 'Remove Attachment',
 '附加表格文件': 'Attach Table Files',
 '附加表格或图片（也可以直接粘贴、拖入）': 'Attach tables or images (you can also paste or drop them)',
 '附加要分析的 Excel 表格': 'Attach Excel tables to analyze',
 '提问，或附加表格后描述要分析什么…': 'Ask a question, or attach tables and describe what to analyze...',
 '今天帮你做些什么？': 'What can I do for you today?',
 '松手即可附加：表格直接解析，图片先压缩再读': 'Drop to attach: tables are parsed, images are downscaled before analysis',
 '图片预览': 'Image Preview',
 '用系统程序打开': 'Open with Default App',
 '图片已不在本地缓存中，无法预览': 'The image is no longer in the local cache, so it cannot be previewed',
 '搜索对话…': 'Search chats...',
 '没有匹配的对话': 'No matching chat',
 '改名': 'Rename',
 '对话名称': 'Chat name',
 '看图': 'Vision',
 '换模型': 'Switch model',
 '展开 Sage': 'Expand Sage',
 '粘贴的图片': 'Pasted image',
 '图片粘贴': 'Paste Image',
 '图片附件': 'Image Attachment',
 '附件解析': 'Attachment',
 '图片内容为空，请重新复制或选择。': 'The image is empty. Copy or select it again.',
 '无法识别的图片格式，请改用 PNG、JPG、WEBP、BMP 或 GIF。': 'Unrecognized image format. Use PNG, JPG, WEBP, BMP or GIF.',
 '这张图片无法读取或压缩，请换一张再试（支持 PNG/JPG/WEBP/BMP/GIF）。': 'This image cannot be read or compressed. Try another one (PNG/JPG/WEBP/BMP/GIF).',
 '当前模型可能读不了图片，请在模型菜单切换到带 VL / Vision 的视觉模型。': 'The current model may not read images; switch to a VL / Vision model from the model menu.',
 '写点什么…': 'Write something...',
 '发送': 'Send',
 '停止': 'Stop',
 'Enter 发送 · Shift+Enter 换行 · Ctrl+V 粘图或拖入文件 · Ctrl+K 开关 Sage': 'Enter to send · Shift+Enter for a new line · Ctrl+V pastes an image or drops files · Ctrl+K toggles Sage',
 '服务商': 'Provider',
 '粘贴 API Key': 'Paste API Key',
 '留空使用默认模型': 'Leave empty for the default model',
 '留空使用默认地址': 'Leave empty for the default endpoint',
 '模型': 'Model',
 '添加模型…': 'Add model...',
 '模型名称，例如 MiniMax-M3': 'Model name, e.g. MiniMax-M3',
 'MiniMax-M3 支持图片，M2.x 系列只认文字。': 'MiniMax-M3 reads images; the M2.x line is text only.',
 '智谱 GLM': 'Zhipu GLM',
 '通义千问': 'Qwen',
 '可选：': 'Available: ',
 '服务地址已按服务商内置，留空即用官方接口；只有自建网关时才需要改，只填域名会自动补全路径。': 'The endpoint is built in per provider \u2014 leave it blank to use the official API. Only change it for your own gateway; a bare domain is completed automatically.',
 '模型名称，例如 ': 'Model name, e.g. ',
 '服务地址': 'Endpoint',
 '显示': 'Show',
 '关闭': 'Close',
 'Key 仅保存在本机，不会写入日志或随项目文件分发；为避免泄露，界面不提供明文查看。': 'The key is stored only on this machine and never written '
                                                          'to logs or shipped with project files. It is '
                                                          'never shown in plain text.',
 '正在测试…': 'Testing...',
 '测试连接': 'Test Connection',
 '已保存。': 'Saved.',
 '选择要分析的表格或图片': 'Select tables or images to analyze',
 '服务地址留空使用默认接口；只填 https://域名/v1 会自动补全为完整接口路径。': 'Leave the endpoint empty for the default; a base URL such as https://host/v1 is completed automatically.',}

# Captures that contain application messages rather than user data.
TRANSLATED_ARGUMENTS = {'^尚未配置\\ (.*?)\\ 的\\ API\\ Key，请先在设置中填写。$': (0,),
 '^(.*?)\\ →\\ (.*?)\\ 改名失败，已停止：(.*?)。已完成\\ (.*?)\\ 项：(.*?)；未处理\\ (.*?)\\ 项：(.*?)。请检查结果并重新预览。$': (2,),
 '^(.*?)\\ 原因：(.*?)$': (0, 1),
 '^(.*?)\\ 改名失败：(.*?)$': (1,),
 '^(.*?)\\ 未完成合并，本次未生成汇总结果：(.*?)$': (1,),
 '^(.*?)\\ 的\\ (.*?)\\ 格式底稿精简失败，已使用原工作簿保留格式：(.*?)$': (2,),
 '^(.*?)\\ 解压失败，已跳过：(.*?)$': (1,),
 '^(.*?)对应列（可不选）$': (0,),
 '^(.*?)对应列（必须选择）$': (0,),
 '^(.*?)数据所在页$': (0,),
 '^Excel\\ 输出兼容性校验失败：(.*?)$': (0,),
 '^OCR\\ 索引缓存写入失败：(.*?)；本次仍使用内存索引完成检索，下次会重新建立。$': (0,),
 '^OCR\\ 缓存写入失败：(.*?)（资料库目录可能为只读），本次未持久化识别结果。$': (0,),
 '^PDF\\ 识别组件运行检查失败：(.*?)$': (0,),
 '^上次运行\\ (.*?)\\ ·\\ (.*?)$': (1,),
 '^历史索引已损坏，原索引已安全备份在\\ (.*?)，但自动整理失败：(.*?)$': (1,),
 '^原因：(.*?)$': (0,),
 '^可拖入(.*?)$': (0,),
 '^可拖入(.*?)，也可点击选择$': (0,),
 '^可拖入(.*?)；已填写目标人员时可不选$': (0,),
 '^后台更新下载失败，稍后重试：(.*?)$': (0,),
 '^处理失败，且项目未能安全结案：(.*?)；(.*?)$': (0, 1),
 '^处理失败：(.*?)$': (0,),
 '^处理完成，用时\\ (.*?)\\ 秒（(.*?)）。$': (1,),
 '^复制失败：(.*?)\\ →\\ (.*?):\\ (.*?)$': (2,),
 '^完成\\ (.*?)，耗时\\ (.*?)\\ 秒$': (0,),
 '^已(.*?)\\ (.*?)\\ 项资料，当前共\\ (.*?)\\ 项。$': (0,),
 '^已复制原件但未完成身份核对：(.*?)；(.*?)$': (1,),
 '^开始(.*?)，请稍候…$': (0,),
 '^开始\\ (.*?)（(.*?)\\ 个资料来源，仅读取原文件，项目只保存结果）$': (0,),
 '^开始\\ (.*?)（资料库只读检索，原件保留在原目录）$': (0,),
 '^当前模板还需要选择：(.*?)$': (0,),
 '^改名已完成，但\\ CSV\\ 清单保存失败。请查看完整改名记录：(.*?)。原因：(.*?)$': (1,),
 '^改名未全部完成，已尝试安全恢复原名；(.*?)\\ 项尚未恢复。请保留结果目录（含临时项目）并查看改名记录：(.*?)。原因：(.*?)$': (2,),
 '^数据排列方式：(.*?)$': (0,),
 '^文件读取异常\\ (.*?):\\ (.*?)$': (1,),
 '^本地\\ OCR\\ 引擎运行检查失败：(.*?)$': (0,),
 '^松开后(.*?)：(.*?)$': (0, 1),
 '^正在保存\\ (.*?)\\ 档案表\\.\\.\\.$': (0,),
 '^正在合并\\ (.*?)\\ 档案：(.*?)/(.*?)$': (0,),
 '^正在生成\\ (.*?)\\ 档案：(.*?)/(.*?)$': (0,),
 '^读取方式：(.*?)$': (0,),
 '^请先(.*?)。$': (0,),
 '^资料识别失败，已跳过\\ (.*?)：(.*?)$': (1,),
 '^还需要选择：(.*?)$': (0,),
 '^预览存在冲突，请修正或排除后重试：(.*?)$': (0,)}

TRANSLATED_ARGUMENTS.update({'^AI\\ 服务返回错误（HTTP\\ (.*?)）：(.*?)$': (1,), '^AI\\ 服务返回错误：(.*?)$': (0,), '^AI\\ 服务返回了空回复。(.*?)$': (0,), '^AI\\ 服务未返回任何回复。(.*?)$': (0,), '^AI\\ 服务未返回有效回复。(.*?)$': (0,), '^AI\\ 服务没有返回流式内容（(.*?)）。请确认服务地址是\\ OpenAI\\ 兼容接口，例如\\ https://api\\.minimax\\.cn/v1/chat/completions(.*?)$': (0, 1)})
