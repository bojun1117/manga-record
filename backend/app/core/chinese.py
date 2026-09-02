from functools import lru_cache

from opencc import OpenCC

_normalize_converter = OpenCC("tw2sp")
_traditional_converter = OpenCC("s2twp")


@lru_cache(maxsize=4096)
def normalize_chinese(s: str) -> str:
    if s == "":
        return s
    return _normalize_converter.convert(s).lower()


@lru_cache(maxsize=4096)
def to_traditional(s: str) -> str:
    if s == "":
        return s
    return _traditional_converter.convert(s)
