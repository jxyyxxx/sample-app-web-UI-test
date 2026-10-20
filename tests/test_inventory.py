import allure
import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage


@allure.feature("商品列表")
@pytest.mark.inventory
class TestInventory:
    """商品列表：加购计数、多商品加购、排序（价格双向/名称）、详情页、重置状态"""

    @allure.title("加入一件商品后角标为 1")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    def test_add_single_item(self, logged_in_page):
        InventoryPage(logged_in_page).expect_loaded().add_to_cart(
            "sauce-labs-backpack"
        ).expect_badge(1)

    @allure.title("加入两件商品后角标为 2，购物车有 2 行")
    def test_add_two_items(self, logged_in_page):
        inventory = InventoryPage(logged_in_page).add_to_cart(
            "sauce-labs-backpack"
        ).add_to_cart("sauce-labs-bike-light")

        inventory.expect_badge(2)
        cart = inventory.open_cart()
        cart.expect_item_count(2)

    @allure.title("按价格从低到高排序生效")
    def test_sort_price_low_to_high(self, logged_in_page):
        prices = (
            InventoryPage(logged_in_page)
            .sort_by_price_low_to_high()
            .price_list()
        )
        assert prices == sorted(prices), f"价格未按升序排列：{prices}"

    @allure.title("按价格从高到低排序生效")
    def test_sort_price_high_to_low(self, logged_in_page):
        prices = (
            InventoryPage(logged_in_page)
            .sort_by_price_high_to_low()
            .price_list()
        )
        assert prices == sorted(prices, reverse=True), f"价格未按降序排列：{prices}"

    @allure.title("按名称 A→Z 排序生效")
    def test_sort_name_a_to_z(self, logged_in_page):
        names = (
            InventoryPage(logged_in_page)
            .sort_by_name_a_to_z()
            .name_list()
        )
        assert names == sorted(names), f"名称未按升序排列：{names}"

    @allure.title("商品详情页的名称与价格和列表一致")
    def test_product_detail_matches_list(self, logged_in_page):
        inventory = InventoryPage(logged_in_page).expect_loaded()

        name = inventory.name_list()[0]
        price = inventory.price_list()[0]

        detail = inventory.open_product_detail(name)
        detail.expect_name(name)
        assert detail.price_text() == f"${price:.2f}", "详情页价格与列表不一致"

        detail.back_to_list().expect_loaded()

    @allure.title("重置 App State 后购物车被清空")
    def test_reset_app_state_clears_cart(self, logged_in_page):
        inventory = InventoryPage(logged_in_page).add_to_cart(
            "sauce-labs-backpack"
        ).add_to_cart("sauce-labs-bike-light")
        inventory.expect_badge(2)

        inventory.reset_app_state()

        expect(logged_in_page.locator(".shopping_cart_badge")).to_have_count(0)
