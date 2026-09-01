# AUTH.md — 認證機制

多使用者版本：帳號＋密碼註冊，登入換 JWT。密碼**單向雜湊**儲存（bcrypt/argon2），不可逆。

## 概念

- 開放註冊，任何人可建立帳號（`username` + `password`，無 email 驗證）
- 密碼絕不落地明文：註冊時雜湊後存 `member.password_hash`，登入時用雜湊比對函式驗證，**沒有任何流程可以把密碼還原回明文**
- JWT secret 存 AWS Secrets Manager，HS256 簽名，30 天過期
- 前端存 `localStorage`（沿用舊系統的做法與取捨，見下方安全考量）

## 為什麼是雜湊而不是加密

早期規劃時曾考慮用「對稱加密（可還原明文）」，最終改為單向雜湊，原因：
- 系統本身從不需要「拿回明文密碼」——登入只需要比對是否相符，雜湊完全做得到
- 雜湊沒有 key 外洩風險：即使整個 DB + Secrets Manager 都外洩，密碼依然無法還原；對稱加密只要 key 也外洩，密碼就等於明文外洩
- 業界標準做法，bcrypt/argon2 刻意設計成運算慢，暴力破解成本高

## 流程

```
使用者 → 前端 RegisterView → POST /auth/register {username, password}
                              ↓
                          bcrypt.hash(password) → 存 member.password_hash
                              ↓
                          201 {id, username}

使用者 → 前端 LoginView → POST /auth/login {username, password}
                          ↓
                       查 member by username
                          ↓
                       bcrypt.checkpw(password, password_hash)
                          ↓
                       對 → 簽 JWT(sub: member.id, 30 天) → 200 {token}
                       錯 → 401 UNAUTHORIZED（帳號不存在/密碼錯都回同樣訊息，避免帳號列舉）

前端把 token 存 localStorage
之後每次打受保護 endpoint 都帶 Authorization: Bearer <token>
```

每個受保護 endpoint 用 `require_auth` FastAPI dependency，沒 token / 過期 / 簽章錯 → 401；JWT payload 的 `sub` 就是操作者的 `member.id`，`/collections` 系列 endpoint 用它過濾「只回這個人的資料」。

## 密碼雜湊參數

- 演算法：bcrypt（`passlib` 或 `bcrypt` 套件）或 argon2
- bcrypt cost factor：12（預設值，個人專案流量不需要調更高）
- 每個密碼雜湊自帶 salt（bcrypt/argon2 內建），不需要另外管理 salt 欄位

## Secrets 管理

- JWT secret、DB 連線字串存 AWS Secrets Manager
- EC2 上的程式啟動時用 IAM instance profile 權限讀取，結果 cache 在記憶體
- ❌ 不寫死在程式碼、Dockerfile、Terraform 檔案裡

## 前端存儲位置

- `localStorage['manga-record.token']`：JWT 字串
- 不存密碼、不存其他使用者資訊

存 localStorage 的安全考量（沿用舊系統的分析）：
- 弱點：同 origin 的任何 JS 都讀得到
- 對策：不引入第三方 JS、只用自己控制的 origin
- 之後部署到正式 domain 可考慮改用 httpOnly cookie + CSRF token（比照舊系統 `AUTH.md` 階段 5 規劃，這次先不做）

## token 失效自動處理

前端偵測到 401：
1. 清掉 localStorage 的 token
2. 路由守衛踢回 `/login`

發生時機：token 過期（30 天）、JWT secret 旋轉、token 被人為清除。

## 之後可以做但這階段不做

- Email 驗證、忘記密碼流程
- httpOnly cookie + CSRF token
- Login 端點 rate limiting（連續失敗鎖定）
- IP allowlist / WAF
