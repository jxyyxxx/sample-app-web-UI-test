import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage
from pages.checkout_step_one_page import CheckoutStepOnePage

ITEM = by_test_id("inventory-item")
PRICE = by_test_id("inventory-item-price")


class CartPage(BasePage):
    """购物车页：/cart.html（商品行、移除、结算入口）"""

    path = "/cart.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.items = page.locator(ITEM)
        self.checkout_button = page.locator(by_test_id("checkout"))

    @allure.step("移除商品：{slug}")
    def remove(self, slug):
        self.page.locator(by_test_id(f"remove-{slug}")).click()
        return self

    @allure.step("读取购物车商品数量")
    def item_count(self):
        return self.items.count()

    @allure.step("读取购物车商品名称列表")
    def item_names(self):
        return self.page.locator(f"{ITEM} {by_test_id('inventory-item-name')}").all_inner_texts()

    @allure.step("读取购物车各商品价格（数值）")
    def item_prices(self):
        texts = self.page.locator(f"{ITEM} {PRICE}").all_inner_texts()
        return [float(text.replace("$", "")) for text in texts]

    @allure.step("断言购物车商品数量为：{count}")
    def expect_item_count(self, count):
        # 用 expect 而不是直接读 count：会重试等待 DOM 更新，避免竞态
        expect(self.items).to_have_count(count)
        return self

    @allure.step("断言购物车角标消失")
    def expect_no_badge(self):
        expect(self.page.locator(by_test_id("shopping-cart-badge"))).to_have_count(0)
        return self

    @allure.step("返回商品列表")
    def continue_shopping(self):
        self.page.locator(by_test_id("continue-shopping")).click()
        self.page.wait_for_url("**/inventory.html")
        # 延迟导入：列表页与本页互相引用，模块级导入会形成循环
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page)

    @allure.step("进入结算")
    def start_checkout(self):
        self.checkout_button.click()
        self.page.wait_for_url("**/checkout-step-one.html")
        return CheckoutStepOnePage(self.page)
