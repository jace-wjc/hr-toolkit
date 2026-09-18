"""Project overrides for region numbers; built-in relationships stay immutable."""
from __future__ import annotations

import re

REGION_CODES = {
    "总部": "00",
    "南昌": "01",
    "南昌分公司": "01",
    "抚州": "02",
    "鹰潭": "03",
    "达州": "04",
    "乐山": "05",
    "成都": "06",
    "广州": "07",
    "河源": "08",
    "云浮": "09",
    "阳江": "10",
    "茂名": "11",
    "普洱": "12",
    "德宏": "13",
    "上海": "14",
    "新疆": "15",
    "青岛": "16",
    "青海": "17",
    "研发部": "18",
    "南京": "19",
    "福建": "20",
    "河南": "21",
    "湖南": "22",
    "北京": "23",
    "江西工程": "24",
    "惠州": "25",
    "陕西": "26",
    "贵州": "27",
    "攀枝花": "28",
    "山东": "29",
    "西藏": "30",
    "中山": "31",
    "临沧": "32",
    "上饶": "33",
    "公路事业部": "34",
    "九江": "35",
    "湖州": "36",
    "舟山": "37",
    "绍兴": "38",
}


def validate_overrides(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("地区编号配置格式无效，请修正后再处理。")
    result: dict[str, str] = {}
    codes: set[int] = set()
    for name, code in value.items():
        if not isinstance(name, str) or not name.strip() or len(name) > 80 or any(ord(c) < 32 for c in name):
            raise ValueError("地区名称不能为空，且不能包含控制字符。")
        if not isinstance(code, str) or not re.fullmatch(r"[0-9]{1,12}", code):
            raise ValueError("编号须为 1 至 12 位数字，前导零会保留。")
        if name.strip() in result or int(code) in codes:
            raise ValueError("用户配置中地区或编号重复，请先修改已有条目。")
        result[name.strip()] = code
        codes.add(int(code))
    return result


def effective_region_codes(overrides: object = None) -> dict[str, str]:
    custom = validate_overrides({} if overrides is None else overrides)
    overridden_codes = {int(code) for code in custom.values()}
    effective = {name: code for name, code in REGION_CODES.items()
                 if name not in custom and int(code) not in overridden_codes}
    effective.update(custom)
    return effective
