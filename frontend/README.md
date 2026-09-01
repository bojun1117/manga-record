# Frontend — Phase 5

Vue 3 + TypeScript + Vite + Pinia + Tailwind，畫面風格比照舊專案 `comic-vibe`，接的是新的 FastAPI 後端。

這個環境沒裝 Node.js，這次沒辦法像後端那樣先自己跑過 `npm install`/型別檢查再交給你——**麻煩你先跑一次 `npm run type-check`，把錯誤訊息貼給我**，我再照著修，這是這階段跟前面幾個 Phase 最大的差別。

## 本機設定

### 1. 裝套件

```powershell
cd manga-record\frontend
npm install
```

### 2. 確認後端有在跑

`.env.development` 已經指向 `http://localhost:8000`，跟 backend 那邊用同一個 `.env` 裡的 port 一致。先在另一個終端機視窗把 backend 開著（`uvicorn app.main:app --reload --reload-dir app`）。

### 3. 型別檢查（這次麻煩你先跑，我沒辦法先自己驗證）

```powershell
npm run type-check
```

有任何錯誤訊息都貼給我，我來修。

### 4. 啟動開發伺服器

```powershell
npm run dev
```

開瀏覽器 `http://localhost:5173/`。

## Phase 5 驗收流程

1. 開啟首頁應該直接被導去 `/login`（還沒登入）
2. 點「註冊」，建立一個新帳號（帳號 3–30 字元英數字底線、密碼至少 8 字元、兩次密碼要一致）
3. 註冊成功應該直接登入並導回首頁（不用再手動登入一次）
4. 點「＋ 新增漫畫」：
   - 打書名（例如「進擊的巨人」），停頓一下應該會有搜尋中提示，若這是你之前用 curl 測試 Phase 4 時建過的漫畫，應該會跳出建議清單
   - 選一個建議項目，分類欄位應該被鎖住（灰色不可選）
   - 不選建議、直接打全新的書名，分類欄位維持可選，代表會新建一部漫畫
   - 選「待看」以外的狀態，應該會出現卷/話輸入框跟評分星星
5. 新增後應該出現在列表上，卡片可以：
   - 點卷/話數字直接編輯
   - 點星星評分（待看狀態不會顯示這個區塊）
   - 右上角 ⋯ 選單切換狀態、刪除
6. 搜尋框、狀態篩選、分類篩選都能正常縮小列表範圍
7. 登出後應該被導回 `/login`，重新整理頁面不會自動登入（token 被清掉了）
8. 重新登入後，重新整理頁面應該還維持登入狀態，畫面上會出現帳號名稱（這是靠 `/auth/me` 補回來的，見 `stores/auth.ts` 的 `restoreSession`）

## 跟舊系統 comic-vibe 的差異對照

| 項目 | 舊系統 | 這次 |
|---|---|---|
| 登入 | 單一密碼 | 帳號＋密碼，多一個註冊頁 |
| 資料型別 | `Manga`（單一物件） | `CollectionItem`（`manga` + `member_manga` join 後的結果），`id`/`mangaId` 都是 number 不是字串 |
| 新增漫畫 | 直接打書名送出 | 打書名會即時模糊搜尋既有漫畫，選到既有的會鎖分類欄位 |
| 評分 | 只有「已追完」才能填 | 除了「待看」以外的狀態都能填(API 不再限制,見 `docs/API.md`) |
| 「他人推薦」清單 | 有獨立區塊 | 這次 SPEC 沒有這個功能,拿掉了,`plan_to_read` 就是狀態篩選裡的一個選項 |
| 分類 | 5～7 類 | 9 類(多了復仇、生活) |
