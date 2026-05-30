import time
import pytest
from playwright.sync_api import expect
from pages.login_page import LoginPage
from pages.game_page import GamePage


# ---------------------------Helpers--------------------------------- #
def _unique(base: str) -> str:
    return f"{base}_{int(time.time() * 1000) % 100_000}"


# ---------------------------Auth form--------------------------------- #
@pytest.mark.auth
def test_auth_form_visible_on_load(login: LoginPage):
    """TC-AUTH-14: auth form is visible before login."""
    login.assert_visible(LoginPage.AUTH_FORM)
    login.assert_visible(LoginPage.INPUT_NAME)
    login.assert_visible(LoginPage.BTN_REGISTER)


# ---------------------------Register--------------------------------- #
@pytest.mark.critical
@pytest.mark.auth
def test_register_valid_user(login: LoginPage):
    """TC-AUTH-03: register with unique name auto-logs in and shows game screen."""
    username = _unique("reg_valid")
    login.register(username)
    login.assert_logged_in(username)
    login.assert_visible(GamePage.BOARD)
    login.assert_visible(LoginPage.NAV_PLAY)
    login.delete_account()

@pytest.mark.auth
@pytest.mark.parametrize(
    "invalid_name, expected_error",
    [
        ("", "Please enter a name"),
        ("A", "Name must be at least 2 characters"),
        ("   ", "Please enter a name"),
        ("a" * 101, "Name must be less than 100 characters"), # Base on the backend validation
    ],
)
def test_register_invalid_username(login: LoginPage, invalid_name: str, expected_error: str):
    """TC-AUTH-18: registration rejects empty, short, whitespace, and overlong names."""
    login.register(invalid_name)

    error_locator = login.get_auth_error_locator()
    expect(error_locator).to_be_visible()
    expect(error_locator).to_contain_text(expected_error)

    login.assert_logged_out()
    assert not login.get_by_testid(GamePage.BOARD).is_visible()


@pytest.mark.auth
def test_register_duplicate_name_shows_error(login: LoginPage):
    """TC-AUTH-04: duplicate registration shows error and blocks account creation."""
    username = _unique("dup_user")
    login.register(username)
    login.assert_logged_in(username)
    login.logout()
    login.fill(LoginPage.INPUT_NAME, username)
    login.click(LoginPage.BTN_REGISTER)
    login.assert_auth_error()


# ---------------------------Login--------------------------------- #
@pytest.mark.critical
@pytest.mark.auth
def test_login_valid_name(login: LoginPage):
    """TC-AUTH-01: existing user login reaches dashboard with board visible."""
    username = _unique("login_ok")
    login.register(username)
    login.logout()
    login.login(username)
    login.assert_logged_in(username)
    login.assert_visible(GamePage.BOARD)
    login.delete_account()

@pytest.mark.auth
@pytest.mark.parametrize(
    "invalid_name, expected_error",
    [
        ("", "Please enter a name"),
        ("A", "Name must be at least 2 characters"),
        ("invalid_user_xyz", "No account with this name"),
    ],
)
def test_login_invalid_username(login: LoginPage, invalid_name: str, expected_error: str):
    """TC-AUTH-02, TC-AUTH-09: login rejects invalid names including whitespace-only."""
    login.login(invalid_name)

    error_locator = login.get_auth_error_locator()
    expect(error_locator).to_be_visible()
    expect(error_locator).to_contain_text(expected_error)

    login.assert_logged_out()
    assert not login.get_by_testid(GamePage.BOARD).is_visible()


# ---------------------------Logout--------------------------------- #
@pytest.mark.critical
@pytest.mark.auth
def test_logout_returns_to_login_form(logged_in_login: LoginPage):
    """TC-AUTH-15: logout clears session and shows login form."""
    logged_in_login.assert_logged_in()
    logged_in_login.logout()
    logged_in_login.assert_logged_out()
    logged_in_login.assert_visible(LoginPage.AUTH_FORM)


