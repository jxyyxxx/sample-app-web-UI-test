# ============================================================
# 用例层：登录模块
# 覆盖：正向登录、锁定用户、密码错误、用户名为空、登出后越权访问
# ============================================================

import re

import allure
import pytest
from playwright.sync_api import expect

from common.data_loader import data_loader
from common.locator_utils import by_test_id
from config.settings import BASE_URL
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

# 从 YAML 读取账号数据，加账号不用改代码
accounts = data_loader.load("login/accounts.yaml")


@allure.feature("登录认证")
@pytest.mark.login
class TestLogin:
    """登录模块：正向 + 锁定用户 + 密码错误 + 用户名为空 + 登出越权"""

    @allure.title("标准用户登录成功，进入商品列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_login_success(self, page):
        account = accounts["standard"]
        LoginPage(page).login(
            account["username"], account["password"]
        ).expect_session_cookie(account["username"])
        InventoryPage(page).expect_loaded()

    @allure.title("锁定用户登录被拒")
    def test_login_locked_user(self, page):
        account = accounts["locked"]
        LoginPage(page).login(account["username"], account["password"]).expect_error("locked out")

    @allure.title("密码错误时提示不匹配")
    def test_login_wrong_password(self, page):
        account = accounts["wrong_password"]
        LoginPage(page).login(account["username"], account["password"]).expect_error(
            "Username and password do not match"
        )

    @allure.title("用户名为空时提示必填")
    def test_login_empty_username(self, page):
        LoginPage(page).login("", accounts["standard"]["password"]).expect_error(
            "Username is required"
        )

    @allure.title("登出后直接访问商品页会被重定向到登录页")
    def test_logout_redirects_to_login(self, logged_in_page):
        InventoryPage(logged_in_page).logout()

        # 模拟"未登录直接输 URL 访问内页"，应被前端路由拦回登录页
        logged_in_page.goto(BASE_URL.rstrip("/") + "/inventory.html")

        expect(logged_in_page).to_have_url(
            re.compile(re.escape(BASE_URL.rstrip("/")) + r"/?$")
        )
        expect(logged_in_page.locator(by_test_id("login-button"))).to_be_visible()
