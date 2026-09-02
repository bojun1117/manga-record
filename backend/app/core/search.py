_LIKE_ESCAPE_MAP = str.maketrans({"%": "\\%", "_": "\\_", "\\": "\\\\"})


def like_pattern(s: str) -> str:
    return f"%{s.translate(_LIKE_ESCAPE_MAP)}%"
