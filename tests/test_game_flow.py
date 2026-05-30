"""
Tests for the core game flow.

Covers board play, win/draw, score, hint, difficulty, and critical edge cases.
"""
import time
import pytest
import random
from pages.game_page import GamePage
from pages.login_page import LoginPage
from playwright.sync_api import expect

# ---------------------------App load--------------------------------- #
def test_page_title_visible(game: GamePage):
    """TC-GAME-16: app title is visible on load."""
    game.assert_visible(GamePage.TITLE)
    game.assert_contains_text(GamePage.TITLE, "Tic-Tac-Toe")


def test_board_renders_nine_cells(logged_in_game: GamePage):
    """TC-GAME-17: nine empty cells render after login."""
    for i in range(9):
        assert logged_in_game.cell(i).is_visible(), f"Cell {i} not visible"
    logged_in_game.assert_board_empty()


def test_status_visible_on_load(logged_in_game: GamePage):
    """TC-GAME-18: status bar is visible on the play view."""
    logged_in_game.assert_visible(GamePage.STATUS)


# ---------------------------Human Move--------------------------------- #
@pytest.mark.critical
@pytest.mark.game
def test_human_can_place_mark(logged_in_game: GamePage):
    """TC-GAME-01, TC-GAME-19: human click places X on the board."""
    logged_in_game.click_cell(4)
    assert logged_in_game.get_cell_state(4) == "x"


@pytest.mark.critical
@pytest.mark.game
def test_computer_responds_after_human_move(logged_in_game: GamePage):
    """TC-GAME-02, TC-GAME-11, TC-GAME-15, TC-GAME-20: AI responds, locks input, returns turn in time."""
    start = time.perf_counter()
    logged_in_game.click_cell(4)
    logged_in_game.page.wait_for_function(
        """() => {
            const s = document.querySelector('[data-testid="status"]');
            return s && s.getAttribute('data-status') === 'computer-thinking';
        }""",
        timeout=3000,
    )
    for i in range(9):
        if logged_in_game.is_cell_empty(i):
            expect(logged_in_game.cell(i)).to_be_disabled()
    logged_in_game.wait_for_computer(timeout=5000)
    elapsed = time.perf_counter() - start
    assert elapsed < 5.0
    assert logged_in_game.count_marks("x") == 1
    assert logged_in_game.find_cell_index_with_state("o") is not None
    assert logged_in_game.get_status_attr() == "your-turn"


@pytest.mark.game
def test_clicked_cell_becomes_disabled(logged_in_game: GamePage):
    """TC-GAME-06, TC-GAME-21: played cell is disabled after the move."""
    logged_in_game.click_cell(0)
    logged_in_game.wait_for_computer()
    assert logged_in_game.is_cell_disabled(0), "Played cell should be disabled"


# ---------------------------Win and Draw--------------------------------- #
@pytest.mark.critical
@pytest.mark.game
def test_human_win_highlights_cells(logged_in_game: GamePage):
    """TC-GAME-03, TC-GAME-12, TC-GAME-14: win highlights cells and locks the board."""
    logged_in_game.set_difficulty("easy")
    logged_in_game.new_game()

    # Play until win or give up after 5 human moves
    won = False
    for _ in range(5):
        for i in range(9):
            if not logged_in_game.is_cell_disabled(i):
                logged_in_game.click_cell(i)
                logged_in_game.wait_for_computer()
                status = logged_in_game.get_status_attr()
                if status == "human":
                    won = True
                    break
                if status in ("computer", "draw"):
                    break
        if won or logged_in_game.get_status_attr() in ("computer", "draw"):
            break

    if won:
        logged_in_game.assert_status_attr("human")
        logged_in_game.assert_win_cells_highlighted()
        for i in range(9):
            assert logged_in_game.is_cell_disabled(i)
    else:
        pytest.skip("Human did not win in this run — non-deterministic AI")


@pytest.mark.critical
@pytest.mark.game
def test_draw_game_updates_status_and_score(logged_in_game: GamePage):
    """TC-GAME-04, TC-GAME-23: draw ends game and increments profile draw counter."""
    score_before = logged_in_game.get_score()
    logged_in_game.play_until_draw()
    logged_in_game.assert_status_attr("draw")
    logged_in_game.assert_game_over()
    for i in range(9):
        assert not logged_in_game.is_cell_empty(i), f"Cell {i} should be filled on draw"

    score_after = logged_in_game.get_score()
    assert score_after["draws"] == score_before["draws"] + 1


