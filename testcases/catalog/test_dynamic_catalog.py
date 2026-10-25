# ============================================================
# 用例层：动态目录模块
# 覆盖：滚动加载追加、卡片占位符转真实内容、loading 圈转网格、轮播手动切换与自动轮播
# ============================================================

import allure
import pytest

from pages.dynamic_catalog_lazy_load_page import DynamicCatalogLazyLoadPage
from pages.dynamic_catalog_slider_page import DynamicCatalogSliderPage
from pages.dynamic_catalog_spinner_page import DynamicCatalogSpinnerPage


@allure.feature("动态目录")
@pytest.mark.catalog
class TestDynamicCatalogLazyLoad:
    """滚动加载：首屏一批卡片，滚动到底部 sentinel 后追加"""

    @allure.title("滚动到底部后追加加载更多商品")
    def test_scroll_loads_more_items(self, logged_in_page):
        catalog = DynamicCatalogLazyLoadPage(logged_in_page).open().expect_loaded()
        catalog.expect_card_visible(0).expect_card_content_loaded(0)

        before = catalog.card_count()
        assert before > 0, "列表页没有渲染出任何商品卡片"

        catalog.scroll_to_sentinel()

        catalog.expect_more_cards_than(before)

    @allure.title("卡片进入视口后由占位符切换为真实内容")
    def test_card_content_loads_when_visible(self, logged_in_page):
        catalog = DynamicCatalogLazyLoadPage(logged_in_page).open().expect_loaded()
        catalog.expect_card_visible(0).expect_card_content_loaded(0)


@allure.feature("动态目录")
@pytest.mark.catalog
class TestDynamicCatalogSpinner:
    """加载态：先 loading 圈，随机延迟后出网格"""

    @allure.title("先出现 loading 圈，随后替换为商品网格")
    def test_spinner_replaced_by_grid(self, logged_in_page):
        catalog = DynamicCatalogSpinnerPage(logged_in_page).open()

        catalog.expect_loading().expect_grid_loaded().expect_item_visible(0)


@allure.feature("动态目录")
@pytest.mark.catalog
class TestDynamicCatalogSlider:
    """轮播：2 秒自动切换，点圆点可跳转"""

    @allure.title("点击圆点切换到对应商品")
    def test_click_dot_switches_item(self, logged_in_page):
        # 自动轮播每 2s 推进一次，会在点击与断言之间覆盖掉点击设置的下标，
        # 造成"点击其实生效了、断言却超时"的假红。冻结时间后再打开，定时器不触发。
        slider = (
            DynamicCatalogSliderPage(logged_in_page)
            .open_with_clock_frozen()
            .expect_loaded()
        )
        slider.expect_dot_count(6)

        slider.click_dot(2).expect_active_dot(2)
        slider.expect_item_name(slider.dot_product_name(2))

    @allure.title("每 2 秒自动轮播到下一件商品")
    def test_auto_advance_to_next_item(self, logged_in_page):
        slider = DynamicCatalogSliderPage(logged_in_page).open().expect_loaded()

        first = slider.current_item_name()
        slider.expect_auto_advanced(first)
