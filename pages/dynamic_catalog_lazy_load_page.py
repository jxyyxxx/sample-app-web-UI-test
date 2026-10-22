import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage

CONTAINER = by_test_id("dynamic-catalog-lazy-load-container")
CARD = "lazy-load-item-{}"


class DynamicCatalogLazyLoadPage(BasePage):
    """滚动加载目录页：/dynamic-catalog-lazy-load.html

    卡片进入视口后才从占位符切换为真实内容；页尾 sentinel 进入视口时追加一批。
    注意：视口较高时 sentinel 首屏就可见，页面会立刻自动追加，因此不要断言"首屏恰好 6 张"。
    """

    path = "/dynamic-catalog-lazy-load.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.container = page.locator(CONTAINER)
        self.sentinel = page.locator(by_test_id("dynamic-catalog-lazy-load-sentinel"))

    @allure.step("断言已进入滚动加载目录页")
    def expect_loaded(self):
        expect(self.container).to_be_visible()
        return self

    def card(self, index):
        return self.page.locator(by_test_id(CARD.format(index)))

    @allure.step("读取当前已渲染的卡片数量")
    def card_count(self):
        # 容器的直接子节点就是卡片，用带 data-test 的直接子元素计数，不会把卡片内部节点算进来
        return self.page.locator(f"{CONTAINER} > [data-test]").count()

    @allure.step("断言第 {index} 张卡片已出现")
    def expect_card_visible(self, index):
        expect(self.card(index)).to_be_visible()
        return self

    @allure.step("断言第 {index} 张卡片内容已加载（占位符消失）")
    def expect_card_content_loaded(self, index):
        expect(self.page.locator(by_test_id(CARD.format(index) + "-name"))).to_be_visible()
        expect(self.page.locator(by_test_id(CARD.format(index) + "-placeholder"))).to_have_count(0)
        return self

    @allure.step("滚动到列表底部，触发加载更多")
    def scroll_to_sentinel(self):
        self.sentinel.scroll_into_view_if_needed()
        return self

    @allure.step("断言卡片数量多于 {count}（滚动后追加成功）")
    def expect_more_cards_than(self, count, timeout=5000):
        predicate = "([sel, minimum]) => document.querySelectorAll(sel + ' > [data-test]').length > minimum"
        try:
            self.page.wait_for_function(predicate, arg=[CONTAINER, count], timeout=timeout)
        except PlaywrightTimeoutError:
            raise AssertionError(
                f"滚动后没有加载更多商品：滚动前 {count} 张，滚动后仍是 {self.card_count()} 张"
            ) from None
        return self
