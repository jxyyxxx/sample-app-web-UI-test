import allure
from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页：/（用户名、密码、登录按钮、错误提示）"""

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.locator("#user-name")
        self.password_input = page.locator("#password")
        self.login_button = page.locator("#login-button")
        self.error_message = page.locator("[data-test='error']")

    @allure.step("登录：{username}")
    def login(self, username, password):
        self.open()
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        return self

    @allure.step("断言错误提示包含：{text}")
    def expect_error(self, text):
        expect(self.error_message).to_be_visible()
        expect(self.error_message).to_contain_text(text)
        return self
