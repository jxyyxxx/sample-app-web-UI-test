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
| 报告 | Allure（环境面板含被测地址/浏览器/应用 commit，失败自动截图、步骤链、默认中文） |
| CI | GitHub Actions（push / PR / 手动） |

## 目录结构（测试项目）

```
saucedemo-ui-automation框架/
├── .github/workflows/ui-ci.yml     CI：装 Chromium → 跑用例 → 发布 Allure
├── config/
│   ├── __init__.py
│   └── settings.py                 环境白名单（local/prod）、BASE_URL、ROOT_DIR、移动端视口
├── common/
│   ├── __init__.py
│   ├── data_loader.py              YAML 数据加载（按模块分目录，如 login/accounts.yaml）
│   ├── locator_utils.py            by_test_id：统一用 data-test 契约生成选择器
│   ├── assert_utils.py             公共断言（排序断言走 wait_for_function 自动重试）
│   └── reporting.py                Allure 元数据 + 本地报告生成（默认中文）
├── data/
│   └── login/accounts.yaml         账号数据（标准/锁定/错误密码）
├── pages/                          Page Object
│   ├── base_page.py                公共操作（打开页面、URL 断言）
│   ├── login_page.py               登录页
│   ├── inventory_page.py           商品列表页（加购、角标、排序、菜单）
│   ├── inventory_item_page.py      商品详情页
│   ├── cart_page.py                购物车页（移除、结算入口）
│   ├── checkout_step_one_page.py   结算第一步（收货信息、必填校验）
│   ├── checkout_step_two_page.py   结算第二步（订单概览、总额）
│   ├── checkout_complete_page.py   下单完成页
│   ├── dynamic_catalog_lazy_load_page.py  动态目录：滚动加载
│   ├── dynamic_catalog_spinner_page.py    动态目录：loading 圈 → 网格
│   └── dynamic_catalog_slider_page.py     动态目录：轮播
├── testcases/                      用例（按业务模块分目录）
│   ├── login/test_login.py         登录 5 条（含登出越权）
│   ├── inventory/test_inventory.py 列表/加购/排序/详情/重置 7 条
│   ├── cart/test_cart.py           购物车 1 条
│   ├── checkout/test_checkout.py   结算 5 条（含总额、邮编校验）
│   ├── catalog/test_dynamic_catalog.py  动态目录 5 条（滚动加载/占位符/loading/轮播）
│   └── compat/test_compat.py       兼容性 1 条（移动端视口）
├── conftest.py                     登录态 fixture + 失败截图 + 会话结束生成报告
├── pytest.ini                      标记、testpaths=testcases、strict-markers
├── run.py                          本地一键入口（pytest.main 全量执行）
├── run-tests.cmd                   一键跑用例（直调 .venv 里的 python -m pytest，参数可透传）
├── start-app.cmd                   一键启动被测应用（3000 端口）
└── requirements.txt
```

## 快速开始

### 1. 启动被测应用（本地，推荐）

```cmd
cd /d D:\sample-app-web项目\sample-app-web
npm install
npm run start                 :: Vite 起在 http://localhost:3000
```

也可以直接双击 `start-app.cmd` 一键启动。

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
.venv\Scripts\pytest              :: 全量 24 条
.venv\Scripts\pytest -m smoke     :: 冒烟 3 条
.venv\Scripts\pytest --headed     :: 有界面跑，方便看

:: 需要打线上时，覆盖 BASE_URL 即可
set BASE_URL=https://www.saucedemo.com
.venv\Scripts\pytest -q
```

也可以直接双击 `run-tests.cmd` 一键跑全量；想带参数就在命令行里 `run-tests.cmd -m smoke`，脚本会把参数原样透传给 pytest。

PowerShell 里用 `$env:BASE_URL = 'https://www.saucedemo.com'`（不设则为本地默认值）。

环境切换还有更省事的一层：设 `ENV=prod` 就整体切到线上，`ENV=local` 回本地；写了别的值会在启动时直接报错（白名单校验）。

本地跑完会自动生成 Allure 报告并打开（`CI=true` 时跳过，由流水线生成）。
也可以手动：`allure open reports/allure-html`。

## 用例清单（24 条）

| 模块 | 条数 | 覆盖内容 |
|---|---|---|
| 登录 | 5 | 标准用户登录成功、锁定用户被拒、密码错误、用户名为空、**登出后直接访问内页被拦回登录页** |
| 商品列表 | 7 | 加购 1 件角标为 1、加购 2 件且购物车 2 行、价格升序/降序、名称 A→Z、商品详情与列表一致、**重置 App State 清空购物车** |
| 购物车 | 1 | 移除商品后购物车清空、角标消失 |
| 结算 | 5 | 完整下单、缺名/缺姓各 1 条提示、**缺邮编提示**、**订单总额等于各商品价格之和** |
| 动态目录 | 5 | 滚动到底部追加加载、卡片进入视口由占位符转为真实内容、**loading 圈替换为网格**、点圆点切换商品、**每 2 秒自动轮播** |
| 兼容性 | 1 | **移动端视口 390×844 下登录并加购** |

标记：`smoke`（登录成功 + 加购 + 完整下单，共 3 条）、`login`、`inventory`、`cart`、`checkout`、`catalog`、`compat`。

## 设计要点

1. **分层清晰**：`config/` 管环境与常量，`common/` 管通用能力，`pages/` 管元素与操作，`testcases/` 只写业务步骤。改页面只动对应页面类，改环境只动 `config/settings.py`。
2. **Page Object 模式**：页面元素与操作封装在 `pages/`，用例只写业务步骤。
3. **选择器用契约不用样式**：`common/locator_utils.py` 的 `by_test_id` 统一生成 `[data-test='...']`；类名会随改版变，`data-test` 是应用留给自动化的接口。应用侧确实没有 `data-test` 的元素（如菜单按钮）才退回 `id`。
4. **自动等待，不用 sleep**：全部使用 Playwright 的自动等待与 `expect(...)` 重试断言；排序这类异步重渲染，交给 `wait_for_function` 轮询到"真的有序"，避免读到旧快照而假通过。
5. **失败自动截图**：`conftest.py` 的 `pytest_runtest_makereport` 钩子在用例失败时截全页并附到 Allure 报告。
6. **登录态复用**：`logged_in_page` fixture 统一完成登录，购物车/结算用例不重复写登录步骤。
7. **数据驱动**：账号数据放 `data/login/accounts.yaml`，加账号不改代码。
8. **Allure 步骤链**：页面操作与断言都用 `allure.step` 包起来，失败时能定位到"哪一页、哪一步"。
9. **环境可切换**：`ENV=local|prod` 两档白名单，`BASE_URL` 可单独覆盖；用例代码不动。
10. **覆盖维度**：主流程、权限（越权访问）、状态管理（重置）、排序双向、导航、金额计算、表单必填、移动端视口、动态加载/轮播这类"时序型" UI。

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
