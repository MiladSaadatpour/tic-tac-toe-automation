# Quick Tech Notes

Just a few practical notes on why I built the framework this way.

### 1. Playwright + Pytest over Selenium
* Selenium needs too many explicit/implicit wait workarounds. Playwright handles element actionability (visible, stable) out of the box. No more `time.sleep()` hacks.
* **Super fast execution:** Instead of spinning up heavy, slow browser instances for each test, Playwright uses a single connection and isolated contexts. Running tests in parallel takes seconds.

---

### 2. The POM Setup
* All selectors and clicks live in `pages/`. The `tests/` folder only cares about the actual test flow and assertions. If the frontend devs change an ID tomorrow, we only fix it in one file.

---

### 3. Edge Cases & Handling Bugs
* **Breaking things on purpose (TC-SET-03):** To test resilience, the script injects corrupted JSON directly into `localStorage`. We need to make sure the app resets gracefully instead of just showing a blank white screen.
* **Flaky tests prevention:** Dynamic values like usernames get salted with a `_unique()` helper so tests don't step on each other's toes when running in parallel.
* **Tracking Known Defects (XFAIL):** For `TC-AUTH-18`, the frontend is missing the 100-character boundary validation that exists on the backend. Instead of skipping the whole test, I wrapped that specific long-name parameter in `pytest.param(..., marks=pytest.mark.xfail)`. This keeps the bug tracked in the test reports without breaking the CI/CD pipeline or turning the build red.

---

### 4. Running the Code
* **Parallel mode:** Run with `pytest -n auto` to trigger multiple workers. Every worker runs incognito, so zero state leaking.
* **Cross-browser check:** Just change the CLI argument to swap between `chromium`, `firefox`, or `webkit`.

---

### 5. Smart Fixture Architecture (conftest.py)
* Instead of copying the login steps inside every single game flow test, I created a `logged_in_game` fixture. It handles the authentication once at the setup phase and yields a ready-to-play `GamePage` instance straight to the test logic.
* **Automatic Cleanup:** To avoid bloating the application storage or leaving behind guest accounts, the fixtures automatically trigger `delete_account()` or clear browser cookies on the `teardown` phase right after each test finishes. 
* **State Isolation:** Every test gets a clean, fresh browser context via fixtures. This guarantees that if a test changes the language to Persian or corrupts `localStorage` in one run, it won't leak state or break the next test down the line.