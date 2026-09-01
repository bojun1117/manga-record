# Data Model — Manga Record

三張表：`member`（會員）、`manga`（全站共用漫畫目錄）、`member_manga`（會員收藏，per-user 進度與狀態；表名採標準關聯表命名法，對外 API 仍以「收藏 / collections」稱呼）。

---

## 列舉值

### ReadingStatus（追讀狀態，屬於 `member_manga`）

| 程式碼 | UI 顯示(zh-TW) |
|---|---|
| `plan_to_read` | 待看 |
| `reading` | 追讀中 |
| `dropped` | 棄坑 |
| `completed` | 已追完 |

### MangaCategory（分類，屬於 `manga`）

| 程式碼 | UI 顯示(zh-TW) |
|---|---|
| `hot_blooded` | 熱血 |
| `mystery` | 懸疑 |
| `adventure` | 冒險 |
| `romance` | 愛情 |
| `casual` | 輕鬆 |
| `competition` | 競技 |
| `revenge` | 復仇 |
| `slice_of_life` | 生活 |
| `other` | 其他 |

---

## `member`

```
id            bigserial PK             -- auto increment
username      text UNIQUE NOT NULL     -- 3–30 字元，僅英數字與底線（實作時再細訂）
password_hash text NOT NULL            -- bcrypt/argon2 雜湊，永不存明文
created_at    timestamptz NOT NULL
updated_at    timestamptz NOT NULL
```

- 密碼規則（明文，寫入前雜湊，DB 不留明文）：至少 8 字元
- `username` 全站唯一，註冊時檢查

## `manga`

```
id                bigserial PK
title             text NOT NULL              -- 1–200 字元，trim 過
normalized_title  text UNIQUE NOT NULL       -- title 經繁簡正規化 + 小寫，get-or-create 用的查詢鍵
category          MangaCategory NOT NULL DEFAULT 'other'
created_at        timestamptz NOT NULL
updated_at        timestamptz NOT NULL
```

- 全站共用：不同使用者收藏同一部作品時，共用同一筆 `manga` 記錄
- `normalized_title` 由後端在寫入時自動算出（繁簡轉簡體 + 小寫），前端不需要自己算
- **`normalized_title` 有 UNIQUE 限制**，這個限制在 Postgres 會自動建立對應的唯一索引，不需要另外下 `CREATE INDEX`。用途兩個：
  1. `POST /collections` 用 `INSERT ... ON CONFLICT (normalized_title)` 做 get-or-create（見 `API.md` §9），靠這個限制保證同一標題只會有一筆 manga，新增流程中途失敗、前端重試也不會建出重複資料
  2. 代價：兩部標題完全相同但實際是不同作品的漫畫無法都存在，這階段接受這個限制
  3. 這個索引只加速「精確比對」，`GET /manga/search` 的模糊搜尋（`ILIKE '%...%'`）用不到；之後目錄變大要優化模糊搜尋，需另外加 `pg_trgm` trigram index，是不同的東西
- 沒有 `member_id`：這張表不屬於任何人，是客觀資料
- 這階段沒有「編輯 / 刪除 manga」的 API；`title` / `category` 一旦建立即固定（如發現打錯字，之後再補管理功能）

## `member_manga`

標準關聯表命名（`member` + `manga`），代表「某個會員與某部漫畫之間的收藏關係」，實際存放 per-user 的追讀進度與狀態。

```
id               bigserial PK
member_id        FK -> member.id NOT NULL
manga_id         FK -> manga.id NOT NULL
status           ReadingStatus NOT NULL DEFAULT 'plan_to_read'
current_volume   int NULL CHECK (current_volume >= 0)
current_chapter  int NULL CHECK (current_chapter >= 0)
rating           int NULL CHECK (rating BETWEEN 1 AND 5)
last_read_at     timestamptz NOT NULL
created_at       timestamptz NOT NULL
updated_at       timestamptz NOT NULL

UNIQUE (member_id, manga_id)   -- 同一人對同一部漫畫只能有一筆收藏
```

### 重要規則

- `current_volume` 與 `current_chapter` 各自獨立，可以只填一個、兩個都填、或兩個都空（沿用舊系統規則）
- `rating` **不綁定 status**：任何狀態都可以評分，也可以清空（與舊系統不同的簡化決策）
- `last_read_at` 在 `current_volume` 或 `current_chapter` 被更新時自動刷新為當下時間，用來排序「最近在追的」
- `(member_id, manga_id)` 唯一：同一人不能對同一部漫畫建立兩筆收藏（重複新增時 API 回 409，見 `API.md`）
- 刪除 `member_manga` 記錄**不會**連動刪除 `manga`（其他使用者可能還收藏著同一部作品）

---

## 與前端型別對照

前端 `MangaCollectionItem`（畫面顯示用的合併型別，實際是 `manga` + `member_manga` join 後的結果）：

```typescript
interface MangaCollectionItem {
  id: number                    // member_manga.id（這筆收藏記錄的 id）
  mangaId: number                // manga.id
  title: string                   // manga.title
  category: MangaCategory         // manga.category
  status: ReadingStatus           // member_manga.status
  currentVolume: number | null
  currentChapter: number | null
  rating: number | null
  lastReadAt: string              // ISO 8601 UTC
  createdAt: string
  updatedAt: string
}
```

> API 層仍以「收藏 / collections」稱呼這個資源（`GET/POST /collections` 等），只有 DB 表名採用 `member_manga`；這是刻意的命名分工：表名反映關聯表的技術本質，API 路徑反映使用者看到的概念。

`API.md` §3 有完整的 request/response 結構定義。
