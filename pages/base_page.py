import os
from playwright.sync_api import Page, Locator, expect
from pathlib import Path

class BasePage:
    STORAGE_SESSION = "ttt:session"
    STORAGE_USERS = "ttt:users"
    STORAGE_LANG = "ttt:lang"
    STORAGE_THEME = "ttt:theme"

    def __init__(self, page: Page) -> None:
        self.page = page
        self.project_root = Path(__file__).resolve().parent.parent
        self.default_path = f"file:///{self.project_root}/index.html"

    # ---------------------------Locators and Actions--------------------------------- #
    def get_by_testid(self, testid: str) -> Locator:
        return self.page.get_by_test_id(testid)

    def click(self, testid: str) -> None:
        self.get_by_testid(testid).click()

    def fill(self, testid: str, value: str) -> None:
        self.get_by_testid(testid).fill(value)

    def select_option(self, testid: str, value: str) -> None:
        self.get_by_testid(testid).select_option(value)

    def inner_text(self, testid: str) -> str:
        return self.get_by_testid(testid).inner_text()

    def is_visible(self, testid: str) -> bool:
        return self.get_by_testid(testid).is_visible()

    def set_storage_item(self, key: str, value: str) -> None:
        self.page.evaluate(
            "([k, v]) => localStorage.setItem(k, v)",
            [key, value],
        )

    # ---------------------------Assertions--------------------------------- #
    def assert_visible(self, testid: str) -> None:
        expect(self.get_by_testid(testid)).to_be_visible()

    def assert_contains_text(self, testid: str, text: str) -> None:
        expect(self.get_by_testid(testid)).to_contain_text(text)
