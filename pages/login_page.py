from playwright.sync_api import Page, expect
from .base_page import BasePage


class LoginPage(BasePage):
    # ---------------------------Variables--------------------------------- #
    AUTH_FORM       = "auth-form"
    INPUT_NAME      = "input-name"
    AUTH_ERROR      = "auth-error"
    BTN_REGISTER    = "btn-register"
    BTN_LOGIN       = "btn-login"
    BTN_SWITCH_MODE = "btn-switch-mode"

    HELLO_USER      = "hello-user"
    NAV_PLAY        = "nav-play"
    NAV_PROFILE     = "nav-profile"
    NAV_HISTORY     = "nav-history"
    BTN_LOGOUT      = "btn-logout"

    VIEW_PROFILE        = "view-profile"
    INPUT_PROFILE_NAME  = "input-profile-name"
    BTN_SAVE_PROFILE    = "btn-save-profile"
    PROFILE_ERROR       = "profile-error"
    PROFILE_WINS        = "profile-wins"
    PROFILE_LOSSES      = "profile-losses"
    PROFILE_DRAWS       = "profile-draws"
    BTN_DELETE_ACCOUNT  = "btn-delete-account"

    VIEW_HISTORY        = "view-history"
    HISTORY_TABLE       = "history-table"
    BTN_CLEAR_HISTORY   = "btn-clear-history"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---------------------------Actions--------------------------------- #
    def switch_to_login(self) -> None:
        self.click(self.BTN_SWITCH_MODE)

    def register(self, name: str) -> None:
        self.fill(self.INPUT_NAME, name)
        self.click(self.BTN_REGISTER)

    def login(self, name: str) -> None:
        if not self.get_by_testid(self.BTN_LOGIN).is_visible():
            self.switch_to_login()
        self.fill(self.INPUT_NAME, name)
        self.click(self.BTN_LOGIN)

    def logout(self) -> None:
        self.click(self.BTN_LOGOUT)

    def go_to_profile(self) -> None:
        self.click(self.NAV_PROFILE)

    def go_to_history(self) -> None:
        self.click(self.NAV_HISTORY)

    def go_to_play(self) -> None:
        self.click(self.NAV_PLAY)

    def update_display_name(self, new_name: str) -> None:
        self.go_to_profile()
        self.fill(self.INPUT_PROFILE_NAME, new_name)
        self.click(self.BTN_SAVE_PROFILE)

    def save_profile_name(self, new_name: str) -> None:
        self.fill(self.INPUT_PROFILE_NAME, new_name)
        self.click(self.BTN_SAVE_PROFILE)

    def delete_account(self) -> None:
        self.go_to_profile()
        self.page.once("dialog", lambda dialog: dialog.accept())
        self.click(self.BTN_DELETE_ACCOUNT)

    def reload_session(self) -> None:
        self.page.reload()
        self.page.wait_for_load_state("domcontentloaded")

    # ---------------------------Assertions--------------------------------- #
    def assert_logged_in(self, name: str = "") -> None:
        expect(self.get_by_testid(self.HELLO_USER)).to_be_visible()
        if name:
            expect(self.get_by_testid(self.HELLO_USER)).to_contain_text(name)

    def assert_logged_out(self) -> None:
        expect(self.get_by_testid(self.AUTH_FORM)).to_be_visible()

    def assert_auth_error(self, message: str = "") -> None:
        locator = self.get_auth_error_locator()
        expect(locator).to_be_visible()
        if message:
            expect(locator).to_contain_text(message)

    def assert_profile_error(self, message: str = "") -> None:
        locator = self.get_by_testid(self.PROFILE_ERROR)
        expect(locator).to_be_visible()
        if message:
            expect(locator).to_contain_text(message)

    def get_auth_error_locator(self):
        return self.get_by_testid(self.AUTH_ERROR)

    def get_history_row_count(self) -> int:
        self.go_to_history()
        rows = self.page.locator(
            f'[data-testid="{self.HISTORY_TABLE}"] tbody tr'
        )
        return rows.count()

    def get_history_row_texts(self) -> list[str]:
        self.go_to_history()
        rows = self.page.locator(
            f'[data-testid="{self.HISTORY_TABLE}"] tbody tr'
        )
        return [rows.nth(i).inner_text().strip() for i in range(rows.count())]
