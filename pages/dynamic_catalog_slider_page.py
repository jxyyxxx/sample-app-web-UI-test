import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class DynamicCatalogSliderPage(BasePage):
    """轮播目录页：/dynamic-catalog-slider.html

    每 2 秒自动切到下一件商品，点下方圆点可直接跳转。
    """

    path = "/dynamic-catalog-slider.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.container = page.locator(by_test_id("dynamic-catalog-slider-container"))
        self.item_name = page.locator(by_test_id("dynamic-catalog-slider-item-name"))
        self.item_price = page.locator(by_test_id("dynamic-catalog-slider-item-price"))

    def dot(self, index):
        return self.page.locator(by_test_id(f"dynamic-catalog-slider-dot-{index}"))

    @allure.step("断言已进入轮播目录页")
    def expect_loaded(self):
        expect(self.container).to_be_visible()
        expect(self.item_name).to_be_visible()
        return self

    @allure.step("断言共 {count} 个轮播圆点")
    def expect_dot_count(self, count):
        expect(self.dot(count - 1)).to_be_visible()
        expect(self.dot(count)).to_have_count(0)
        return self

    @allure.step("点击第 {index} 个圆点")
    def click_dot(self, index):
        self.dot(index).click()
        return self

    @allure.step("断言第 {index} 个圆点为选中态")
    def expect_active_dot(self, index):
        expect(self.dot(index)).to_have_attribute("aria-current", "true")
        return self

    @allure.step("读取圆点对应的商品名：{index}")
    def dot_product_name(self, index):
        """圆点的 aria-label 就是 'Show <商品名>'，用它推导期望值，避免硬编码商品数据"""
        label = self.dot(index).get_attribute("aria-label") or ""
        return label.replace("Show ", "", 1)

    @allure.step("读取当前展示的商品名")
    def current_item_name(self):
        return self.item_name.inner_text()

    @allure.step("断言当前展示商品名为：{name}")
    def expect_item_name(self, name):
        expect(self.item_name).to_have_text(name)
        return self

    @allure.step("断言轮播会自动切换到下一件商品")
    def expect_auto_advanced(self, previous_name):
        expect(self.item_name).not_to_have_text(previous_name, timeout=8000)
        return self
