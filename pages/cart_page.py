import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class CartPage(BasePage):
    """购物车页：/cart.html（商品行、移除、结算入口）"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.items = page.locator(".cart_item")
        self.checkout_button = page.locator("[data-test='checkout']")

    @allure.step("移除商品：{slug}")
    def remove(self, slug):
        self.page.locator(f"[data-test='remove-{slug}']").click()
        return self

    @allure.step("读取购物车商品数量")
    def item_count(self):
        return self.items.count()

    @allure.step("读取购物车各商品价格（数值）")
    def item_prices(self):
        texts = self.page.locator(".cart_item .inventory_item_price").all_inner_texts()
        return [float(text.replace("$", "")) for text in texts]

    @allure.step("断言购物车商品数量为：{count}")
    def expect_item_count(self, count):
        # 用 expect 而不是直接读 count：会重试等待 DOM 更新，避免竞态
        expect(self.items).to_have_count(count)
        return self

    @allure.step("进入结算")
    def start_checkout(self):
        self.checkout_button.click()
        self.page.wait_for_url("**/checkout-step-one.html")
        from pages.checkout_page import CheckoutPage

        return CheckoutPage(self.page)
