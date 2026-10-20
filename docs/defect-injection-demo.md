# 缺陷注入演示记录（方案 C）

目的：证明这套 UI 用例**真的能抓到 bug**，而不是"只要页面能打开就绿"。

## 环境

| 项 | 值 |
|---|---|
| 被测应用 | `D:\sample-app-web项目\sample-app-web`（本地 Vite 开发服务器，`http://localhost:3000`） |
| 测试项目 | `D:\sample-app-web项目\saucedemo-ui-automation框架` |
| 浏览器 | Playwright Chromium（headless） |

## 注入的缺陷

文件：`sample-app-web/src/utils/Sorting.js`

价格升序排序的比较函数被改成降序（只改一行）：

```js
// 正常（HEAD）
return [...data].sort((a, b) => Number(a[property]) - Number(b[property]));

// 注入缺陷后
return [...data].sort((a, b) => Number(b[property]) - Number(a[property]));
```

改动保存后 Vite 会热更新，不需要重启服务。

## 执行与结果

只跑排序相关用例：

```powershell
$env:CI = 'true'
$env:BASE_URL = 'http://localhost:3000'
.venv\Scripts\python.exe -m pytest tests/test_inventory.py::TestInventory::test_sort_price_low_to_high -q
```

结果：**1 failed**，断言差异显示实际价格从 49.99 开始，而预期是 7.99 开始：

```
-     7.99,
-     9.99,
+     49.99,
+     29.99,
      15.99,
      15.99,
-     29.99,
+     9.99,
-     49.99,
+     7.99,
```

Allure 结果里同时生成了 `失败截图` 附件（`image/png`），说明失败截图钩子生效。

## 还原

把那一行改回升序（或 `git -C sample-app-web restore src/utils/Sorting.js`），重跑同一条用例：

```
1 passed in 1.57s
```

## 面试可以怎么讲（三句话）

1. 我把被测应用部署到本地，因为它开源（MIT），这样我既能回归，也能**造缺陷验证用例有效性**；
2. 我故意把价格升序改成降序，用例立刻失败并给出价格差异，报告里还有失败截图；
3. 还原后用例通过——这一步证明我的用例不是"永远绿"的摆设，而是真的能拦住回归。
