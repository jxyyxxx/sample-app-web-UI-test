# SauceDemo Web UI 自动化测试

基于 Playwright + pytest 的 Web UI 自动化测试项目，被测站点是公开的电商练习网站 [SauceDemo](https://www.saucedemo.com)（登录、商品列表、购物车、结算）。

与同目录的接口自动化项目形成分层：**UI 冒烟 → 接口回归 → 性能容量**。

## 技术栈

| 项 | 内容 |
|---|---|
| 语言 | Python 3.11+ |
| UI 框架 | Playwright（Chromium，headless） |
| 测试框架 | pytest + pytest-playwright |
| 页面封装 | Page Object 模式 |
| 报告 | Allure（失败自动截图、步骤链、本地默认中文） |
| CI | GitHub Actions（push / PR / 手动） |

## 目录结构

```
saucedemo-ui-automation/
├── .github/workflows/ui-ci.yml    CI：装 Chromium → 跑用例 → 发布 Allure
├── common/
│   ├── config.py                  被测地址、账号数据、报告目录
│   └── reporting.py               Allure 报告生成 + 默认中文
├── data/accounts.yaml             账号数据（标准/锁定/错误密码）
├── pages/                         Page Object
│   ├── base_page.py               公共操作（打开页面、URL 断言）
│   ├── login_page.py              登录页
│   ├── inventory_page.py          商品列表页（加购、角标、排序）
│   ├── cart_page.py               购物车页（移除、结算入口）
│   └── checkout_page.py           结算页（填写信息、提交、完成）
├── tests/
│   ├── test_login.py              登录 4 条
│   ├── test_inventory.py          列表/加购/排序 3 条
│   ├── test_cart.py               购物车 1 条
│   └── test_checkout.py           结算 2 条
├── conftest.py                    登录态 fixture + 失败截图 + 会话结束生成报告
├── pytest.ini                     标记、Allure 目录、strict-markers
└── requirements.txt
```

## 快速开始

```cmd
cd /d D:\saucedemo-ui-automation

:: 1. 虚拟环境 + 依赖
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt

:: 2. 下载 Chromium（约 150MB，只需一次）
.venv\Scripts\playwright install chromium

:: 3. 跑用例
.venv\Scripts\pytest              :: 全量 10 条
.venv\Scripts\pytest -m smoke     :: 冒烟 3 条
.venv\Scripts\pytest --headed     :: 有界面跑，方便看
```

本地跑完会自动生成 Allure 报告并打开（`CI=true` 时跳过，由流水线生成）。
也可以手动：`.venv\Scripts\pytest` 后执行 `allure open reports/allure-html`。

**切换被测地址**（指向自己部署的实例）：

```powershell
$env:BASE_URL = 'http://localhost:8080'; .venv\Scripts\pytest -q
```

## 用例清单（10 条）

| 模块 | 条数 | 覆盖内容 |
|---|---|---|
| 登录 | 4 | 标准用户登录成功、锁定用户被拒、密码错误、用户名为空 |
| 商品列表 | 3 | 加购 1 件角标为 1、加购 2 件角标为 2 且购物车 2 行、价格升序排序生效 |
| 购物车 | 1 | 移除商品后购物车清空、角标消失 |
| 结算 | 2 | 完整下单流程（加购→结算→填写→完成）、缺少姓名时提示必填 |

标记：`smoke`（登录成功 + 加购 + 完整下单）、`login`、`inventory`、`cart`、`checkout`。

## 设计要点

1. **Page Object 模式**：页面元素与操作封装在 `pages/`，用例只写业务步骤；页面改版只改对应页面类。
2. **自动等待，不用 sleep**：全部使用 Playwright 的自动等待与 `expect(...)` 重试断言，避免固定等待造成的偶发失败。
3. **失败自动截图**：`conftest.py` 的 `pytest_runtest_makereport` 钩子在用例失败时截全页并附到 Allure 报告。
4. **登录态复用**：`logged_in_page` fixture 统一完成登录，购物车/结算用例不重复写登录步骤。
5. **数据驱动**：账号数据放 `data/accounts.yaml`，加账号不改代码。
6. **Allure 步骤链**：页面操作与断言都用 `allure.step` 包起来，失败时能定位到"哪一页、哪一步"。

## CI

`.github/workflows/ui-ci.yml`：push / PR / 手动触发 → 装依赖与 Chromium → `pytest -q` → `allure generate`（默认中文）→ 上传 artifact；`main` 上成功时发布报告到 GitHub Pages。

> 失败也能拿到报告与截图（`if: always()`），方便排查。

## 已知限制

- 被测站点是公开练习站，UI 可能被官方调整，导致元素定位失效——这也是"UI 自动化要少而稳"的现实例子；
- 只做 Chromium，未覆盖多浏览器；
- 未做视觉回归（截图对比）。
