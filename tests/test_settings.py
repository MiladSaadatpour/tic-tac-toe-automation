import pytest
from playwright.sync_api import Page
from pages.game_page import GamePage
from pages.login_page import LoginPage


# ---------------------------Language--------------------------------- #
@pytest.mark.settings
def test_default_language_is_english(game: GamePage):
    """TC-SET-05: default language is English with LTR direction."""
    assert game.get_current_language() == "en"
    assert game.get_current_dir() == "ltr"


@pytest.mark.settings
def test_switch_to_persian(game: GamePage):
    """TC-SET-06: switching to Persian sets lang=fa and dir=rtl."""
    game.set_language("fa")
    assert game.get_current_language() == "fa"
    assert game.get_current_dir() == "rtl"


@pytest.mark.settings
def test_switch_back_to_english(game: GamePage):
    """TC-SET-07: user can switch back from Persian to English."""
    game.set_language("fa")
    game.set_language("en")
    assert game.get_current_language() == "en"
    assert game.get_current_dir() == "ltr"


@pytest.mark.settings
def test_language_selector_has_two_options(game: GamePage):
    """TC-SET-08: language dropdown offers exactly en and fa."""
    options = game.page.locator(
        f"[data-testid='{GamePage.SELECT_LANGUAGE}'] option"
    ).all()
    values = [o.get_attribute("value") for o in options]
    assert set(values) == {"en", "fa"}, f"Unexpected options: {values}"


@pytest.mark.settings
def test_language_persists_after_new_game(logged_in_game: GamePage):
    """TC-SET-01: language persists after New Game."""
    logged_in_game.set_language("fa")
    logged_in_game.click_cell(4)
    logged_in_game.wait_for_computer()
    logged_in_game.new_game()
    assert logged_in_game.get_current_language() == "fa"
    assert logged_in_game.get_current_dir() == "rtl"
    logged_in_game.assert_board_empty()


# ---------------------------Theme--------------------------------- #
@pytest.mark.settings
def test_default_theme_is_light(game: GamePage):
    """TC-SET-05: default theme is light on first load."""
    assert game.get_current_theme() == "light"


@pytest.mark.settings
def test_toggle_to_dark_theme(game: GamePage):
    """TC-SET-09: theme toggle switches to dark mode."""
    game.toggle_theme()
    assert game.get_current_theme() == "dark"


@pytest.mark.settings
def test_toggle_back_to_light_theme(game: GamePage):
    """TC-SET-10: theme toggle returns to light mode."""
    game.toggle_theme()
    game.toggle_theme()
    assert game.get_current_theme() == "light"


@pytest.mark.settings
def test_theme_button_label_dark(game: GamePage):
    """TC-SET-11: theme button shows Dark label in light mode."""
    from playwright.sync_api import expect
    expect(game.get_by_testid(GamePage.BTN_THEME)).to_contain_text("Dark")


@pytest.mark.settings
def test_theme_button_label_light(game: GamePage):
    """TC-SET-11: theme button shows Light label in dark mode."""
    from playwright.sync_api import expect
    game.toggle_theme()
    expect(game.get_by_testid(GamePage.BTN_THEME)).to_contain_text("Light")


@pytest.mark.settings
def test_theme_persists_after_reload(game: GamePage, page: Page):
    """TC-SET-02: dark theme persists after page reload."""
    game.toggle_theme()
    assert game.get_current_theme() == "dark"
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    assert game.get_current_theme() == "dark"


@pytest.mark.settings
def test_language_persists_after_reload(game: GamePage, page: Page):
    """TC-SET-12: Persian language persists after page reload."""
    game.set_language("fa")
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    assert game.get_current_language() == "fa"


# ---------------------------Critical — storage (TC-SET-03/04)--------------------------------- #
@pytest.mark.critical
@pytest.mark.settings
@pytest.mark.parametrize(
    "session_value, users_value",
    [
        pytest.param("broken", "not-json", id="corrupt_storage_on_load"),
    ],
)
def test_invalid_session_storage_shows_login(
    page: Page, session_value: str, users_value: str
):
    """TC-AUTH-11, TC-SET-03: corrupt localStorage on cold load shows login safely."""
    login = LoginPage(page)
    login.set_storage_item(LoginPage.STORAGE_SESSION, session_value)
    login.set_storage_item(LoginPage.STORAGE_USERS, users_value)
    page.reload()
    page.wait_for_load_state("domcontentloaded")
    login.assert_logged_out()
    assert not login.get_by_testid(GamePage.BOARD).is_visible()


@pytest.mark.critical
@pytest.mark.settings
def test_settings_sync_to_second_tab_after_reload(two_tabs):
    """TC-SET-04: language/theme written in tab A apply in tab B after reload."""
    page_a, page_b = two_tabs
    game_a = GamePage(page_a)
    game_b = GamePage(page_b)

    game_a.set_language("fa")
    game_a.toggle_theme()

    page_b.reload()
    page_b.wait_for_load_state("domcontentloaded")

    assert game_b.get_current_language() == "fa"
    assert game_b.get_current_dir() == "rtl"
    assert game_b.get_current_theme() == "dark"
