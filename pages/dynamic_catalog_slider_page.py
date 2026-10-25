import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage

# 假时钟参数：起点取固定值保证可重复；暂停点跳到 1 分钟后，
# 此时页面还没加载，不会有定时器被这次跳转误触发
_CLOCK_START_MS = 0
_CLOCK_PAUSE_MS = 60_000


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

    @allure.step("打开页面并冻结时间（关闭自动轮播干扰）")
    def open_with_clock_frozen(self):
        """冻结页面时间后再打开，自动轮播的 setInterval 不会触发

        轮播每 2s 推进一次 activeIndex，会覆盖点击圆点设置的值：
        只要一次 tick 落在"点击生效"和"断言首次轮询"之间，圆点就一直是
        false，要等 12s（6 个商品 × 2s）才轮转回来——断言 5s 超时必然失败。
        冻结时间后 activeIndex 只由点击决定，结果才可稳定复现。
        """
        self.page.clock.install(time=_CLOCK_START_MS)
        self.page.clock.pause_at(_CLOCK_PAUSE_MS)
        return self.open()

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
