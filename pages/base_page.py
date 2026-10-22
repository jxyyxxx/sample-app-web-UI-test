import allure
from playwright.sync_api import Page, expect

from config.settings import BASE_URL


class BasePage:
    """所有页面对象的基类：统一放公共操作与页面路径约定

    子类通过 path 声明自己的路由，open() 不带参数时默认打开该路由。
    """

    path = "/"

    def __init__(self, page: Page):
        self.page = page

    def open(self, path=None):
        """打开页面：默认打开子类声明的 path，也可显式传入其他路由"""
        target = BASE_URL + (self.path if path is None else path)
        with allure.step(f"打开页面：{target}"):
            self.page.goto(target)
        return self

    def expect_url(self, pattern):
        expect(self.page).to_have_url(pattern)
        return self
