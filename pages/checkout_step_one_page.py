import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage
from pages.checkout_step_two_page import CheckoutStepTwoPage


class CheckoutStepOnePage(BasePage):
    """结算第一步：/checkout-step-one.html（收货信息、必填校验）"""

    path = "/checkout-step-one.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.first_name = page.locator(by_test_id("firstName"))
        self.last_name = page.locator(by_test_id("lastName"))
        self.postal_code = page.locator(by_test_id("postalCode"))
        self.continue_button = page.locator(by_test_id("continue"))
        self.error_message = page.locator(by_test_id("error"))

    @allure.step("填写收货信息：{first} {last} / {zip_code}")
    def fill_info(self, first, last, zip_code):
        self.first_name.fill(first)
        self.last_name.fill(last)
        self.postal_code.fill(zip_code)
        return self

    @allure.step("提交收货信息")
    def submit(self):
        """点击 Continue。校验通过才跳转，不通过仍停留本页，因此统一返回自身；
        是否真的进入下一页由 expect_overview() 断言决定。
        """
        self.continue_button.click()
        return self

    @allure.step("断言进入订单概览页")
    def expect_overview(self):
        self.page.wait_for_url("**/checkout-step-two.html")
        return CheckoutStepTwoPage(self.page)

    @allure.step("断言结算错误提示包含：{text}")
    def expect_error(self, text):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(text)
        return self
