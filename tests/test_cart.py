import allure
import pytest
from playwright.sync_api import expect

from pages.inventory_page import InventoryPage


@allure.feature("购物车")
@pytest.mark.cart
class TestCart:
    """购物车增删"""

    @allure.title("从购物车移除商品后角标消失")
    def test_remove_item(self, logged_in_page):
        cart = InventoryPage(logged_in_page).add_to_cart("sauce-labs-backpack").open_cart()
        cart.expect_item_count(1)

        cart.remove("sauce-labs-backpack")

        cart.expect_item_count(0)
        expect(logged_in_page.locator(".shopping_cart_badge")).to_have_count(0)
