import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class ProductDetailPage(BasePage):
    """商品详情页：/inventory-item.html?id=xxx"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.name = page.locator(".inventory_details_name")
        self.price = page.locator(".inventory_details_price")
        self.back_button = page.locator("[data-test='back-to-products']")

    @allure.step("断言详情页商品名：{name}")
    def expect_name(self, name):
        expect(self.name).to_have_text(name)
        return self

    @allure.step("读取详情页价格文本")
    def price_text(self):
        return self.price.inner_text().strip()

    @allure.step("返回商品列表")
    def back_to_list(self):
        self.back_button.click()
        self.page.wait_for_url("**/inventory.html")
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page)
