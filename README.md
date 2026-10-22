# SauceDemo Web UI 自动化测试

[![UI CI](https://github.com/jxyyxxx/sample-app-web-UI-test/actions/workflows/ui-ci.yml/badge.svg)](https://github.com/jxyyxxx/sample-app-web-UI-test/actions/workflows/ui-ci.yml)

基于 Playwright + pytest 的 Web UI 自动化测试项目。被测应用是开源电商练习站 SauceDemo（MIT 协议，源码 [saucelabs/sample-app-web](https://github.com/saucelabs/sample-app-web)），**支持本地部署**，也可以指向线上 https://www.saucedemo.com 做对照。

- 仓库地址：<https://github.com/jxyyxxx/sample-app-web-UI-test>
- 在线 Allure 报告：<https://jxyyxxx.github.io/sample-app-web-UI-test/>（需在仓库 Settings → Pages 里把 Source 设为 `gh-pages` 分支后生效）

当前目录约定：

```
D:\sample-app-web项目\
├── sample-app-web\                 被测应用源码（npm run start → http://localhost:3000）
└── saucedemo-ui-automation框架\     本测试项目
```

## 技术栈

| 项 | 内容 |
|---|---|
| 语言 | Python 3.11+ |
| UI 框架 | Playwright（Chromium，headless） |
| 测试框架 | pytest + pytest-playwright |
| 页面封装 | Page Object 模式 |
| 报告 | Allure（失败自动截图、步骤链、本地默认中文） |
| CI | GitHub Actions（push / PR / 手动） |

## 目录结构（测试项目）

```
saucedemo-ui-automation框架/
├── .github/workflows/ui-ci.yml    CI：装 Chromium → 跑用例 → 发布 Allure
├── common/
│   ├── config.py                  被测地址（BASE_URL 可覆盖）、账号数据、报告目录
│   └── reporting.py               Allure 报告生成 + 默认中文
├── data/accounts.yaml             账号数据（标准/锁定/错误密码）
├── pages/                         Page Object
│   ├── base_page.py               公共操作（打开页面、URL 断言）
│   ├── login_page.py              登录页
│   ├── inventory_page.py          商品列表页（加购、角标、排序、菜单）
│   ├── product_detail_page.py     商品详情页
│   ├── cart_page.py               购物车页（移除、结算入口）
│   └── checkout_page.py           结算页（填写信息、提交、完成、总额）
├── tests/
│   ├── test_login.py              登录 5 条（含登出越权）
│   ├── test_inventory.py          列表/加购/排序/详情/重置 7 条
│   ├── test_cart.py               购物车 1 条
│   ├── test_checkout.py           结算 4 条（含总额、邮编校验）
│   └── test_compat.py             兼容性 1 条（移动端视口）
├── conftest.py                    登录态 fixture + 失败截图 + 会话结束生成报告
├── pytest.ini                     标记、Allure 目录、strict-markers
├── run.py                         本地一键入口（pytest.main 全量执行）
└── requirements.txt
```

## 快速开始

### 1. 启动被测应用（本地，推荐）

```cmd
cd /d D:\sample-app-web项目\sample-app-web
npm install
npm run start                 :: Vite 起在 http://localhost:3000
```

> Node 要求 `>=24.9.0`（当前本机 24.19.0 满足）；`npm run start` 是开发服务器，改代码会自动热更新。

### 2. 安装测试依赖（首次）

```cmd
cd /d D:\sample-app-web项目\saucedemo-ui-automation框架
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\playwright install chromium
```

### 3. 运行用例

```cmd
:: 默认打本地（http://localhost:3000），不用设环境变量
.venv\Scripts\pytest              :: 全量 18 条
.venv\Scripts\pytest -m smoke     :: 冒烟 3 条
.venv\Scripts\pytest --headed     :: 有界面跑，方便看

:: 需要打线上时，覆盖 BASE_URL 即可
set BASE_URL=https://www.saucedemo.com
.venv\Scripts\pytest -q
```

PowerShell 里用 `$env:BASE_URL = 'https://www.saucedemo.com'`（不设则为本地默认值）。

本地跑完会自动生成 Allure 报告并打开（`CI=true` 时跳过，由流水线生成）。
也可以手动：`allure open reports/allure-html`。

## 用例清单（18 条）

| 模块 | 条数 | 覆盖内容 |
|---|---|---|
| 登录 | 5 | 标准用户登录成功、锁定用户被拒、密码错误、用户名为空、**登出后直接访问内页被拦回登录页** |
| 商品列表 | 7 | 加购 1 件角标为 1、加购 2 件且购物车 2 行、价格升序/降序、名称 A→Z、商品详情与列表一致、**重置 App State 清空购物车** |
| 购物车 | 1 | 移除商品后购物车清空、角标消失 |
| 结算 | 4 | 完整下单、缺姓名提示、**缺邮编提示**、**订单总额等于各商品价格之和** |
| 兼容性 | 1 | **移动端视口 390×844 下登录并加购** |

标记：`smoke`（登录成功 + 加购 + 完整下单）、`login`、`inventory`、`cart`、`checkout`、`compat`。

## 设计要点

1. **Page Object 模式**：页面元素与操作封装在 `pages/`，用例只写业务步骤；页面改版只改对应页面类。
2. **自动等待，不用 sleep**：全部使用 Playwright 的自动等待与 `expect(...)` 重试断言，避免固定等待造成的偶发失败。
3. **失败自动截图**：`conftest.py` 的 `pytest_runtest_makereport` 钩子在用例失败时截全页并附到 Allure 报告。
4. **登录态复用**：`logged_in_page` fixture 统一完成登录，购物车/结算用例不重复写登录步骤。
5. **数据驱动**：账号数据放 `data/accounts.yaml`，加账号不改代码。
6. **Allure 步骤链**：页面操作与断言都用 `allure.step` 包起来，失败时能定位到"哪一页、哪一步"。
7. **环境可切换**：默认打本地 `http://localhost:3000`，用 `BASE_URL` 可切到线上；用例代码不动。
8. **覆盖维度**：主流程、权限（越权访问）、状态管理（重置）、排序双向、导航、金额计算、表单必填、移动端视口。

## CI

`.github/workflows/ui-ci.yml`：push / PR / 手动触发 →

1. 拉取测试代码；
2. 克隆被测应用并 **checkout 到固定 commit**（`APP_COMMIT`，不依赖线上站点）；
3. `npm ci` 安装应用依赖（带 npm 缓存）；
4. 安装 Python 依赖与 Chromium（浏览器带缓存）；
5. 启动应用并轮询 `http://localhost:3000` 直到就绪（60 秒超时则打印 `app.log` 后失败）；
6. `pytest -q`（`BASE_URL` 指向本地应用）；
7. `allure generate` + 默认中文 → 上传 artifact；`main` 上成功时发布报告到 GitHub Pages。

> 失败也能拿到报告、截图与应用日志（`if: always()`）。应用版本锁在 commit 上，避免上游改动导致流水线"自己变红"。

## 已知限制

- 只跑 Chromium，未覆盖 Firefox/WebKit；
- 未做视觉回归（截图对比）；
- 登录态未用 `storage_state` 复用（每条用例重新登录，约多 2 秒）；
- 本地应用未纳入本仓库（是独立的上游仓库，放在同级目录 `sample-app-web`）。
