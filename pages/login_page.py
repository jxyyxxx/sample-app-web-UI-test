import allure
from playwright.sync_api import Page, expect

from common.locator_utils import by_test_id
from pages.base_page import BasePage


class LoginPage(BasePage):
    """登录页：/（用户名、密码、登录按钮、错误提示）"""

    path = "/"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.locator(by_test_id("username"))
        self.password_input = page.locator(by_test_id("password"))
        self.login_button = page.locator(by_test_id("login-button"))
        self.error_message = page.locator(by_test_id("error"))

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

    @allure.step("断言登录态 cookie 已写入：{username}")
    def expect_session_cookie(self, username):
        """登录态真正的载体是 cookie session-username，只断言跳转成功不够"""
        cookies = {cookie["name"]: cookie["value"] for cookie in self.page.context.cookies()}
        actual = cookies.get("session-username")
        assert actual == username, f"登录态 cookie 不正确：期望 {username}，实际 {actual}"
        return self
