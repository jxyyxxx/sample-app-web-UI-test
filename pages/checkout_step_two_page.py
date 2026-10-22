import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class CheckoutStepTwoPage(BasePage):
    """结算第二步：/checkout-step-two.html（订单概览、金额明细、提交订单）"""

    path = "/checkout-step-two.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.subtotal_label = page.locator(by_test_id("subtotal-label"))
        self.tax_label = page.locator(by_test_id("tax-label"))
        self.total_label = page.locator(by_test_id("total-label"))
        self.finish_button = page.locator(by_test_id("finish"))

    @allure.step("断言已进入订单概览")
    def expect_loaded(self):
        expect(self.subtotal_label).to_be_visible()
        return self

    @staticmethod
    def _amount(locator):
        """从 "Item total: $39.98" 这类文本里取出金额数值"""
        return float(locator.inner_text().split("$")[1])

    @allure.step("读取订单商品总额（不含税）")
    def subtotal(self):
        return self._amount(self.subtotal_label)

    @allure.step("读取订单税额")
    def tax(self):
        return self._amount(self.tax_label)

    @allure.step("读取订单应付总额（含税）")
    def total(self):
        return self._amount(self.total_label)

    @allure.step("提交订单")
    def finish_order(self):
        self.finish_button.click()
        self.page.wait_for_url("**/checkout-complete.html")
        from pages.checkout_complete_page import CheckoutCompletePage

        return CheckoutCompletePage(self.page)
