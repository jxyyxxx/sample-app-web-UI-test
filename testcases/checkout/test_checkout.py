# ============================================================
# 用例层：结算模块
# 覆盖：完整下单、三条必填校验（姓/名/邮编）、商品总额与税额/应付总额
# ============================================================

import allure
import pytest

from pages.inventory_page import InventoryPage


@allure.feature("结算")
@pytest.mark.checkout
class TestCheckout:
    """结算流程：完整下单 + 必填字段校验 + 金额计算"""

    @allure.title("完整下单流程：加购 → 结算 → 填写信息 → 完成")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_checkout_full_flow(self, logged_in_page):
        step_one = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        (
            step_one.fill_info("张三", "测试", "100000")
            .submit()
            .expect_overview()
            .expect_loaded()
            .finish_order()
            .expect_complete()
        )

    @allure.title("结算缺少名字时提示必填")
    def test_checkout_requires_first_name(self, logged_in_page):
        step_one = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        step_one.fill_info("", "测试", "100000").submit()

        step_one.expect_error("First Name is required")

    @allure.title("结算缺少姓氏时提示必填")
    def test_checkout_requires_last_name(self, logged_in_page):
        step_one = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        step_one.fill_info("张三", "", "100000").submit()

        step_one.expect_error("Last Name is required")

    @allure.title("结算缺少邮编时提示必填")
    def test_checkout_requires_postal_code(self, logged_in_page):
        step_one = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .open_cart()
            .start_checkout()
        )

        step_one.fill_info("张三", "测试", "").submit()

        step_one.expect_error("Postal Code is required")

    @allure.title("商品总额、税额与应付总额都与购物车一致")
    def test_cart_total_equals_sum_of_prices(self, logged_in_page):
        cart = (
            InventoryPage(logged_in_page)
            .add_to_cart("sauce-labs-backpack")
            .add_to_cart("sauce-labs-bike-light")
            .open_cart()
        )
        cart.expect_item_count(2)

        expected = round(sum(cart.item_prices()), 2)
        overview = (
            cart.start_checkout()
            .fill_info("张三", "测试", "100000")
            .submit()
            .expect_overview()
        )
        overview.expect_loaded()

        subtotal = overview.subtotal()
        assert subtotal == expected, f"商品总额不符：页面 {subtotal}，期望 {expected}"

        # 应用按 8% 计税，应付总额 = 商品总额 + 税额；任一项算错都能被这条抓住
        expected_tax = round(expected * 0.08, 2)
        tax = overview.tax()
        assert tax == expected_tax, f"税额不符：页面 {tax}，期望 {expected_tax}"

        expected_total = round(expected + expected_tax, 2)
        total = overview.total()
        assert total == expected_total, f"应付总额不符：页面 {total}，期望 {expected_total}"
