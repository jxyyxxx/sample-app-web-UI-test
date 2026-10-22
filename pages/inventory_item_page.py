import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class InventoryItemPage(BasePage):
    """商品详情页：/inventory-item.html?id=xxx"""

    path = "/inventory-item.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.name = page.locator(by_test_id("inventory-item-name"))
        self.price = page.locator(by_test_id("inventory-item-price"))
        self.back_button = page.locator(by_test_id("back-to-products"))

    @allure.step("断言已进入商品详情页")
    def expect_loaded(self):
        # 用详情页独有的"返回商品列表"按钮做锚点：列表页同样有
        # data-test="inventory-item-name" 且一次渲染 6 个，用它等待会触发
        # strict mode 冲突，也判断不出路由是否真的切换完成
        expect(self.back_button).to_be_visible()
        return self

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
        # 延迟导入：列表页与详情页互相引用，模块级导入会形成循环
        from pages.inventory_page import InventoryPage

        return InventoryPage(self.page)
