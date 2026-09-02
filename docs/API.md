# API.md — Manga Record Backend Contract

REST API 規格。詳細資料模型定義見 `DATA_MODEL.md`。

---

## 0. 文件導讀

- §1–§2：基礎約定（base URL、認證、時間、錯誤格式）
- §3：資料模型（API 視角）
- §4：endpoint 一覽
- §5：`POST /auth/register`
- §6：`POST /auth/login`
- §7：`GET /auth/me`
- §8：`GET /manga/search`
- §9–§12：`/collections` 系列 endpoint
- §13–§14：`GET /manga`、`PATCH /manga/{id}`（admin only）
- §15：`POST /assistant/query`
- §16：驗證規則總表
- §17：錯誤碼總表

---

## 1. 基礎約定

### 1.1 Base URL

| 環境 | URL |
|---|---|
| 本機開發 | `http://localhost:8000` |
| 正式 | `https://<domain>`（Terraform 部署後決定） |

前端用 `VITE_API_BASE_URL` 讀。

### 1.2 認證

除 `/auth/register`、`/auth/login` 外，所有 endpoint **需要** `Authorization: Bearer <jwt>`。
JWT 由 `POST /auth/login` 簽發，payload 帶 `sub`（`member.id`）。

未帶 / 過期 / 簽章錯誤 → 回 `401 UNAUTHORIZED`。

`GET /manga`、`PATCH /manga/{id}` 除了要有效 JWT，還要求 `member.is_admin = true`，否則回 `403 FORBIDDEN`。

### 1.3 內容格式

- 所有 request / response body 一律 `application/json; charset=utf-8`
- 字串編碼 UTF-8
- 時間一律 **ISO 8601 UTC**
- 數字欄位以 JSON number 表示，不接受字串數字
- `null` 與「欄位不存在」有別：`null` 表示明確清空，key 不存在表示不要動（PATCH 語意）

