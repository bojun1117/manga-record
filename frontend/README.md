# Frontend

Vue 3 + TypeScript + Vite + Pinia + Tailwind CSS。

## 架構

```
src/
├── api/         # HTTP client 與端點封裝
├── components/
├── stores/      # Pinia stores（auth, collection）
├── views/       # 路由頁面
└── router/
```

呼叫後端走 `api/`（統一封裝 fetch、帶 JWT、處理 401），頁面層的狀態放 Pinia store，元件盡量無狀態。部署到 GitHub Pages（見 [`../.github/workflows/deploy.yml`](../.github/workflows/deploy.yml)），API base URL 由 `.env.production` 指向 CloudFront。

## 相關文件

- API 規格：[`../docs/API.md`](../docs/API.md)
