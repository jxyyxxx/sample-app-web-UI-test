# ============================================================
# 用例层：购物车模块
# 覆盖：移除商品、角标消失、加购按钮状态恢复
# ============================================================

import allure
import pytest

from pages.inventory_page import InventoryPage


@allure.feature("购物车")
@pytest.mark.cart
class TestCart:
    """购物车增删"""

    @allure.title("从购物车移除商品后角标消失，回到列表按钮恢复为 Add to cart")
    def test_remove_item(self, logged_in_page):
        cart = InventoryPage(logged_in_page).add_to_cart("sauce-labs-backpack").open_cart()
        cart.expect_item_count(1)

        cart.remove("sauce-labs-backpack")

        cart.expect_item_count(0).expect_no_badge()

        # 回到列表页，加购按钮应从 Remove 恢复成 Add to cart
        cart.continue_shopping().expect_loaded().expect_not_in_cart("sauce-labs-backpack")
