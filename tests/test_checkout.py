import allure
import pytest

from pages.inventory_page import InventoryPage


@allure.feature("结算")
@pytest.mark.checkout
class TestCheckout:
    """结算流程：完整下单 + 必填字段校验 + 总额计算"""

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

    @allure.title("结算缺少邮编时提示必填")
    def test_checkout_requires_postal_code(self, logged_in_page):
        checkout = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        checkout.fill_info("张三", "测试", "").continue_to_overview()

        checkout.expect_error("Postal Code is required")

    @allure.title("订单商品总额等于购物车各商品价格之和")
    def test_cart_total_equals_sum_of_prices(self, logged_in_page):
        cart = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .add_to_cart("sauce-labs-bike-light")
            .open_cart()
        )
        cart.expect_item_count(2)

        expected = round(sum(cart.item_prices()), 2)
        checkout = cart.start_checkout().fill_info("张三", "测试", "100000").continue_to_overview()
        checkout.expect_overview()

        actual = checkout.subtotal()
        assert actual == expected, f"订单总额不符：页面 {actual}，期望 {expected}"
