WIN_LINES = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
)


def _winner(board: list[str]) -> str | None:
    for a, b, c in WIN_LINES:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


def _full(board: list[str]) -> bool:
    return all(cell != "empty" for cell in board)


def _minimax(board: list[str], player: str) -> int:
    winner = _winner(board)
    if winner == "x":
        return 1
    if winner == "o":
        return -1
    if _full(board):
        return 0
    scores: list[int] = []
    for i in range(9):
        if board[i] != "empty":
            continue
        board[i] = player
        scores.append(_minimax(board, "o" if player == "x" else "x"))
        board[i] = "empty"
    return max(scores) if player == "x" else min(scores)


def best_draw_move(board: list[str]) -> int | None:
    draw_moves: list[int] = []
    win_moves: list[int] = []
    loss_moves: list[int] = []
    for i in range(9):
        if board[i] != "empty":
            continue
        board[i] = "x"
        score = _minimax(board, "o")
        board[i] = "empty"
        if score == 0:
            draw_moves.append(i)
        elif score == 1:
            win_moves.append(i)
        else:
            loss_moves.append(i)
    if draw_moves:
        return draw_moves[0]
    if win_moves:
        return win_moves[0]
    return loss_moves[0] if loss_moves else None