@pytest.mark.game
def test_win_increments_human_score(logged_in_game: GamePage):
    """TC-GAME-22: human win increments profile win counter."""
    score_before = logged_in_game.get_score()
    logged_in_game.set_difficulty("easy")
    logged_in_game.new_game()

    won = False
    for _ in range(5):
        for i in range(9):
            if logged_in_game.is_game_over():
                break
            if not logged_in_game.is_cell_disabled(i):
                logged_in_game.click_cell(i)
                logged_in_game.wait_for_computer()
                if logged_in_game.get_status_attr() == "human":
                    won = True
                    break
        if won or logged_in_game.is_game_over():
            break

    if not won:
        pytest.skip("Human did not win in this run — non-deterministic AI")

    score_after = logged_in_game.get_score()
    assert score_after["human"] == score_before["human"] + 1


@pytest.mark.critical
@pytest.mark.game
def test_history_logs_completed_match(logged_in_game: GamePage):
    """TC-GAME-08, TC-HIST-01, TC-HIST-02: each finished match adds one history row."""
    login = LoginPage(logged_in_game.page)
    rows_before = login.get_history_row_count()
    login.go_to_play()

    outcome_one = logged_in_game.play_until_game_over_easy()
    outcome_two = logged_in_game.play_until_game_over_easy()

    rows_after = login.get_history_row_count()
    assert rows_after == rows_before + 2

    texts = login.get_history_row_texts()
    for outcome, row in zip((outcome_one, outcome_two), texts[-2:]):
        row_lower = row.lower()
        if outcome == "human":
            assert "win" in row_lower
        elif outcome == "computer":
            assert "loss" in row_lower
        else:
            assert "draw" in row_lower


@pytest.mark.game
def test_game_over_all_cells_disabled(logged_in_game: GamePage):
    """TC-GAME-07, TC-GAME-14: all cells disabled after game over."""
    logged_in_game.set_difficulty("easy")
    logged_in_game.new_game()

    # Play until game over
    for _ in range(9):
        status = logged_in_game.get_status_attr()
        if status in ("human", "computer", "draw"):
            break
        for i in range(9):
            if not logged_in_game.is_cell_disabled(i):
                logged_in_game.click_cell(i)
                logged_in_game.wait_for_computer()
                break

    logged_in_game.assert_game_over()
    for i in range(9):
        assert logged_in_game.is_cell_disabled(i), (
            f"Cell {i} should be disabled after game over"
        )


# ---------------------------New Game--------------------------------- #
@pytest.mark.critical
@pytest.mark.game
def test_new_game_resets_board(logged_in_game: GamePage):
    """TC-GAME-05: New Game clears the board."""
    logged_in_game.click_cell(4)
    logged_in_game.wait_for_computer()
    logged_in_game.new_game()
    logged_in_game.assert_board_empty()


@pytest.mark.game
def test_new_game_button_visible(logged_in_game: GamePage):
    """TC-GAME-24: New Game button is visible on the play view."""
    logged_in_game.assert_visible(GamePage.BTN_NEW_GAME)


# ---------------------------Score--------------------------------- #
@pytest.mark.game
def test_score_starts_at_zero(logged_in_game: GamePage):
    """TC-GAME-25: profile wins, losses, and draws start at zero."""
    score = logged_in_game.get_score()
    assert score["human"] == 0
    assert score["computer"] == 0
    assert score["draws"] == 0


@pytest.mark.game
def test_reset_clears_board_but_not_profile_stats(logged_in_game: GamePage):
    """TC-GAME-26, TC-HIST-03: reset clears board but keeps profile stats and history."""
    logged_in_game.set_difficulty("easy")
    logged_in_game.new_game()
    for idx in range(9):
        if logged_in_game.is_game_over():
            break
        if not logged_in_game.is_cell_disabled(idx):
            logged_in_game.click_cell(idx)
            logged_in_game.wait_for_computer()

    score_before = logged_in_game.get_score()
    total_before = score_before["human"] + score_before["computer"] + score_before["draws"]
    assert total_before >= 1, "Need a finished game before testing reset"

    login = LoginPage(logged_in_game.page)
    history_rows_before = login.get_history_row_count()
    assert history_rows_before >= 1
    login.go_to_play()

    logged_in_game.new_game()
    logged_in_game.click_cell(4)
    logged_in_game.wait_for_computer()
    assert logged_in_game.count_filled_cells() >= 2

    logged_in_game.reset_score()
    logged_in_game.assert_board_empty()

    score_after = logged_in_game.get_score()
    assert score_after == score_before
    assert login.get_history_row_count() == history_rows_before


@pytest.mark.critical
@pytest.mark.game
def test_reset_during_computer_thinking_clears_board(logged_in_game: GamePage):
    """TC-GAME-13: reset cancels an in-flight AI turn."""
    logged_in_game.click_cell(0)
    logged_in_game.get_by_testid(GamePage.STATUS).wait_for(state="attached", timeout=2000)
    logged_in_game.reset_score()
    logged_in_game.assert_board_empty()
    assert logged_in_game.get_status_attr() == "your-turn"


