# Frontend

Vue 3 + TypeScript + Vite + Pinia + Tailwind CSS。

## 本機設定

### 1. 裝套件

```powershell
cd manga-record\frontend
npm install
```

### 2. 確認後端有在跑

`.env.development` 指向 `http://localhost:8000`，跟 backend 用同一個 port。先在另一個終端機視窗把 backend 開著（見 [`../backend/README.md`](../backend/README.md)）：

```powershell
uvicorn app.main:app --reload --reload-dir app
```

### 3. 型別檢查與 lint

```powershell
npm run type-check
npm run lint
```

### 4. 啟動開發伺服器

```powershell
npm run dev
```

開瀏覽器 `http://localhost:5173/`。

## 功能

- 帳號＋密碼註冊／登入（JWT，`localStorage` 存 token；偵測到 401 會自動清 token 並導回 `/login`）
- 新增漫畫收藏時對全站漫畫目錄做模糊搜尋（繁簡通用，如「進擊」「进击」都查得到）：選到既有項目會鎖住分類欄位；沒找到則直接新建
- 收藏卡片：點卷/話數字直接編輯、點星星評分（`待看` 狀態不顯示評分區塊）、右上角選單切換狀態／刪除
- 搜尋框、狀態篩選、分類篩選可縮小列表範圍

## 專案結構

```
src/
├── api/       # HTTP client 與端點封裝
├── components/
├── stores/    # Pinia stores (auth, collections)
├── views/     # 路由頁面
└── router/
```
