import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from pages.cart_page import CartPage


class InventoryPage(BasePage):
    """商品列表页：/inventory.html（标题、购物车角标、排序、加购）"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.locator(".title")
        self.cart_badge = page.locator(".shopping_cart_badge")
        self.cart_link = page.locator(".shopping_cart_link")
        self.sort_select = page.locator("[data-test='product-sort-container']")
        self.prices = page.locator(".inventory_item_price")

    @allure.step("断言已进入商品列表页")
    def expect_loaded(self):
        expect(self.title).to_have_text("Products")
        return self

    @allure.step("把商品加入购物车：{slug}")
    def add_to_cart(self, slug):
        self.page.locator(f"[data-test='add-to-cart-{slug}']").click()
        return self

    @allure.step("断言购物车角标为：{count}")
    def expect_badge(self, count):
        expect(self.cart_badge).to_have_text(str(count))
        return self

    @allure.step("按价格从低到高排序")
    def sort_by_price_low_to_high(self):
        self.sort_select.select_option("lohi")
        return self

    @allure.step("读取商品价格列表")
    def price_list(self):
        return [float(text.replace("$", "")) for text in self.prices.all_inner_texts()]

    @allure.step("打开购物车")
    def open_cart(self):
        self.cart_link.click()
        # 等导航完成再返回，避免后续断言在旧页面上执行（UI 竞态）
        self.page.wait_for_url("**/cart.html")
        return CartPage(self.page)
