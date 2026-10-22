import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class CheckoutCompletePage(BasePage):
    """下单完成页：/checkout-complete.html"""

    path = "/checkout-complete.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.complete_header = page.locator(by_test_id("complete-header"))
        self.back_home_button = page.locator(by_test_id("back-to-products"))

    @allure.step("断言下单完成")
    def expect_complete(self):
        expect(self.complete_header).to_contain_text("Thank you for your order")
        return self

    @allure.step("返回商品列表")
    def back_to_products(self):
        self.back_home_button.click()
        self.page.wait_for_url("**/inventory.html")
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page)
