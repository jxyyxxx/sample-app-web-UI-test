import allure
import pytest

from common.config import ACCOUNTS
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


@allure.feature("登录认证")
@pytest.mark.login
class TestLogin:
    """登录模块：正向 + 锁定用户 + 密码错误 + 用户名为空"""

    @allure.title("标准用户登录成功，进入商品列表")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_login_success(self, page):
        account = ACCOUNTS["standard"]
        LoginPage(page).login(account["username"], account["password"])
        InventoryPage(page).expect_loaded()

    @allure.title("锁定用户登录被拒")
    def test_login_locked_user(self, page):
        account = ACCOUNTS["locked"]
        LoginPage(page).login(account["username"], account["password"]).expect_error("locked out")

    @allure.title("密码错误时提示不匹配")
    def test_login_wrong_password(self, page):
        account = ACCOUNTS["wrong_password"]
        LoginPage(page).login(account["username"], account["password"]).expect_error(
            "Username and password do not match"
        )

    @allure.title("用户名为空时提示必填")
    def test_login_empty_username(self, page):
        LoginPage(page).login("", ACCOUNTS["standard"]["password"]).expect_error(
            "Username is required"
        )