# ---------------------------Profile--------------------------------- #
@pytest.mark.auth
def test_profile_panel_opens(logged_in_login: LoginPage):
    """TC-AUTH-16: profile panel opens from navigation after login."""
    logged_in_login.go_to_profile()
    logged_in_login.assert_visible(LoginPage.VIEW_PROFILE)
    logged_in_login.assert_visible(LoginPage.INPUT_PROFILE_NAME)


@pytest.mark.auth
def test_account_deletion_logs_out(logged_in_login: LoginPage):
    """TC-AUTH-08: delete account terminates session and returns to login."""
    logged_in_login.assert_logged_in()
    logged_in_login.delete_account()
    logged_in_login.assert_logged_out()


# ---------------------------Profile rename--------------------------------- #
@pytest.mark.auth
def test_username_available_after_profile_rename(login: LoginPage):
    """TC-AUTH-05, TC-AUTH-06: rename updates UI and releases old username for reuse."""
    original = _unique("release")
    renamed = _unique("renamed")
    login.register(original)
    login.assert_logged_in(original)
    login.update_display_name(renamed)
    login.assert_logged_in(renamed)
    login.logout()

    login.register(original)
    login.assert_logged_in(original)
    login.delete_account()


@pytest.mark.critical
@pytest.mark.auth
def test_profile_rename_to_taken_name_shows_error(login: LoginPage):
    """TC-AUTH-12: rename to taken username shows profile error and keeps current name."""
    taken = _unique("taken_name")
    other = _unique("other_user")
    login.register(taken)
    login.logout()
    login.register(other)
    login.go_to_profile()
    login.save_profile_name(taken)
    login.assert_profile_error("Another account already uses this name")
    login.assert_logged_in(other)
    login.delete_account()
    login.login(taken)
    login.delete_account()


@pytest.mark.critical
@pytest.mark.auth
def test_session_persists_after_page_reload(logged_in_login: LoginPage):
    """TC-AUTH-07, TC-AUTH-13: valid session survives page reload."""
    logged_in_login.assert_logged_in()
    logged_in_login.reload_session()
    logged_in_login.assert_logged_in()
    logged_in_login.assert_visible(LoginPage.NAV_PLAY)


@pytest.mark.critical
@pytest.mark.auth
@pytest.mark.parametrize(
    "session_name, users_payload",
    [
        pytest.param("orphan_user_xyz", None, id="orphan_session"),
        pytest.param("ghost_user", "{}", id="empty_users_registry"),
    ],
)
def test_invalid_session_storage_redirects_to_login(
    login: LoginPage,
    session_name: str,
    users_payload: str | None,
):
    """TC-AUTH-11: invalid or orphan session returns to login."""
    login.register(_unique("sess"))
    login.assert_logged_in()
    login.set_storage_item(LoginPage.STORAGE_SESSION, session_name)
    if users_payload is not None:
        login.set_storage_item(LoginPage.STORAGE_USERS, users_payload)
    login.reload_session()
    login.assert_logged_out()
    assert not login.get_by_testid(GamePage.BOARD).is_visible()


@pytest.mark.critical
@pytest.mark.auth
def test_concurrent_login_same_user_two_tabs(two_tabs):
    """TC-AUTH-10: same user can log in from two tabs sharing storage."""
    page_a, page_b = two_tabs
    login_a = LoginPage(page_a)
    login_b = LoginPage(page_b)
    username = _unique("conc")

    login_a.register(username)
    login_a.assert_logged_in(username)

    login_b.switch_to_login()
    login_b.login(username)
    login_b.assert_logged_in(username)

    login_a.delete_account()


# ---------------------------History--------------------------------- #
@pytest.mark.auth
def test_history_tab_accessible_after_login(logged_in_login: LoginPage):
    """TC-AUTH-17: history tab opens after login."""
    logged_in_login.assert_logged_in()
    logged_in_login.go_to_history()
    logged_in_login.assert_visible(LoginPage.VIEW_HISTORY)
