// 客戶端本地篩選用的繁簡正規化(首頁搜尋框過濾已載入的收藏清單)。
// 跟後端 app/core/chinese.py 是同樣的邏輯,但用途不同:
// 這裡是「已經拿到的資料在瀏覽器裡篩選」,後端那份是「新增漫畫時查詢/去重」。

import { Converter } from 'opencc-js/t2cn'

const t2cn = Converter({ from: 'tw', to: 'cn' })

const cache = new Map<string, string>()

export function normalizeChinese(s: string): string {
  if (s === '') return s
  const cached = cache.get(s)
  if (cached !== undefined) return cached
  const out = t2cn(s).toLowerCase()
  cache.set(s, out)
  return out
}
