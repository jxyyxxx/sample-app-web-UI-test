import allure
import pytest

from pages.inventory_page import InventoryPage


@allure.feature("结算")
@pytest.mark.checkout
class TestCheckout:
    """结算流程：完整下单 + 必填字段校验"""

    @allure.title("完整下单流程：加购 → 结算 → 填写信息 → 完成")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_checkout_full_flow(self, logged_in_page):
        checkout = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        checkout.fill_info("张三", "测试", "100000").continue_to_overview().finish_order()

        checkout.expect_complete()

    @allure.title("结算缺少姓名时提示必填")
    def test_checkout_requires_first_name(self, logged_in_page):
        checkout = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        checkout.fill_info("", "测试", "100000").continue_to_overview()

        checkout.expect_error("First Name is required")
