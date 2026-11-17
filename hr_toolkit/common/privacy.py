"""Mask identity numbers in text shown or sent outside business workbooks."""

import re


_IDENTITY_NUMBER = re.compile(r"(?<!\d)(?:\d{17}[\dXx]|\d{15})(?!\d)")


def is_identity_number(text: str) -> bool:
    return len(text) in (15, 18) and _IDENTITY_NUMBER.fullmatch(text) is not None


def mask_identity_numbers(text: str) -> str:
    def mask(match: re.Match) -> str:
        identifier = match[0]
        return identifier[:4] + "*" * (len(identifier) - 8) + identifier[-4:]

    return _IDENTITY_NUMBER.sub(mask, text)