### 1.4 錯誤回應通用格式

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "current_chapter must be a non-negative integer or null",
    "details": {
      "field": "current_chapter",
      "received": -1
    }
  }
}
```

## 2. 約定的請求行為

- 冪等性：`GET`、`PATCH`、`DELETE` 冪等；`POST /auth/register`、`POST /collections`（新增收藏）**不冪等**
- **PATCH 語意**：partial update，只更新 body 出現的 key
- 回傳完整資源：`POST /collections`、`PATCH /collections/{id}`、`PATCH /manga/{id}` 成功時回傳更新後的完整資源
- 分頁清單一律固定頁大小、`page` 從 1 起算，見 §3.6

---

## 3. 資料模型（API 視角）

### 3.1 收藏項目（`CollectionItem`）

```ts
{
  id: number                      // member_manga.id
  mangaId: number                  // manga.id
  title: string                    // manga.title
  category: MangaCategory
  status: ReadingStatus
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
  lastReadAt: string                // ISO 8601 UTC
  createdAt: string
  updatedAt: string
}
```

### 3.2 漫畫搜尋結果（`MangaSearchResult`，`GET /manga/search`、`GET /manga` 共用）

```ts
{
  id: number
  title: string
  category: MangaCategory
}
```

### 3.3 使用者資料（`GET /auth/me` 回傳）

```ts
{
  id: number
  username: string
  isAdmin: boolean
}
```

### 3.4 漫畫目錄項目（`PATCH /manga/{id}` 回傳）

```ts
{
  id: number
  title: string
  category: MangaCategory
  createdAt: string
  updatedAt: string
}
```

### 3.5 列舉值

`ReadingStatus`：`plan_to_read` / `reading` / `dropped` / `completed`
`MangaCategory`：`hot_blooded` / `mystery` / `adventure` / `romance` / `casual` / `competition` / `revenge` / `slice_of_life` / `other`

（中英對照見 `DATA_MODEL.md`）

### 3.6 分頁清單通用格式

`GET /collections`、`GET /manga` 都回傳這個形狀（`items` 的型別依 endpoint 不同）：

```ts
{
  items: T[]
  page: number       // 從 1 起算，對應 request 帶的 page（未帶則預設 1）
  pageSize: number    // 對應 request 帶的 pageSize（未帶則預設 20，上限 100）
  total: number        // 符合目前篩選條件的總筆數（不是 items.length）
}
```

### 3.7 收藏統計（`GET /collections/stats` 回傳）

```ts
{
  total: number
  planToRead: number
  reading: number
  completed: number
  dropped: number
}
```

不受 `GET /collections` 的 `status`/`category`/`q` 篩選影響，永遠是目前使用者的全站總覽數字。

### 3.8 AI 助理回應（`POST /assistant/query` 回傳）

```ts
{
  answer: string            // AI 對問題的理解摘要，直接顯示在回答框開頭
  items: CollectionItem[]   // 符合條件的收藏，最多 50 筆；問題跟收藏無關時是空陣列
}
```

---

## 4. Endpoint 一覽

| Method | Path | 用途 | 認證 | 成功回應 |
|---|---|---|---|---|
| `POST` | `/auth/register` | 建立帳號 | ❌ | `201 Created` + `{id, username}` |
| `POST` | `/auth/login` | 帳密換 JWT | ❌ | `200 OK` + `{token}` |
| `GET` | `/auth/me` | 目前登入者資訊（含 `isAdmin`） | ✅ | `200 OK` + §3.3 |
| `GET` | `/manga/search?q=` | 模糊查詢漫畫目錄 | ✅ | `200 OK` + `MangaSearchResult[]` |
| `GET` | `/manga?page=` | 分頁列出全站漫畫目錄，最新建立優先（**僅 admin**） | ✅ admin | `200 OK` + §3.6 |
| `PATCH` | `/manga/{id}` | 編輯漫畫目錄（**僅 admin**） | ✅ admin | `200 OK` + §3.4 |
| `GET` | `/collections?...` | 分頁列出目前使用者的收藏，可用 `status`/`category`/`q` 篩選 | ✅ | `200 OK` + §3.6 |
| `GET` | `/collections/stats` | 目前使用者的收藏統計（不受篩選影響） | ✅ | `200 OK` + §3.7 |
| `POST` | `/collections` | 新增收藏 | ✅ | `201 Created` + `CollectionItem` |
| `PATCH` | `/collections/{id}` | 更新收藏（狀態/進度/評分） | ✅ | `200 OK` + `CollectionItem` |
| `DELETE` | `/collections/{id}` | 移除收藏 | ✅ | `204 No Content` |
| `POST` | `/assistant/query` | 自然語言查詢自己的收藏 | ✅ | `200 OK` + §3.8 |

---

## 5. `POST /auth/register`

### Request

```http
POST /auth/register HTTP/1.1
Content-Type: application/json

{ "username": "bojun", "password": "at-least-8-chars" }
```

### 驗證規則

- `username`：3–30 字元，僅允許英數字與底線，全站唯一
- `password`：至少 8 字元（明文只在這次 request 中出現，後端立刻雜湊，不落地儲存明文、不記 log）

### Response 201

```json
{ "id": 42, "username": "bojun" }
```

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | username/password 格式不符 |
| 409 | `USERNAME_TAKEN` | username 已被註冊 |

---

## 6. `POST /auth/login`

### Request

```http
POST /auth/login HTTP/1.1
Content-Type: application/json

