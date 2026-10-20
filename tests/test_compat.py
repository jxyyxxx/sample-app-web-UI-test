import allure
import pytest

from common.config import ACCOUNTS
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage


@allure.feature("兼容性")
@pytest.mark.compat
class TestMobileViewport:
    """兼容性：移动端视口下主流程仍然可用"""

    @allure.title("移动端视口 390×844 下登录并加购")
    def test_mobile_viewport_login_and_add_to_cart(self, page):
        page.set_viewport_size({"width": 390, "height": 844})

        account = ACCOUNTS["standard"]
        LoginPage(page).login(account["username"], account["password"])

        InventoryPage(page).expect_loaded().add_to_cart(
            "sauce-labs-backpack"
        ).expect_badge(1)
