# ============================================================
# 夹具层：全局公共 fixture 统一放这里
# 作用：封装公共前置逻辑、公共资源
#      所有测试文件不需要 import，直接就能用里面的 fixture
#
# 报告相关（环境面板、生成、默认语言）在 common/reporting.py，
# 这里只负责在 pytest 钩子里调用它。
# ============================================================

import os
import time

import allure
import pytest

from common.data_loader import data_loader
from common.reporting import (
    detect_scope,
    generate_local_report,
    prepare_allure_inputs,
    resolve_results_dir,
    save_trace,
)
from pages.login_page import LoginPage

# 账号数据：data/login/accounts.yaml（加账号不用改代码）
accounts = data_loader.load("login/accounts.yaml")


# ------------------------------------------------------------
# 0.1 会话配置：默认开启 trace（只在失败时保留产物）
#     retain-on-failure = 运行期间录制，用例通过就把产物丢掉、失败才留
#     想临时关掉：TRACE=0；命令行显式传了 --tracing 时以命令行为准
# ------------------------------------------------------------
def pytest_configure(config):
    if os.getenv("TRACE", "1") == "0":
        config.option.tracing = "off"
    elif getattr(config.option, "tracing", "off") == "off":
        config.option.tracing = "retain-on-failure"


# ------------------------------------------------------------
# 0. 会话开始：记录开始时间
#    pytest 9 不再设置 session.start_time（老版本由 Session 自己写），
#    而运行器标签和归档目录名都要用会话开始时间，不能退化成"写文件的时刻"，
#    所以这里自己记一份。
# ------------------------------------------------------------
def pytest_sessionstart(session):
    session.start_time = time.time()


# ------------------------------------------------------------
# 1. 登录页：直接打开登录页，供登录相关用例使用
#    scope="function"：每条用例都从干净的页面开始
# ------------------------------------------------------------
@pytest.fixture
def login_page(page):
    """返回已打开登录页的 Page Object"""
    return LoginPage(page).open()


# ------------------------------------------------------------
# 2. 已登录页面：统一完成标准用户登录
#    购物车/结算等用例直接以已登录状态开始，不重复写登录步骤
# ------------------------------------------------------------
@pytest.fixture
def logged_in_page(page):
    """返回已完成标准用户登录的 page"""
    account = accounts["standard"]
    LoginPage(page).login(account["username"], account["password"])
    return page


# ------------------------------------------------------------
# 3. 失败现场：失败截图（call 阶段）+ trace 路径（teardown 阶段）
#    都只挂附件，不影响用例本身的结果
# ------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        _attach_failure_screenshot(item)
    elif report.when == "teardown":
        _attach_trace(item)


def _attach_failure_screenshot(item):
    page = item.funcargs.get("page")
    if page is None:
        return

    try:
        png = page.screenshot(full_page=True)
        allure.attach(png, name="失败截图", attachment_type=allure.attachment_type.PNG)
    except Exception:
        # 截图失败不能影响用例本身的结果
        pass


def _attach_trace(item):
    """teardown 阶段收 trace：插件到这时代码才把 zip 落到 --output 目录

    retain-on-failure 下通过的用例不留文件，所以目录里至多一个 zip。
    收进来的是"移动"，插件那份不会重复占盘。
    """
    try:
        output_dir = item.config.getoption("--output")
    except (ValueError, AttributeError):
        return

    trace_path = None
    for root, _dirs, files in os.walk(output_dir):
        for name in files:
            if name.startswith("trace") and name.endswith(".zip"):
                trace_path = os.path.join(root, name)
                break
        if trace_path:
            break

    saved = save_trace(trace_path, item.session, item.name)
    if not saved:
        return

    # 统一用 Windows 原生分隔符，粘贴到 CMD / PowerShell 里能直接跑
    shown = os.path.normpath(saved)
    allure.attach(
        f"trace：{shown}\n"
        f'查看：playwright show-trace "{shown}"\n'
        f"或拖到 https://trace.playwright.dev 在线打开",
        name="Trace 路径",
        attachment_type=allure.attachment_type.TEXT,
    )


# ------------------------------------------------------------
# 4. 会话结束：写报告环境面板 + 本地生成报告（含归档）
#    CI 里跳过生成：workflow 已显式生成，且没有浏览器可开
# ------------------------------------------------------------
def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束后：
    1. 准备报告输入：拷历史（趋势）→ 环境面板 + 失败分类 → 运行器
    2. 本地生成 Allure 报告、存回历史、归档、设中文、打开浏览器

    这些都放在会话结束时做，是为了避开 allure 的 --clean-alluredir：
    它在会话开始时清空结果目录，先写会被清掉。
    """
    prepare_allure_inputs(session)

    if os.getenv("CI"):
        return

    generate_local_report(
        results_dir=resolve_results_dir(session),
        scope=detect_scope(session),
        started_at=getattr(session, "start_time", None),
    )
