# Tic-Tac-Toe — Test Automation

**Language:** Python 3.13  
**Framework:** Playwright + Pytest  
**Pattern:** Page Object Model (POM)  
**Browsers:** Chromium · Firefox · WebKit

---

## Test Plan

### Scope

The SUT is a single-page Tic-Tac-Toe game (`index.html`) with four feature areas:

| Area | Test File | Tests |
|------|-----------|------:|
| **Game Flow** | `test_game_flow.py` | 26 |
| **Settings** | `test_settings.py` | 15 |
| **Authentication & Profile** | `test_auth.py` | 20 |
| **Total** | | **61** |

### Risk-based priority

| Priority | Areas |
|----------|-------|
| **Critical** | Board interaction, win/draw detection, auth register/login, session handling, AI double-move prevention |
| **High** | Score tracking, New Game reset, theme/language persistence, history logging |
| **Medium** | Hint feature, difficulty levels, profile rename, history tab |
| **Low** | Edge cases (empty fields, duplicate name, UI labels) |

### Out of scope
- Visual / pixel-level regression
- Performance / load testing
- Mobile-specific layout (responsive CSS only)

---

## Project Structure

```
tic-tac-toe-automation/
├── pages/
│   ├── base_page.py        # Shared locator helpers & assertion wrappers
│   ├── game_page.py        # Board, toolbar, score, settings, hint
│   └── login_page.py       # Auth form, nav bar, profile, history
├── tests/
│   ├── conftest.py         # Fixtures, report hooks, two-tab helper
│   ├── test_game_flow.py   # 26 tests — moves, win/draw, score, hint, difficulty
│   ├── test_settings.py    # 15 tests — language, theme, persistence, cross-tab
│   └── test_auth.py        # 20 tests — register, login, logout, profile, session
├── reports/                # Auto-generated HTML reports (timestamped)
├── README.md
├── requirements.txt
└── pytest.ini
```

---

## Setup

### 1 — Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 2 — Install dependencies and browsers

```bash
pip install -r requirements.txt
playwright install chromium firefox webkit
```

---

## Running the tests

### All tests
```bash
pytest
```

### Headless mode
```bash
pytest --headless
```

### By priority / area
```bash
pytest -m critical        # critical flows only
pytest -m game            # game board & logic
pytest -m auth            # authentication & profile
pytest -m settings        # language & theme
pytest -m bug_hunting     # known defect tracking
```

### With headed browser (visible window)
```bash
pytest --headed -m critical
```

### Cross-browser
```bash
pytest --browser firefox
pytest --browser webkit
pytest --browser chromium --browser firefox --browser webkit   # all three
```

### Parallel execution
```bash
pytest -n auto                                                  # auto-detect CPU cores
pytest --browser chromium --browser firefox --browser webkit -n auto  # cross-browser + parallel
```

### Against a served URL
```bash
# macOS / Linux
URL=http://localhost:8080/index.html pytest

# Windows CMD
set URL=http://localhost:8080/index.html && pytest
```

---

## HTML Report

Every run generates a timestamped report in `reports/`:

```
reports/
├── report_all_2026-05-31_10-00-00.html
├── report_critical_2026-05-31_10-05-00.html
└── report_auth_2026-05-31_10-10-00.html
```

Failed tests automatically include a full-page screenshot embedded in the report.

---

## Key Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `page` | function | Navigates to SUT before each test |
| `game` | function | `GamePage` instance on a fresh page |
| `login` | function | `LoginPage` instance on a fresh page |
| `logged_in_game` | function | Registers guest → yields `GamePage` → logs out |
| `logged_in_login` | function | Registers guest → yields `LoginPage` → deletes account |
| `two_tabs` | function | Two pages sharing the same browser context (localStorage) |

---

## Design Decisions

| Decision | Reason |
|----------|--------|
| **Playwright + Pytest (native)** | Built-in `expect` with auto-retry, clean fixture model, no extra BDD layer |
| **Page Object Model** | Locators live in one place; tests read like plain English |
| **`data-testid` selectors** | Resilient to CSS/layout changes; already present in the SUT |
| **Timestamped reports** | Multiple runs don't overwrite each other; label reflects marker or file |
| **`pytest.mark` tags** | Enables targeted runs in CI (critical, game, auth, settings) |
| **`pytest.skip` for non-deterministic AI** | Win/draw outcomes depend on the AI; tests skip gracefully instead of flaking |
| **`two_tabs` fixture** | Shares a single browser context so both tabs see the same localStorage |
| **Screenshot on failure** | Embedded base64 PNG in the HTML report — no external file dependency |
