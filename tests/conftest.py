import base64
import os
import re
import pytest
from datetime import datetime
from pathlib import Path
from playwright.sync_api import Page
from pytest_html import extras as html_extras

from pages.game_page import GamePage
from pages.login_page import LoginPage

_INDEX = Path(__file__).resolve().parent.parent.parent / "index.html"
URL = os.environ.get("URL", _INDEX.as_uri())

GUEST_NAME = "AutoTester"

# ---------------------------Browser--------------------------------- #
@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 800},
        "locale": "en-US",
    }

# ---------------------------Page Fixtures--------------------------------- #
@pytest.fixture()
def page(page: Page) -> Page:
    page.set_default_timeout(5000)
    page.set_default_navigation_timeout(20000)
    page.goto(URL)
    page.wait_for_load_state("domcontentloaded")
    return page

@pytest.fixture()
def game(page: Page) -> GamePage:
    return GamePage(page)

@pytest.fixture()
def login(page: Page) -> LoginPage:
    return LoginPage(page)

# ---------------------------Logged In Fixtures--------------------------------- #
@pytest.fixture()
def logged_in_game(game: GamePage) -> GamePage:
    login = LoginPage(game.page)
    login.register(GUEST_NAME)
    yield game
    try:
        login.logout()
    except Exception:
        pass

def _delete_guest_account(login: LoginPage) -> None:
    try:
        login.delete_account()
    except Exception:
        try:
            if login.get_by_testid(LoginPage.AUTH_FORM).is_visible():
                login.login(GUEST_NAME)
            login.delete_account()
        except Exception:
            pass

@pytest.fixture()
def logged_in_login(login: LoginPage) -> LoginPage:
    login.register(GUEST_NAME)
    yield login
    _delete_guest_account(login)


@pytest.fixture()
def shared_browser_context(browser, browser_context_args):
    context = browser.new_context(**browser_context_args)
    yield context
    context.close()


@pytest.fixture()
def two_tabs(shared_browser_context):
    """Two pages sharing localStorage (same browser context)."""
    pages = []
    for _ in range(2):
        page = shared_browser_context.new_page()
        page.set_default_timeout(5000)
        page.set_default_navigation_timeout(20000)
        page.goto(URL)
        page.wait_for_load_state("domcontentloaded")
        pages.append(page)
    yield tuple(pages)

# ---------------------------Report--------------------------------- #
def _resolve_page(item) -> Page | None:
    for name in ("page", "game", "login", "logged_in_game", "logged_in_login"):
        fixture = item.funcargs.get(name)
        if fixture is None:
            continue
        if isinstance(fixture, Page):
            return fixture
        if hasattr(fixture, "page"):
            return fixture.page
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    report.extras = getattr(report, "extras", [])

    if report.when != "call" or not report.failed:
        return

    page = _resolve_page(item)
    if page is None:
        return

    try:
        screenshot = page.screenshot(full_page=True)
        screenshot_b64 = base64.b64encode(screenshot).decode("ascii")
        report.extras.append(
            html_extras.html(
                '<div><img alt="failure screenshot" '
                'style="max-width:100%; border:1px solid #ccc" '
                f'src="data:image/png;base64,{screenshot_b64}" /></div>'
            )
        )
    except Exception as exc:
        report.extras.append(html_extras.text(f"Screenshot failed: {exc}"))


def _report_label(config) -> str:
    markexpr = (getattr(config.option, "markexpr", None) or "").strip()
    if markexpr:
        slug = re.sub(r"[^\w]+", "_", markexpr).strip("_")
        return slug[:80] if slug else "marked"

    file_tags: list[str] = []
    for arg in config.args:
        name = Path(str(arg)).name.lower()
        if "test_auth" in name:
            file_tags.append("auth")
        elif "test_game" in name:
            file_tags.append("game")
        elif "test_settings" in name:
            file_tags.append("settings")
    if file_tags:
        return "_".join(dict.fromkeys(file_tags))

    return "all"


def pytest_configure(config):
    reports_dir = Path(__file__).resolve().parent.parent / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    label = _report_label(config)
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = reports_dir / f"report_{label}_{current_time}.html"
    config.option.htmlpath = str(report_path)