{ "username": "bojun", "password": "at-least-8-chars" }
```

### Response 200

```json
{ "token": "eyJhbGciOiJIUzI1NiIs..." }
```

JWT 規格：
- 演算法：HS256
- payload：`{sub: <member.id>, iat, exp}`
- TTL：30 天
- secret：存 AWS Secrets Manager

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | body 缺欄位 |
| 401 | `UNAUTHORIZED` | 帳號不存在或密碼錯誤（**不區分兩者**，避免洩漏帳號是否存在） |

密碼比對：用 bcrypt/argon2 的驗證函式（例如 `bcrypt.checkpw`），本身就是 timing-safe，不需要額外處理。

---

## 7. `GET /auth/me`

```http
GET /auth/me HTTP/1.1
Authorization: Bearer <jwt>
```

回傳目前登入者的帳號資訊（見 §3.3），前端用 `isAdmin` 決定要不要顯示「管理目錄」入口——後端 `GET /manga`、`PATCH /manga/{id}` 本身也會再檢查一次 `is_admin`，前端隱藏入口只是 UX，不是唯一的權限防線。

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 未帶/無效 token |

---

## 8. `GET /manga/search?q=`

### Request

```http
GET /manga/search?q=進撃 HTTP/1.1
Authorization: Bearer <jwt>
```

- `q`：必填，至少 1 字元（trim 後）
- 查詢邏輯：`q` 經繁簡正規化 + 小寫後，對 `manga.normalized_title` 做 `ILIKE '%...%'`
- 回傳最多 20 筆，不分頁（給輸入書名時即時建議用；要瀏覽/管理全站目錄用 §13 的 `GET /manga`）

### Response 200

```json
[
  { "id": 7, "title": "進擊的巨人", "category": "adventure" }
]
```

沒找到 → `[]`（**這不是錯誤**，前端據此判斷「要新建漫畫」）

---

## 9. `GET /collections`

### Request

```http
GET /collections?status=reading&status=dropped&status=completed&category=hot_blooded&q=進擊&page=1&pageSize=20 HTTP/1.1
Authorization: Bearer <jwt>
```

- `status`：選填，可重複帶多次（`status=reading&status=dropped`），代表「符合其中任一個狀態」；完全不帶 = 不篩選狀態（四種都算，包含 `plan_to_read`）
- `category`：選填，單一 `MangaCategory`；不帶 = 不篩選分類
- `q`：選填，比照 `GET /manga/search` 的繁簡正規化模糊比對，對象是這個使用者收藏的 `manga.title`
- `page`：選填，預設 1
- `pageSize`：選填，預設 20，上限 100——由前端決定要拿幾筆，後端不寫死

首頁「待看清單」是獨立區塊，前端對它另外呼叫一次 `GET /collections?status=plan_to_read&...`（`category`/`q` 沿用同一組篩選，只有 `status` 固定成 `plan_to_read`），不是同一份分頁結果裡再切一次。

### Response 200

回傳 §3.6 的分頁格式，`items` 是 `CollectionItem[]`（join `manga` 取得 title/category）。固定依 `lastReadAt` desc 排序。

---

## 10. `GET /collections/stats`

```http
GET /collections/stats HTTP/1.1
Authorization: Bearer <jwt>
```

回傳 §3.7，用於首頁頂部「共 X 部 · 待看 Y · ...」跟「待看清單 (N)」的數字——這兩處都是全站總覽，不受目前的 `status`/`category`/`q` 篩選影響，所以獨立一個不帶篩選參數的 endpoint。

---

## 11. `POST /collections`

### Request

```http
POST /collections HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt>

