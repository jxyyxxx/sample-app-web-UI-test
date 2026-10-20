import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from pages.cart_page import CartPage
from pages.product_detail_page import ProductDetailPage


class InventoryPage(BasePage):
    """商品列表页：/inventory.html（标题、购物车角标、排序、加购、菜单）"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.locator(".title")
        self.cart_badge = page.locator(".shopping_cart_badge")
        self.cart_link = page.locator(".shopping_cart_link")
        self.sort_select = page.locator("[data-test='product-sort-container']")
        self.prices = page.locator(".inventory_item_price")
        self.names = page.locator(".inventory_item_name")

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

    @allure.step("按价格从高到低排序")
    def sort_by_price_high_to_low(self):
        self.sort_select.select_option("hilo")
        return self

    @allure.step("按名称 A→Z 排序")
    def sort_by_name_a_to_z(self):
        self.sort_select.select_option("az")
        return self

    @allure.step("读取商品价格列表")
    def price_list(self):
        return [float(text.replace("$", "")) for text in self.prices.all_inner_texts()]

    @allure.step("读取商品名称列表")
    def name_list(self):
        return self.names.all_inner_texts()

    @allure.step("打开商品详情：{name}")
    def open_product_detail(self, name):
        self.page.locator(".inventory_item_name", has_text=name).first.click()
        self.page.wait_for_url("**/inventory-item.html?id=*")
        return ProductDetailPage(self.page)

    @allure.step("打开购物车")
    def open_cart(self):
        self.cart_link.click()
        # 等导航完成再返回，避免后续断言在旧页面上执行（UI 竞态）
        self.page.wait_for_url("**/cart.html")
        return CartPage(self.page)

    @allure.step("打开侧边菜单")
    def open_menu(self):
        self.page.click("#react-burger-menu-btn")
        self.page.wait_for_selector("#logout_sidebar_link", state="visible")
        return self

    @allure.step("登出")
    def logout(self):
        self.open_menu()
        self.page.click("#logout_sidebar_link")
        self.page.wait_for_selector("#login-button", state="visible")
        from pages.login_page import LoginPage

        return LoginPage(self.page)

    @allure.step("重置应用状态（清空购物车）")
    def reset_app_state(self):
        self.open_menu()
        self.page.click("#reset_sidebar_link")
        return self
