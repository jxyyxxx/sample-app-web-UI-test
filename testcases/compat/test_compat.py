# ============================================================
# 用例层：兼容性模块
# 覆盖：移动端视口下主流程可用
# ============================================================

import allure
import pytest

from common.data_loader import data_loader
from config.settings import MOBILE_VIEWPORT
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

accounts = data_loader.load("login/accounts.yaml")


@allure.feature("兼容性")
@pytest.mark.compat
class TestMobileViewport:
    """兼容性：移动端视口下主流程仍然可用"""

    @allure.title("移动端视口 390×844 下登录并加购")
    def test_mobile_viewport_login_and_add_to_cart(self, page):
        page.set_viewport_size(MOBILE_VIEWPORT)

        account = accounts["standard"]
        LoginPage(page).login(account["username"], account["password"])

        InventoryPage(page).expect_loaded().add_to_cart(
            "sauce-labs-backpack"
        ).expect_badge(1)