{
  "mangaName": "咒術迴戰",
  "category": "hot_blooded",
  "status": "plan_to_read",
  "currentVolume": null,
  "currentChapter": null,
  "rating": null
}
```

**沒有 `mangaId` 欄位**——不管是「附加到既有漫畫」還是「建立新漫畫」，一律只送 `mangaName`，由後端統一用 `normalized_title` 解析。這是刻意的簡化：`GET /manga/search` 顯示的候選本來就是靠 `normalized_title` 比對出來的，前端不需要多做一趟「把使用者選的候選 id 記下來再送出」，直接把使用者最終看到／輸入的書名字串送出即可，後端一定能解析回同一筆 `manga`。

### Service 層邏輯（get-or-create by normalized_title）

**整段包在同一個 DB transaction 裡**，中途任何一步失敗就整個 rollback：

1. 把 `mangaName` 正規化（繁簡轉換 + 小寫）成 `normalized_title`
2. 一次 SQL 解決 get-or-create：
   ```sql
   INSERT INTO manga (title, normalized_title, category)
   VALUES (:mangaName, :normalized_title, :category)
   ON CONFLICT (normalized_title) DO UPDATE SET updated_at = now()
   RETURNING id
   ```
   - 如果 `normalized_title` 還不存在 → 真的建立新 manga（`category` 用 request 帶的值，未提供則預設 `'other'`）
   - 如果 `normalized_title` 已存在 → 不新建，直接拿既有那筆的 `id`（**這筆既有 manga 的 `title`／`category` 不會被這次的 request 覆蓋**——`category` 欄位在 request 裡帶了也會被忽略，因為分類屬於漫畫本身，不因為某個人新增收藏而改變）
3. 用步驟 2 拿到的 `manga.id` + 目前登入者 `member.id` 建立 `member_manga` 記錄
   - 若撞到 `UNIQUE(member_id, manga_id)`（代表這個人已經收藏過這部漫畫）→ 回 `409 ALREADY_IN_COLLECTION`

> `ON CONFLICT ... RETURNING id` 這種寫法一次 SQL 呼叫就處理完「有就用、沒有就建」，不需要自己在 service 層寫「先 SELECT、沒有再 INSERT、撞 unique 再 catch 例外」的邏輯，也天生不怕並發 race condition（DB 自己保證原子性）。這同時解決了：模糊查詢選到既有候選（字串經正規化後精確對應到同一筆）、新增全新漫畫、以及前面討論過的「新增流程中途失敗、前端重試」三種情境，全部走同一條路徑。

新增的 `title` 存入前會經過繁簡轉換，一律存繁體（見 `DATA_MODEL.md` `manga`），不管使用者輸入繁體或簡體。

### 驗證規則

- `mangaName`：1–200 字元，trim 過（同 `manga.title` 規則），必填
- `category`：僅在這次 request 導致「真的新建 manga」時才會被採用；若 `mangaName` 解析到既有 manga，帶了也會被忽略
- `status`：未提供 → 預設 `plan_to_read`
- `currentVolume` / `currentChapter`：非負整數或 `null`
- `rating`：`1`–`5` 或 `null`，**不限制狀態**

### Response 201

回傳完整 `CollectionItem`（見 §3.1）。

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | 欄位驗證失敗 |
| 409 | `ALREADY_IN_COLLECTION` | 該使用者已收藏過這部漫畫（`UNIQUE(member_id, manga_id)` 撞到） |

---

## 12. `PATCH /collections/{id}` / `DELETE /collections/{id}`

`PATCH`：body 可帶 `status` / `currentVolume` / `currentChapter` / `rating` 任意子集，partial update。動到 `currentVolume`/`currentChapter` 時 `lastReadAt` 自動刷新。`mangaName`/`category` 不可透過此 endpoint 修改（漫畫本身的屬性不因為個人收藏異動；要換這筆收藏對應的漫畫，語意上應該是刪除重建，不是 PATCH）。

`DELETE`：刪除該筆 `member_manga`，不影響 `manga` 目錄本身。

### 錯誤（兩者共用）

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | PATCH body 驗證失敗 |
| 401 | `UNAUTHORIZED` | 未帶/無效 token |
| 403 | `FORBIDDEN` | 該筆收藏不屬於目前登入的使用者 |
| 404 | `NOT_FOUND` | id 不存在 |

---

## 13. `GET /manga`（admin only）

```http
GET /manga?page=1&pageSize=20 HTTP/1.1
Authorization: Bearer <jwt>
```

分頁列出全站漫畫目錄，依 `created_at` desc 排序（最新建立的在最前面）。給 admin 管理頁面「一開始先瀏覽」用；輸入關鍵字之後管理頁面改叫 §8 的 `GET /manga/search`（不分頁、依標題排序），兩個 endpoint 分工不同，不是同一個查詢加減參數而已。

- `page`：選填，預設 1
- `pageSize`：選填，預設 20，上限 100

### Response 200

回傳 §3.6，`items` 是 `MangaSearchResult[]`。

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 401 | `UNAUTHORIZED` | 未帶/無效 token |
| 403 | `FORBIDDEN` | 目前登入的帳號不是 admin |

---

## 14. `PATCH /manga/{id}`（admin only）

### Request

```http
PATCH /manga/42 HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt>

