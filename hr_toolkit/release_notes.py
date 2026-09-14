"""Versioned user-facing notes, shared by the app and release metadata.

The release command records the user's notes for each new version here and
keeps previous entries for offline review. Do not infer user-facing changes
from Git commit messages.
"""

from __future__ import annotations


RELEASE_NOTES: dict[str, tuple[str, ...]] = {'0.9.3': ('功能更新',
           '- 更新记录仅显示最近10个版本，默认展开最新版本，其他版本点击后查看。',
           '问题修复',
           '- 调整Windows窗口样式，恢复带有工具Logo和名称的系统标题栏，窗口边框、圆角和阴影随系统支持情况显示。',
           '- 调整Windows左右侧栏开关的位置，与窗口控制按钮分开；左侧菜单固定展开时，收起图标显示在菜单右上角，Mac版保持不变。'),
 '0.9.2': ('功能更新',
           '- 左侧菜单支持展开和收起，收起后将鼠标移到图标上可临时查看，点击可固定展开，为小屏幕留出更多操作空间。',
           '- 项目文件入口移至右上角，点击图标即可展开或收起，展开后图标会跟随面板位置移动。',
           '- 调整项目文件面板，项目名称居中显示，文件范围切换和搜索更清晰，“添加”和“刷新”保留图标及文字说明。',
           '- 回收站入口移至项目文件面板底部，放在“移到回收站”右侧，方便查找和恢复已移除的批次。',
           '- “检查更新”移至左侧底部，“使用教程”和“更新记录”并排放在右上角。',
           '- 简化重复入口，缩小顶部留白，调整左右区域背景颜色，让界面更加清爽。',
           '问题修复',
           '- 修复系统自动生成的文件导致回收站批次无法恢复的问题，恢复时仍会检查实际资料是否完整、是否被修改。',
           '- 修复点击侧栏图标后边框一直保留，以及更新弹窗按钮出现深色描边的问题。',
           '- 修复顶部窗口按钮与折叠图标未对齐的问题。'),
 '0.9.1': ('功能更新',
           '社保、保险、考勤、工资、异动和档案工具统一提供“模板适配”入口，遇到列名或工作表名称不一致时，可预览原表并手动选择对应内容。',
           '同一项内容可保存多个名称，例如“姓名、名字、name”，下次使用自动识别，并支持修改、删除自定义名称，系统默认名称保持不变。',
           '社保明细表新增“补充工伤补差”的基数、比例和金额三列，并计入单位补差合计。',
           '资料打包在内存较小的电脑上可自动使用省内存识别方式，减少因内存不足而中断的情况。',
           '更新前可查看本次更新内容，新版本首次打开会显示更新说明，并可通过“更新记录”随时回看。',
           '调整下载和安装进度窗口，清晰显示下载、文件检查和安装状态，并完善取消下载的操作。',
           '问题修复',
           '修复带薪休假漏计及天数换算不正确的问题，婚假、产假、陪护假、丧假、探亲假、工伤假和年假统一按天汇总。',
           '修复部分社保表中个人缴费金额漏读、个人与单位金额区分不正确的问题。',
           '修复医疗个人补差未计入个人补差合计的问题，补缴金额仍与补差分别统计。',
           '修复补缴月份显示为当前账单月份的问题，按实际补缴月份显示，并与当月正常缴费、补差分开列示。',
           '修复工资拆分后仍保留无人员区域、专业的小计行问题，同步调整相关合计。',
           '修复 Mac 版没有可用更新时误报“检查更新失败”的问题。'),
 '0.9.0': ('更新前可以查看本次新增和修复的内容。',
           '新版本第一次打开时显示更新内容，也可通过“更新记录”随时查看。',
           '统一更新提示、下载和安装进度窗口；下载、校验、安装分别显示当前状态。')}


def notes_for_version(version: str) -> tuple[str, ...]:
    return RELEASE_NOTES.get(version.lstrip("v"), ())


def release_entries(current_version: str) -> list[dict[str, object]]:
    def version_key(value: str) -> tuple[int, ...]:
        return tuple(int(part) for part in value.lstrip("v").split("."))

    current = version_key(current_version)
    return [
        {"version": version, "notes": list(RELEASE_NOTES[version])}
        for version in sorted(RELEASE_NOTES, key=version_key, reverse=True)
        if version_key(version) <= current
    ]
