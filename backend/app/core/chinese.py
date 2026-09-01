# 繁簡正規化：任意中文字串轉成簡體 + 小寫，讓 manga.normalized_title 的比對繁簡共通
# （「進擊」「进击」都能對到同一筆）。
# 對應舊系統 comic-vibe 的 src/utils/chinese.ts，邏輯一致，這裡換成
# opencc-python-reimplemented（純 Python，不需要編譯 C 擴充）。

from functools import lru_cache

from opencc import OpenCC

# tw2sp：台灣繁體 -> 簡體，含詞彙差異(軟體->软件)，不只是單純換字，跟前端的
# Converter({ from: 'tw', to: 'cn' }) 對應。
_converter = OpenCC("tw2sp")


@lru_cache(maxsize=4096)
def normalize_chinese(s: str) -> str:
    if s == "":
        return s
    return _converter.convert(s).lower()
