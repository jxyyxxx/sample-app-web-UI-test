import allure
from playwright.sync_api import Page, expect

from common.assert_utils import assert_utils
from common.locator_utils import by_test_id
from pages.base_page import BasePage
from pages.cart_page import CartPage
from pages.inventory_item_page import InventoryItemPage
from pages.login_page import LoginPage

# 列表页的商品价格与名称：全用 data-test 定位，排序断言也复用这两个选择器
PRICE = by_test_id("inventory-item-price")
NAME = by_test_id("inventory-item-name")

# 侧边菜单开关：应用源码把 data-test="open-menu" 写在自定义图标上，但
# react-burger-menu 会把这个图标替换成纯文本按钮，真实 DOM 里没有该属性，
# 只剩按钮 id。这是全站唯一需要退回 id 定位的元素。
MENU_BUTTON = "#react-burger-menu-btn"


class InventoryPage(BasePage):
    """商品列表页：/inventory.html（标题、购物车角标、排序、加购、菜单）"""

    path = "/inventory.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.locator(by_test_id("title"))
        self.cart_badge = page.locator(by_test_id("shopping-cart-badge"))
        self.cart_link = page.locator(by_test_id("shopping-cart-link"))
        self.sort_select = page.locator(by_test_id("product-sort-container"))
        self.prices = page.locator(PRICE)
        self.names = page.locator(NAME)

    @allure.step("断言已进入商品列表页")
    def expect_loaded(self):
        expect(self.title).to_have_text("Products")
        return self

    @allure.step("把商品加入购物车：{slug}")
    def add_to_cart(self, slug):
        self.page.locator(by_test_id(f"add-to-cart-{slug}")).click()
        return self

    @allure.step("断言商品已在购物车中（按钮变为 Remove）：{slug}")
    def expect_in_cart(self, slug):
        expect(self.page.locator(by_test_id(f"remove-{slug}"))).to_be_visible()
        return self

    @allure.step("断言商品不在购物车中（按钮为 Add to cart）：{slug}")
    def expect_not_in_cart(self, slug):
        expect(self.page.locator(by_test_id(f"add-to-cart-{slug}"))).to_be_visible()
        return self

    @allure.step("断言购物车角标为：{count}")
    def expect_badge(self, count):
        expect(self.cart_badge).to_have_text(str(count))
        return self

    @allure.step("断言购物车角标消失")
    def expect_no_badge(self):
        expect(self.cart_badge).to_have_count(0)
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

    @allure.step("按名称 Z→A 排序")
    def sort_by_name_z_to_a(self):
        self.sort_select.select_option("za")
        return self

    @allure.step("断言商品价格按升序排列")
    def expect_prices_sorted_asc(self):
        assert_utils.assert_sorted(self.page, PRICE, mode="number", reverse=False, label="商品价格")
        return self

    @allure.step("断言商品价格按降序排列")
    def expect_prices_sorted_desc(self):
        assert_utils.assert_sorted(self.page, PRICE, mode="number", reverse=True, label="商品价格")
        return self

    @allure.step("断言商品名称按 A→Z 排列")
    def expect_names_sorted_asc(self):
        assert_utils.assert_sorted(self.page, NAME, mode="text", reverse=False, label="商品名称")
        return self

    @allure.step("读取商品价格列表")
    def price_list(self):
        return [float(text.replace("$", "")) for text in self.prices.all_inner_texts()]

    @allure.step("读取商品名称列表")
    def name_list(self):
        return self.names.all_inner_texts()

    @allure.step("打开商品详情：{name}")
    def open_product_detail(self, name):
        self.page.locator(NAME, has_text=name).first.click()
        detail = InventoryItemPage(self.page)
        # 只等 URL 变化不够：History 先变，React 后重渲染，此刻页面上还是列表
        detail.expect_loaded()
        return detail

    @allure.step("打开购物车")
    def open_cart(self):
        self.cart_link.click()
        # 等导航完成再返回，避免后续断言在旧页面上执行（UI 竞态）
        self.page.wait_for_url("**/cart.html")
        return CartPage(self.page)

    @allure.step("打开侧边菜单")
    def open_menu(self):
        self.page.click(MENU_BUTTON)
        # 菜单是离屏滑入的，元素在 DOM 里一直"可见"，必须等它真正进入视口
        expect(self.page.locator(by_test_id("logout-sidebar-link"))).to_be_in_viewport()
        return self

    @allure.step("登出")
    def logout(self):
        self.open_menu()
        self.page.click(by_test_id("logout-sidebar-link"))
        self.page.wait_for_selector(by_test_id("login-button"), state="visible")
        return LoginPage(self.page)

    @allure.step("重置应用状态（清空购物车）")
    def reset_app_state(self):
        self.open_menu()
        self.page.click(by_test_id("reset-sidebar-link"))
        return self
