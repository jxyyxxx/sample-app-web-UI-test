import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class DynamicCatalogSpinnerPage(BasePage):
    """加载态目录页：/dynamic-catalog-spinner.html

    进入后先显示 loading 圈，随机 0.5~3 秒后替换为商品网格。
    """

    path = "/dynamic-catalog-spinner.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.container = page.locator(by_test_id("dynamic-catalog-spinner-container"))
        self.spinner = page.locator(by_test_id("dynamic-catalog-spinner"))
        self.grid = page.locator(by_test_id("dynamic-catalog-spinner-grid"))

    @allure.step("断言 loading 圈可见")
    def expect_loading(self):
        expect(self.spinner).to_be_visible(timeout=3000)
        return self

    @allure.step("断言商品网格已加载完成")
    def expect_grid_loaded(self):
        # 应用侧随机延迟最大 3 秒，这里留足余量
        expect(self.grid).to_be_visible(timeout=10000)
        expect(self.spinner).to_have_count(0)
        return self

    def item(self, index):
        return self.page.locator(by_test_id(f"spinner-item-{index}"))

    @allure.step("断言网格中有第 {index} 个商品")
    def expect_item_visible(self, index):
        expect(self.item(index)).to_be_visible()
        return self

    @allure.step("读取商品名称：{index}")
    def item_name(self, index):
        return self.page.locator(by_test_id(f"spinner-item-{index}-name")).inner_text()