{ "title": "進擊的巨人", "category": "adventure" }
```

`title`、`category` 都選填，只更新 body 出現的 key。改 `title` 時後端會用新標題重新計算 `normalized_title`（同樣先轉繁體，見 §11），並檢查有沒有撞到其他 manga 的 `normalized_title`。

跟 `PATCH /collections/{id}` 不同：這裡改的是全站共用的 `manga` 目錄本身，不是某個人的收藏，所有收藏這部漫畫的使用者都會看到新標題/分類。

### 驗證規則

- `title`：1–200 字元，trim 過，選填
- `category`：enum 九選一，選填

### Response 200

回傳完整的漫畫目錄項目（見 §3.4）。

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | 欄位驗證失敗 |
| 401 | `UNAUTHORIZED` | 未帶/無效 token |
| 403 | `FORBIDDEN` | 目前登入的帳號不是 admin |
| 404 | `NOT_FOUND` | manga id 不存在 |
| 409 | `DUPLICATE_TITLE` | 改完的標題（正規化後）跟另一部既有 manga 撞了 |

---

## 15. `POST /assistant/query`

### Request

```http
POST /assistant/query HTTP/1.1
Content-Type: application/json
Authorization: Bearer <jwt>

{ "question": "我評分最高的 10 部漫畫" }
```

後端把 `question` 送給 Claude Haiku，請它轉成一組結構化查詢條件（狀態/分類/評分範圍/排序/筆數上限），**不會**讓 AI 直接生 SQL 或碰資料庫——查詢條件驗證過後，套用一般的 SQLAlchemy 查詢，範圍固定是目前登入者自己的收藏，AI 拿不到、也查不到其他使用者的資料。

問題跟使用者的漫畫收藏無關時（閒聊、問別人的收藏），`items` 回空陣列，`answer` 說明沒辦法回答。

### 驗證規則

- `question`：1–500 字元

### Response 200

回傳 §3.8。

### 錯誤

| Status | code | 情境 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | `question` 空白或超過 500 字元 |
| 401 | `UNAUTHORIZED` | 未帶/無效 token |
| 502 | `ASSISTANT_UNAVAILABLE` | Anthropic API 沒設定、逾時、或回傳無法解析的結果 |

---

## 16. 驗證規則總表

| 欄位 | 規則 |
|---|---|
| `username` | 3–30 字元，`^[a-zA-Z0-9_]+$`，全站唯一 |
| `password` | 明文至少 8 字元（僅註冊/登入時出現，不落地） |
| `mangaName` / `title` | trim 後 1–200 字元 |
| `category` | enum 九選一 |
| `status` | enum 四選一 |
| `currentVolume` / `currentChapter` | 整數 0–9999 或 `null` |
| `rating` | 整數 1–5 或 `null`，任何 status 都允許 |
| `page` | 整數，≥ 1，未帶預設 1 |
| `pageSize` | 整數，1–100，未帶預設 20 |
| `question` | trim 後 1–500 字元 |

---

## 17. 錯誤碼總表

| code | Status | 說明 |
|---|---|---|
| `VALIDATION_ERROR` | 400 | 欄位驗證失敗 |
| `MALFORMED_JSON` | 400 | body 不是合法 JSON |
| `UNAUTHORIZED` | 401 | 未認證/認證失敗 |
| `FORBIDDEN` | 403 | 認證成功但無權限操作該資源（含非 admin 呼叫 `GET /manga`、`PATCH /manga/{id}`） |
| `USERNAME_TAKEN` | 409 | 註冊時 username 已存在 |
| `ALREADY_IN_COLLECTION` | 409 | 重複收藏同一部漫畫 |
| `DUPLICATE_TITLE` | 409 | `PATCH /manga/{id}` 改完的標題跟另一部既有 manga 撞了 |
| `NOT_FOUND` | 404 | 資源不存在 |
| `ASSISTANT_UNAVAILABLE` | 502 | AI 助理暫時無法回應（未設定/逾時/回應無法解析） |
| `INTERNAL_ERROR` | 500 | 未預期錯誤 |
