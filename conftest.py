# ============================================================
# 夹具层：登录态 fixture + 失败截图 + 会话结束生成报告
# ============================================================

import os

import allure
import pytest

from common.config import ACCOUNTS, REPORT_DIR, RESULTS_DIR
from common.reporting import generate_local_report
from pages.login_page import LoginPage


@pytest.fixture
def login_page(page):
    """返回已打开登录页的 Page Object"""
    return LoginPage(page).open()


@pytest.fixture
def logged_in_page(page):
    """返回已完成标准用户登录的 page（用例直接以已登录状态开始）"""
    LoginPage(page).login(
        ACCOUNTS["standard"]["username"],
        ACCOUNTS["standard"]["password"],
    )
    return page


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败时自动截图并挂到 Allure 报告里"""
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


def pytest_sessionfinish(session, exitstatus):
    """本地跑完自动生成报告并打开；CI 里由 workflow 生成"""
    if os.getenv("CI"):
        return
    generate_local_report(RESULTS_DIR, REPORT_DIR)
