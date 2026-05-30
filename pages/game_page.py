from __future__ import annotations
from typing import Literal
from playwright.sync_api import Page, expect
from .base_page import BasePage

Difficulty = Literal["Easy", "Medium", "Hard"]


class GamePage(BasePage):
    # ---------------------------Variables--------------------------------- #
    TITLE            = "title"
    SELECT_LANGUAGE  = "select-language"
    BTN_THEME        = "btn-theme"
    SELECT_DIFFICULTY = "select-difficulty"
    STATUS  = "status" 
    BOARD   = "board"
    BTN_NEW   = "btn-new"    
    BTN_NEW_GAME = BTN_NEW   
    BTN_HINT  = "btn-hint"   
    BTN_RESET = "btn-reset"  
    NAV_PROFILE = "nav-profile"
    NAV_PLAY    = "nav-play"
    PROFILE_WINS    = "profile-wins"
    PROFILE_LOSSES  = "profile-losses"
    PROFILE_DRAWS   = "profile-draws"

    def __init__(self, page: Page) -> None:
        super().__init__(page)

    # ---------------------------Cell Locators and Actions--------------------------------- #
    def cell(self, index: int):
        return self.get_by_testid(f"cell-{index}")

    def click_cell(self, index: int) -> None:
        self.cell(index).click()

    def get_cell_state(self, index: int) -> str:
        return self.cell(index).get_attribute("data-state") or "empty"

    def get_board_state(self) -> list[str]:
        return [self.get_cell_state(i) for i in range(9)]

    def is_cell_empty(self, index: int) -> bool:
        return self.get_cell_state(index) == "empty"

    def is_cell_disabled(self, index: int) -> bool:
        return self.cell(index).is_disabled()

    def count_filled_cells(self) -> int:
        return sum(1 for i in range(9) if not self.is_cell_empty(i))

    def get_winning_cells(self) -> list[int]:
        winning = []
        for i in range(9):
            classes = self.cell(i).get_attribute("class") or ""
            if "is-win" in classes:
                winning.append(i)
        return winning

    def first_empty_cell(self) -> int | None:
        for i in range(9):
            if self.is_cell_empty(i):
                return i
        return None

    def find_cell_index_with_state(self, state: str) -> int | None:
        for i in range(9):
            if self.get_cell_state(i) == state:
                return i
        return None

    def get_hinted_cell_indices(self) -> list[int]:
        return [
            i
            for i in range(9)
            if "is-hint" in (self.cell(i).get_attribute("class") or "")
        ]

    def get_hinted_cell_index(self) -> int:
        hinted = self.get_hinted_cell_indices()
        assert len(hinted) == 1, f"Expected 1 hint cell, found {hinted}"
        return hinted[0]

    def assert_hint_cell_is_empty(self) -> int:
        i = self.get_hinted_cell_index()
        assert self.is_cell_empty(i), (
            f"Hint highlighted cell {i} but data-state is '{self.get_cell_state(i)}'"
        )
        return i

    def assert_hint_cell_empty_immediately(self) -> int:
        hinted = self.page.locator('[data-testid^="cell-"].is-hint').first
        hinted.wait_for(state="attached", timeout=1000)
        cell_text = hinted.inner_text().strip()
        assert cell_text == "", (
            f"Hint highlighted a cell with text {cell_text!r}"
        )
        testid = hinted.get_attribute("data-testid") or ""
        i = int(testid.replace("cell-", ""))
        state = hinted.get_attribute("data-state") or ""
        assert state == "empty", (
            f"Hint cell {i} has data-state={state!r}, expected 'empty'"
        )
        return i

    # ---------------------------Status Helpers--------------------------------- #
    def get_status_attr(self) -> str:
        return self.get_by_testid(self.STATUS).get_attribute("data-status") or ""

    def is_game_over(self) -> bool:
        return self.get_status_attr() in ("human", "computer", "draw")

    def count_marks(self, state: str) -> int:
        return sum(1 for i in range(9) if self.get_cell_state(i) == state)

    def play_until_game_over_easy(self, max_moves: int = 9) -> str:
        self.set_difficulty("easy")
        self.new_game()
        for _ in range(max_moves):
            if self.is_game_over():
                break
            for idx in range(9):
                if self.is_game_over():
                    break
                if not self.is_cell_disabled(idx):
                    self.click_cell(idx)
                    self.wait_for_computer()
                    break
        return self.get_status_attr()

    def wait_for_computer(self, timeout: int = 5000) -> None:
        self.page.wait_for_function(
            """() => {
                const s = document.querySelector('[data-testid="status"]');
                return s && s.getAttribute('data-status') !== 'computer-thinking';
            }""",
            timeout=timeout,
        )

    # ---------------------------Game Actions--------------------------------- #
    def set_difficulty(self, level: Difficulty) -> None:
        self.select_option(self.SELECT_DIFFICULTY, level)

    def change_difficulty_mid_game(
        self, level: Difficulty, *, accept_dialog: bool
    ) -> None:
        if accept_dialog:
            self.page.once("dialog", lambda dialog: dialog.accept())
        else:
            self.page.once("dialog", lambda dialog: dialog.dismiss())
        self.select_option(self.SELECT_DIFFICULTY, level)

    def get_selected_difficulty(self) -> str:
        return self.get_by_testid(self.SELECT_DIFFICULTY).input_value()

    def play_until_draw(self, max_turns: int = 20) -> None:
        from utils.board_strategy import best_draw_move

        self.set_difficulty("Hard")
        for _ in range(max_turns):
            if self.is_game_over():
                break
            move = best_draw_move(self.get_board_state())
            assert move is not None, "No legal move available"
            self.click_cell(move)
            self.wait_for_computer()

    def new_game(self) -> None:
        self.click(self.BTN_NEW)

    def request_hint(self, *, force: bool = False) -> None:
        self.get_by_testid(self.BTN_HINT).click(force=force)

    def reset_score(self) -> None:
        self.click(self.BTN_RESET)

    def get_score(self) -> dict[str, int]:
        self.click(self.NAV_PROFILE)

        def _read(testid: str) -> int:
            try:
                return int(self.get_by_testid(testid).inner_text().strip())
            except ValueError:
                return 0

        score = {
            "human": _read(self.PROFILE_WINS),
            "computer": _read(self.PROFILE_LOSSES),
            "draws": _read(self.PROFILE_DRAWS),
        }
        self.click(self.NAV_PLAY)
        return score

    def play_full_game(self) -> str:
        for _ in range(9):
            if self.is_game_over():
                break
            i = self.first_empty_cell()
            if i is None:
                break
            self.click_cell(i)
            self.wait_for_computer()
        return self.get_status_attr()

    # ---------------------------Settings--------------------------------- #
    def set_language(self, lang: Literal["en", "fa"]) -> None:
        self.select_option(self.SELECT_LANGUAGE, lang)

    def toggle_theme(self) -> None:
        self.click(self.BTN_THEME)

    def get_current_theme(self) -> str:
        return self.page.locator("html").get_attribute("data-theme") or ""

    def get_current_language(self) -> str:
        return self.page.locator("html").get_attribute("lang") or ""

    def get_current_dir(self) -> str:
        return self.page.locator("html").get_attribute("dir") or ""

    # ---------------------------Assertions--------------------------------- #
    def assert_board_empty(self) -> None:
        for i in range(9):
            assert self.is_cell_empty(i), f"Cell {i} should be empty"

    def assert_game_over(self) -> None:
        assert self.is_game_over(), (
            f"Expected game-over status, got '{self.get_status_attr()}'"
        )

    def assert_status_attr(self, expected: str) -> None:
        expect(self.get_by_testid(self.STATUS)).to_have_attribute(
            "data-status", expected
        )

    def assert_win_cells_highlighted(self) -> None:
        assert len(self.get_winning_cells()) == 3, (
            f"Expected 3 winning cells, got {self.get_winning_cells()}"
        )
