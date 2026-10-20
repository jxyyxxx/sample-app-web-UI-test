import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class CheckoutPage(BasePage):
    """结算页：/checkout-step-one.html 与 /checkout-step-two.html"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.first_name = page.locator("#first-name")
        self.last_name = page.locator("#last-name")
        self.postal_code = page.locator("#postal-code")
        self.continue_button = page.locator("[data-test='continue']")
        self.finish_button = page.locator("[data-test='finish']")
        self.complete_header = page.locator(".complete-header")
        self.error_message = page.locator("[data-test='error']")

    @allure.step("填写收货信息：{first} {last} / {zip_code}")
    def fill_info(self, first, last, zip_code):
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(zip_code)
        return self

    @allure.step("继续进入订单概览")
    def continue_to_overview(self):
        self.continue_button.click()
        return self

    @allure.step("提交订单")
    def finish_order(self):
        self.finish_button.click()
        return self

    @allure.step("断言已进入订单概览")
    def expect_overview(self):
        expect(self.page.locator(".summary_subtotal_label")).to_be_visible()
        return self

    @allure.step("读取订单商品总额（数值）")
    def subtotal(self):
        text = self.page.locator(".summary_subtotal_label").inner_text()
        return float(text.split("$")[1])

    @allure.step("断言下单完成")
    def expect_complete(self):
        expect(self.complete_header).to_contain_text("Thank you for your order")
        return self

    @allure.step("断言结算错误提示包含：{text}")
    def expect_error(self, text):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(text)
        return self
