import allure
from playwright.sync_api import Page, expect

from common.config import BASE_URL


class BasePage:
    """所有页面对象的基类：统一放公共操作"""

    def __init__(self, page: Page):
        self.page = page

    @allure.step("打开页面：{path}")
    def open(self, path=""):
        self.page.goto(BASE_URL + path)
        return self

    def expect_url(self, pattern):
        expect(self.page).to_have_url(pattern)
        return self