# ---------------------------Hint--------------------------------- #
@pytest.mark.game
def test_hint_highlights_a_cell(logged_in_game: GamePage):
    """TC-GAME-27: hint highlights an empty cell."""
    logged_in_game.request_hint()
    logged_in_game.assert_hint_cell_is_empty()

# ---------------------------Bug Hunting (logical bugs)--------------------------------- #
@pytest.mark.bug_hunting
@pytest.mark.game
def test_reproduce_ai_overwrite_bug_by_tracking_move(logged_in_game: GamePage):
    """TC-GAME-29: document Hard AI overwrite on replayed cell (known defect)."""
    game = logged_in_game
    game.set_difficulty("hard")
    game.assert_visible(GamePage.BOARD)

    game.click_cell(0)
    game.wait_for_computer()

    ai_chosen_i = game.find_cell_index_with_state("o")
    assert ai_chosen_i is not None, "Computer did not place a mark in round 1"

    game.new_game()
    game.assert_board_empty()

    game.click_cell(ai_chosen_i)
    game.wait_for_computer()

    final_state = game.get_cell_state(ai_chosen_i)
    assert final_state == "x", (
        f"Hard AI overwrote human on cell {ai_chosen_i}: "
        f"expected data-state 'x', got '{final_state}'"
    )

# This bug is so flicky that it's hard to reproduce, you should try more than once to see if it happens.
@pytest.mark.game
@pytest.mark.bug_hunting
def test_hint_always_suggests_empty_cell_until_game_over(logged_in_game: GamePage):
    """TC-GAME-09, TC-GAME-28: hint and AI only target empty cells during play."""
    game = logged_in_game
    difficulty = random.choice(['medium', 'hard'])
    game.set_difficulty(difficulty)
    game.assert_visible(GamePage.BOARD)

    hint_checks = 0
    max_iterations = 30

    for _ in range(max_iterations):
        if game.is_game_over():
            break

        if game.get_by_testid(GamePage.BTN_HINT).is_enabled():
            game.request_hint(force=True)
            hinted_i = game.assert_hint_cell_empty_immediately()
            game.click_cell(hinted_i)
            game.wait_for_computer()
            hint_checks += 1
        elif game.get_status_attr() == "computer-thinking":
            game.wait_for_computer()
        else:
            i = game.first_empty_cell()
            if i is not None and not game.is_cell_disabled(i):
                game.click_cell(i)
                game.wait_for_computer()

    game.assert_game_over()
    assert hint_checks > 0, (
        f"Hint was never checked during the game (difficulty={difficulty})"
    )

# ---------------------------Difficulty--------------------------------- #
@pytest.mark.game
def test_difficulty_selector_present(logged_in_game: GamePage):
    """TC-GAME-30: difficulty selector is visible."""
    logged_in_game.assert_visible(GamePage.SELECT_DIFFICULTY)


@pytest.mark.game
@pytest.mark.parametrize("level", ["easy", "medium", "hard"])
def test_difficulty_can_be_changed(logged_in_game: GamePage, level: str):
    """TC-GAME-31: easy, medium, and hard difficulty options are selectable."""
    logged_in_game.set_difficulty(level)  # type: ignore[arg-type]
    logged_in_game.new_game()
    logged_in_game.assert_board_empty()


@pytest.mark.game
def test_mid_game_difficulty_change_accept_resets_board(logged_in_game: GamePage):
    """TC-GAME-32: accepting mid-game difficulty change resets the board."""
    logged_in_game.set_difficulty("easy")
    logged_in_game.click_cell(0)
    logged_in_game.wait_for_computer()
    assert logged_in_game.get_cell_state(0) != "empty"

    logged_in_game.change_difficulty_mid_game("Hard", accept_dialog=True)
    logged_in_game.assert_board_empty()
    assert logged_in_game.get_selected_difficulty() == "hard"


@pytest.mark.game
def test_mid_game_difficulty_change_cancel_keeps_board(logged_in_game: GamePage):
    """TC-GAME-33: canceling mid-game difficulty change keeps the current board."""
    logged_in_game.set_difficulty("easy")
    logged_in_game.click_cell(0)
    logged_in_game.wait_for_computer()
    board_before = logged_in_game.get_board_state()

    logged_in_game.change_difficulty_mid_game("Hard", accept_dialog=False)
    assert logged_in_game.get_board_state() == board_before
    assert logged_in_game.get_selected_difficulty() == "easy"


@pytest.mark.game
def test_click_spam_registers_single_human_move(logged_in_game: GamePage):
    """TC-GAME-10: rapid clicks on one cell still produce one human mark."""
    logged_in_game.cell(0).click(click_count=5)
    logged_in_game.wait_for_computer()
    assert logged_in_game.count_marks("x") == 1
    assert logged_in_game.count_marks("o") >= 1
