import allure
import pytest

from pages.inventory_page import InventoryPage


@allure.feature("商品列表")
@pytest.mark.inventory
class TestInventory:
    """商品列表：加购计数、多商品加购、按价格排序"""

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
