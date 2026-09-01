# bcrypt 雜湊 / JWT 簽發驗證。AUTH.md 有完整流程說明。

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"

# bcrypt 對輸入長度有 72 bytes 的硬限制，超過會直接丟例外（不同版本行為可能是截斷或報錯，
# 不要依賴任何一種，從輸入端就擋掉）。app/schema/auth.py 的 password 欄位已經設 max_length=72，
# 這裡再檢查一次防呆，不要只信任呼叫端有驗證過。
_BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > _BCRYPT_MAX_BYTES:
        raise ValueError("password exceeds bcrypt's 72-byte limit")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(subject: str) -> str:
    """subject 是 member.id 的字串形式（JWT sub claim 規定要是字串）。"""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(seconds=settings.jwt_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> str:
    """回傳 payload 的 sub。token 無效/過期時 pyjwt 會丟例外，呼叫端（app/api/deps.py）接住轉成 401。"""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    return payload["sub"]
