# ============================================================
# 夹具层：全局公共 fixture 统一放这里
# 作用：封装公共前置逻辑、公共资源
#      所有测试文件不需要 import，直接就能用里面的 fixture
#
# 报告相关（环境面板、生成、默认语言）在 common/reporting.py，
# 这里只负责在 pytest 钩子里调用它。
# ============================================================

import os

import allure
import pytest

from common.data_loader import data_loader
from common.reporting import generate_local_report, prepare_allure_inputs
from pages.login_page import LoginPage

# 账号数据：data/login/accounts.yaml（加账号不用改代码）
accounts = data_loader.load("login/accounts.yaml")


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
# 3. 失败截图：用例失败时截全页并挂到 Allure 报告
#    只拦 call 阶段的失败，不影响用例本身的结果
# ------------------------------------------------------------
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("page")
    if page is None:
        return

    try:
        png = page.screenshot(full_page=True)
        allure.attach(png, name="失败截图", attachment_type=allure.attachment_type.PNG)
    except Exception:
        # 截图失败不能影响用例本身的结果
        pass


# ------------------------------------------------------------
# 4. 会话结束：写报告环境面板 + 本地生成报告
#    CI 里跳过生成：workflow 已显式生成，且没有浏览器可开
# ------------------------------------------------------------
def pytest_sessionfinish(session, exitstatus):
    """
    测试会话结束后：
    1. 准备报告输入：拷历史（趋势）→ 环境面板 + 失败分类 → 运行器
    2. 本地生成 Allure 报告、设中文、打开浏览器

    这些都放在会话结束时做，是为了避开 allure 的 --clean-alluredir：
    它在会话开始时清空结果目录，先写会被清掉。
    """
    prepare_allure_inputs(session)

    if os.getenv("CI"):
        return

    generate_local_report()
