from functools import lru_cache

from opencc import OpenCC

_converter = OpenCC("tw2sp")


@lru_cache(maxsize=4096)
def normalize_chinese(s: str) -> str:
    if s == "":
        return s
    return _converter.convert(s).lower()
