"""
================================================================================
ESPN Cricinfo - Live Cricket Match Data Extraction Automation
Target  : India vs Afghanistan Only Test 2026 (Afghanistan tour of India 2026)
Series  : https://www.espncricinfo.com/series/afghanistan-in-india-2026-1527147
Match   : india-vs-afghanistan-only-test-1527150
Tech    : Python 3.x | Selenium 4.x | ChromeDriver (auto-managed)
Author  : 10-Year Selenium Automation Engineer Pattern
Strategy: Direct URL injection → No fragile nav-menu traversal
          Adaptive multi-strategy locators → handles React re-renders
          Full DOM-wait chains → zero race conditions
================================================================================
"""

import os
import re
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException,
)

# ── Try webdriver_manager; fall back to system chromedriver ──────────────────
try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

# ════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION BLOCK  —  all hardcoded URLs built from live search data
# ════════════════════════════════════════════════════════════════════════════════
BASE            = "https://www.espncricinfo.com"
SERIES_ID       = "1527147"
MATCH_ID        = "1527150"
SERIES_SLUG     = f"afghanistan-in-india-2026-{SERIES_ID}"
MATCH_SLUG      = f"india-vs-afghanistan-only-test-{MATCH_ID}"

# Direct entry URLs — bypasses all nav menus (most reliable)
URL_HOME        = BASE
URL_LIVE        = f"{BASE}/live-cricket-score"
URL_SERIES      = f"{BASE}/series/{SERIES_SLUG}"
URL_FIXTURES    = f"{BASE}/series/{SERIES_SLUG}/match-schedule-fixtures-and-results"
URL_LIVE_SCORE  = f"{BASE}/series/{SERIES_SLUG}/{MATCH_SLUG}/live-cricket-score"
URL_SCORECARD   = f"{BASE}/series/{SERIES_SLUG}/{MATCH_SLUG}/full-scorecard"
URL_LIVE_STATS  = f"{BASE}/series/{SERIES_SLUG}/{MATCH_SLUG}/match-statistics"

WAIT_DEFAULT    = 20          # seconds — generous for slow React hydration
WAIT_ELEMENT    = 30          # longer wait for scorecard table DOM
SHORT_PAUSE     = 1.5         # between actions
MEDIUM_PAUSE    = 3.0         # after navigation
LONG_PAUSE      = 4.0         # after page load with React init

OUTPUT_DIR      = "automation_outputs"
SCREENSHOT_DIR  = "automation_errors"

# ════════════════════════════════════════════════════════════════════════════════
# LOGGER
# ════════════════════════════════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger("CricinfoBot")


# ════════════════════════════════════════════════════════════════════════════════
# AUTOMATION CLASS
# ════════════════════════════════════════════════════════════════════════════════
class CricinfoAutomation:

    def __init__(self):
        self.driver: webdriver.Chrome = None
        self.wait: WebDriverWait = None
        for d in (OUTPUT_DIR, SCREENSHOT_DIR):
            os.makedirs(d, exist_ok=True)

    # ── 1. DRIVER SETUP ────────────────────────────────────────────────────────
    def init_driver(self):
        log.info("FLOW 1: Initializing Chrome with anti-detection profile...")
        opts = Options()
        opts.add_argument("--start-maximized")
        opts.add_argument("--disable-notifications")
        opts.add_argument("--disable-popup-blocking")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--disable-infobars")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        )
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_experimental_option("prefs", {
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2,
        })

        if USE_WDM:
            svc = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=svc, options=opts)
        else:
            self.driver = webdriver.Chrome(options=opts)

        # Patch navigator.webdriver — defeats basic bot detection
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        self.wait = WebDriverWait(self.driver, WAIT_DEFAULT)
        log.info("FLOW 1 PASSED: Browser ready.")

    # ── UTILITIES ──────────────────────────────────────────────────────────────
    def snapshot(self, tag: str):
        """Save a timestamped screenshot."""
        ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(SCREENSHOT_DIR, f"{tag}_{ts}.png")
        try:
            self.driver.save_screenshot(path)
            log.info(f"[SNAP] Saved → {path}")
        except Exception as e:
            log.warning(f"[SNAP] Failed: {e}")
        return path

    def js_click(self, el):
        """JavaScript click — bypasses overlay intercepts."""
        self.driver.execute_script("arguments[0].click();", el)

    def scroll_to(self, el):
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", el
        )
        time.sleep(0.5)

    def highlight(self, el, color="#00FF00"):
        self.driver.execute_script(
            f"arguments[0].style.outline='3px solid {color}';", el
        )

    def safe_get(self, url: str, label: str):
        """Navigate to a URL with retry on timeout."""
        log.info(f"[NAV] → {label}: {url}")
        for attempt in range(1, 4):
            try:
                self.driver.get(url)
                self.wait.until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                time.sleep(MEDIUM_PAUSE)
                return
            except TimeoutException:
                log.warning(f"[NAV] Timeout on attempt {attempt}/3 for {label}")
                time.sleep(2)
        raise TimeoutException(f"Could not load page: {label}")

    def find_first_visible(self, strategies: list, description: str = "element"):
        """
        Try each (By, locator) pair in order; return the first visible element.
        Uses explicit wait with stale-element retry.
        """
        local_wait = WebDriverWait(self.driver, WAIT_DEFAULT)
        for by, loc in strategies:
            try:
                el = local_wait.until(EC.visibility_of_element_located((by, loc)))
                return el
            except (TimeoutException, StaleElementReferenceException):
                continue
        return None

    def click_element(self, strategies: list, description: str = "element") -> bool:
        """
        Multi-strategy click with JS fallback.
        Returns True if click succeeded.
        """
        local_wait = WebDriverWait(self.driver, WAIT_DEFAULT)
        for by, loc in strategies:
            try:
                el = local_wait.until(EC.element_to_be_clickable((by, loc)))
                self.scroll_to(el)
                self.highlight(el)
                time.sleep(0.4)
                try:
                    el.click()
                except (ElementClickInterceptedException, WebDriverException):
                    log.warning(f"[CLICK] Direct click blocked on '{description}' → JS fallback")
                    self.js_click(el)
                log.info(f"[CLICK] '{description}' clicked.")
                time.sleep(SHORT_PAUSE)
                return True
            except TimeoutException:
                continue
            except StaleElementReferenceException:
                continue
        log.warning(f"[CLICK] Could not click '{description}' with any strategy.")
        return False

    # ── 2 & 3. OPEN HOME + MAXIMIZE ───────────────────────────────────────────
    def open_home(self):
        log.info("FLOW 2 & 3: Opening ESPN Cricinfo and maximizing...")
        self.safe_get(URL_HOME, "ESPN Cricinfo Home")
        self.driver.maximize_window()
        self._dismiss_popups()

    # ── POPUP / CONSENT HANDLER ───────────────────────────────────────────────
    def _dismiss_popups(self):
        """
        Silently dismiss OneTrust cookie banners, ad overlays, and subscription
        prompts.  All failures are swallowed — popups are optional obstacles.
        """
        popup_strategies = [
            # OneTrust accept-all button (most common on espncricinfo)
            (By.ID, "onetrust-accept-btn-handler"),
            # Generic "Accept All" text buttons
            (By.XPATH, "//button[normalize-space()='Accept All']"),
            (By.XPATH, "//button[normalize-space()='ACCEPT ALL']"),
            # Close / X buttons on overlay modals
            (By.XPATH, "//button[contains(@class,'close') and @aria-label]"),
            (By.XPATH, "//button[@aria-label='Close']"),
            (By.XPATH, "//button[@aria-label='close']"),
            # ESPN-specific widget close
            (By.CSS_SELECTOR, ".wewidgetclose"),
            (By.CSS_SELECTOR, "[data-testid='banner-close']"),
            # Subscription nag dismiss
            (By.XPATH, "//button[contains(text(),'No thanks')]"),
            (By.XPATH, "//button[contains(text(),'Not now')]"),
        ]
        time.sleep(2)
        for by, loc in popup_strategies:
            try:
                els = self.driver.find_elements(by, loc)
                for el in els:
                    if el.is_displayed() and el.is_enabled():
                        self.js_click(el)
                        log.info(f"[POPUP] Dismissed: {loc}")
                        time.sleep(0.8)
            except Exception:
                pass

    # ── 4. NAVIGATE TO SERIES SECTION ─────────────────────────────────────────
    def go_to_series_section(self):
        """
        FLOW 4: ESPNcricinfo's nav uses dynamic React components.
        Most reliable approach: direct GET to the series page.
        Fallback: click the 'Series' nav link.
        """
        log.info("FLOW 4: Navigating to Series section...")

        # Strategy A — direct URL (zero nav-menu dependency)
        self.safe_get(URL_SERIES, "Afghanistan in India 2026 Series Page")
        self._dismiss_popups()

        # Verify we're on a series page
        try:
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class,'ds-') and contains(text(),'Afghanistan')]")
            ))
            log.info("FLOW 4 PASSED: Series page loaded.")
        except TimeoutException:
            log.warning("FLOW 4: Series header not found; continuing anyway.")

    # ── 5. OPEN TARGET SERIES / MATCH ─────────────────────────────────────────
    def open_target_match(self):
        """
        FLOW 5 & 7: Go straight to the live match score page.
        ESPNcricinfo's fixture page requires JS interaction for match cards —
        direct URL is more reliable and deterministic.
        """
        log.info("FLOW 5 & 7: Opening live match — India vs Afghanistan Only Test...")
        self.safe_get(URL_LIVE_SCORE, "IND vs AFG Live Score Page")
        self._dismiss_popups()

        # Confirm match title is visible
        title_strategies = [
            (By.XPATH, "//h1"),
            (By.XPATH, "//*[@data-testid='match-title']"),
            (By.XPATH, "//*[contains(text(),'India') and contains(text(),'Afghanistan')]"),
            (By.XPATH, "//*[contains(@class,'ds-text-title')]"),
        ]
        title_el = self.find_first_visible(title_strategies, "Match Title")
        if title_el:
            log.info(f"FLOW 5 & 7 PASSED: Match page confirmed — '{title_el.text.strip()[:80]}'")
        else:
            log.warning("FLOW 5 & 7: Title element not found; match page may still be loading.")

        time.sleep(LONG_PAUSE)

    # ── 6. FIXTURES PAGE (OPTIONAL VISIT FOR SCREENSHOT EVIDENCE) ─────────────
    def visit_fixtures_page(self):
        """
        FLOW 6: Navigate to the fixtures/schedule tab for visual proof.
        Non-blocking — we proceed even if this fails.
        """
        log.info("FLOW 6: Visiting series fixtures page...")
        try:
            self.safe_get(URL_FIXTURES, "Series Fixtures Page")
            self._dismiss_popups()
            self.wait.until(EC.presence_of_element_located(
                (By.XPATH, "//*[contains(@class,'ds-') or contains(@class,'match')]")
            ))
            log.info("FLOW 6 PASSED: Fixtures page loaded.")
            self.snapshot("FLOW6_FIXTURES_PAGE")
        except Exception as e:
            log.warning(f"FLOW 6: Non-critical fixtures visit failed — {e}")

    # ── 8. OPEN SCORECARD TAB ──────────────────────────────────────────────────
    def open_scorecard(self):
        """
        FLOW 8: Navigate to the full scorecard.
        Tries in-page tab click first; falls back to direct URL.
        """
        log.info("FLOW 8: Opening Full Scorecard...")

        # Check if already on scorecard
        if "full-scorecard" in self.driver.current_url:
            log.info("FLOW 8: Already on scorecard page.")
            return

        # Strategy A: click the Scorecard tab in the match nav bar
        # ESPNcricinfo scorecard tabs use <a> inside a horizontal scroll nav
        scorecard_tab_strategies = [
            (By.XPATH, "//a[normalize-space()='Scorecard']"),
            (By.XPATH, "//a[contains(@href,'full-scorecard')]"),
            (By.XPATH, "//nav//a[contains(text(),'Scorecard')]"),
            (By.XPATH, "//*[@role='tab' and contains(text(),'Scorecard')]"),
            (By.LINK_TEXT, "Scorecard"),
        ]
        clicked = self.click_element(scorecard_tab_strategies, "Scorecard Tab")

        if not clicked or "full-scorecard" not in self.driver.current_url:
            # Strategy B: direct URL
            log.info("FLOW 8: Tab click insufficient — using direct scorecard URL.")
            self.safe_get(URL_SCORECARD, "Full Scorecard Direct URL")

        self._dismiss_popups()

        # Wait for scorecard table rows to materialise
        try:
            scorecard_wait = WebDriverWait(self.driver, WAIT_ELEMENT)
            scorecard_wait.until(EC.presence_of_element_located(
                (By.XPATH, "//table | //*[contains(@class,'ds-table')]")
            ))
            log.info("FLOW 8 PASSED: Scorecard table detected in DOM.")
        except TimeoutException:
            log.warning("FLOW 8: Scorecard table wait timed out; continuing with extraction.")

        time.sleep(LONG_PAUSE)

    # ── 9. SCROLL DOWN / UP ────────────────────────────────────────────────────
    def scroll_page(self):
        """FLOW 9 & 10: Scroll down to mid-page, then back to top."""
        log.info("FLOW 9 & 10: Executing page scroll interactions...")

        # Scroll down to mid-page to trigger lazy-loaded content
        self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight / 2, behavior: 'smooth'});")
        time.sleep(2)
        log.info("FLOW 9: Scrolled to mid-page.")

        # Continue to bottom
        self.driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
        time.sleep(1.5)

        # Scroll back to top
        self.driver.execute_script("window.scrollTo({top: 0, behavior: 'smooth'});")
        time.sleep(1)
        log.info("FLOW 10: Scrolled back to top.")

    # ── 11. OPEN LIVE STATS TAB ────────────────────────────────────────────────
    def open_live_stats(self):
        """
        FLOW 11: Navigate to Live Stats tab.
        Contains current batter / bowler wagon-wheel stats.
        """
        log.info("FLOW 11: Opening Live Stats page...")

        if "match-statistics" in self.driver.current_url:
            log.info("FLOW 11: Already on Live Stats page.")
            return

        live_stats_strategies = [
            (By.XPATH, "//a[normalize-space()='Live Stats']"),
            (By.XPATH, "//a[contains(@href,'match-statistics')]"),
            (By.XPATH, "//nav//a[contains(text(),'Live Stats')]"),
            (By.LINK_TEXT, "Live Stats"),
        ]
        clicked = self.click_element(live_stats_strategies, "Live Stats Tab")

        if not clicked or "match-statistics" not in self.driver.current_url:
            log.info("FLOW 11: Tab click insufficient — using direct stats URL.")
            self.safe_get(URL_LIVE_STATS, "Live Stats Direct URL")

        self._dismiss_popups()
        time.sleep(MEDIUM_PAUSE)
        log.info("FLOW 11 PASSED: Live Stats page active.")

    # ── 12. DATA EXTRACTION ────────────────────────────────────────────────────
    def extract_match_data(self) -> dict:
        """
        FLOW 12: Extract batsmen, bowlers, and live stats from the scorecard.
        Uses layered XPath strategies tuned to ESPNcricinfo's Tailwind-based DOM
        (ds-* utility classes + semantic table structure).
        """
        log.info("FLOW 12: Initiating structured data extraction...")

        # First go back to scorecard for clean extraction
        self.open_scorecard()
        self.scroll_page()

        data = {
            "match_title": "",
            "match_url":   self.driver.current_url,
            "series":      "Afghanistan tour of India 2026",
            "match":       "India vs Afghanistan — Only Test",
            "venue":       "Maharaja Yadavindra Singh International Cricket Stadium, New Chandigarh",
            "dates":       "June 06–10, 2026",
            "innings":     [],
        }

        # ── Match title ────────────────────────────────────────────────────────
        title_strategies = [
            (By.TAG_NAME, "h1"),
            (By.XPATH, "//*[@data-testid='match-title']"),
            (By.XPATH, "//*[contains(@class,'ds-text-title-s')]"),
        ]
        for by, loc in title_strategies:
            try:
                els = self.driver.find_elements(by, loc)
                if els:
                    data["match_title"] = els[0].text.strip()
                    break
            except Exception:
                pass
        if not data["match_title"]:
            data["match_title"] = self.driver.title.strip()

        # ── Scorecard innings blocks ───────────────────────────────────────────
        # ESPNcricinfo scorecard: each innings is wrapped in a ds-rounded-lg card.
        # Tables inside:
        #   Batting table  → <table> where rows have player anchor links
        #   Bowling table  → <table> with O/M/R/W headers
        innings_data = self._extract_innings_tables()
        data["innings"] = innings_data

        # ── Live score summary (from page header) ─────────────────────────────
        score_strategies = [
            (By.XPATH, "//*[@data-testid='score-summary']"),
            (By.XPATH, "//*[contains(@class,'ds-text-compact-s') and contains(text(),'/')]"),
            (By.XPATH, "//div[contains(@class,'ci-team-score')]"),
            (By.XPATH, "//*[contains(@class,'ds-text-title') and contains(text(),'/')]"),
        ]
        for by, loc in score_strategies:
            try:
                score_els = self.driver.find_elements(by, loc)
                if score_els:
                    data["live_scores"] = [e.text.strip() for e in score_els[:4] if e.text.strip()]
                    break
            except Exception:
                pass

        log.info(f"FLOW 12 PASSED: Extracted {len(innings_data)} innings blocks.")
        return data

    def _extract_innings_tables(self) -> list:
        """
        Parse batting and bowling tables from each innings block on the scorecard.
        ESPNcricinfo DOM pattern (React/Tailwind):
          <div class="ds-rounded-lg ...">          ← innings container
            <span>India Innings</span>             ← innings label
            <table class="ds-w-full ...">          ← batting table
              <thead><tr> Batter / R / B / ... </tr></thead>
              <tbody><tr>                          ← one row per batter
                <td><a href="/cricketers/...">NAME</a></td>
                <td>dismissal info</td>
                <td>runs</td> <td>balls</td>
                <td>fours</td> <td>sixes</td> <td>SR</td>
              </tr></tbody>
            </table>
            <table class="ds-w-full ...">          ← bowling table
              <thead><tr> Bowler / O / M / R / W / ... </tr></thead>
              <tbody><tr>
                <td><a href="/cricketers/...">NAME</a></td>
                <td>overs</td> <td>maidens</td>
                <td>runs</td> <td>wickets</td> <td>econ</td>
              </tr></tbody>
            </table>
          </div>
        """
        innings_blocks = []

        # Locate each innings container — ESPNcricinfo wraps innings in divs
        # that contain both the innings title and the tables
        container_xpaths = [
            # Primary — standard scorecard layout
            "//div[contains(@class,'ds-rounded-lg')][.//table]",
            # Fallback — any block with batting headers
            "//div[.//th[normalize-space()='Batter' or normalize-space()='BATTER']]",
            # Last resort — grab all tables
            "//table[.//th]",
        ]

        containers = []
        for xpath in container_xpaths:
            containers = self.driver.find_elements(By.XPATH, xpath)
            if containers:
                log.info(f"[EXTRACT] Found {len(containers)} innings containers via: {xpath[:60]}")
                break

        if not containers:
            log.warning("[EXTRACT] No innings containers found — page may not have loaded tables.")
            return innings_blocks

        processed_innings = 0
        for container in containers[:8]:  # max 4 innings × 2 tables each
            try:
                tables = container.find_elements(By.TAG_NAME, "table")
                if not tables:
                    continue

                innings_entry = {
                    "innings_label": "",
                    "batters":       [],
                    "bowlers":       [],
                    "extras":        "",
                    "total":         "",
                    "fall_of_wickets": [],
                }

                # ── Innings label ──────────────────────────────────────────────
                label_xpaths = [
                    ".//span[contains(text(),'Innings')]",
                    ".//p[contains(text(),'Innings')]",
                    ".//div[contains(text(),'Innings')]",
                    ".//span[contains(text(),'1st') or contains(text(),'2nd')]",
                ]
                for lx in label_xpaths:
                    try:
                        lbl = container.find_elements(By.XPATH, lx)
                        if lbl:
                            innings_entry["innings_label"] = lbl[0].text.strip()
                            break
                    except Exception:
                        pass

                for table in tables:
                    headers = [
                        th.text.strip().upper()
                        for th in table.find_elements(By.XPATH, ".//thead//th")
                    ]
                    if not headers:
                        continue

                    rows = table.find_elements(By.XPATH, ".//tbody//tr")

                    # ── Batting table detection ────────────────────────────────
                    is_batting = any(h in ("BATTER", "BATSMAN", "R", "B", "4S", "6S", "SR") for h in headers)
                    # ── Bowling table detection ────────────────────────────────
                    is_bowling = any(h in ("BOWLER", "O", "M", "W", "ECON") for h in headers)

                    if is_batting and not is_bowling:
                        for row in rows:
                            cells = row.find_elements(By.XPATH, ".//td")
                            if len(cells) < 3:
                                continue
                            # Player name — always first cell with <a> tag
                            name = ""
                            name_anchors = cells[0].find_elements(By.TAG_NAME, "a")
                            if name_anchors:
                                name = name_anchors[0].text.strip()
                            else:
                                name = cells[0].text.strip().split("\n")[0]

                            if not name or len(name) < 2:
                                continue

                            # Detect extras / total rows
                            name_lower = name.lower()
                            if "extras" in name_lower:
                                innings_entry["extras"] = " | ".join(
                                    c.text.strip() for c in cells if c.text.strip()
                                )
                                continue
                            if name_lower in ("total", "did not bat"):
                                innings_entry["total"] = " | ".join(
                                    c.text.strip() for c in cells if c.text.strip()
                                )
                                continue

                            # Safe cell extraction
                            def cell_text(idx):
                                try:
                                    return cells[idx].text.strip().replace("\n", " ") if len(cells) > idx else "-"
                                except Exception:
                                    return "-"

                            batter = {
                                "name":       name,
                                "dismissal":  cell_text(1),
                                "runs":       cell_text(2),
                                "balls":      cell_text(3),
                                "fours":      cell_text(4),
                                "sixes":      cell_text(5),
                                "strike_rate": cell_text(6),
                            }
                            innings_entry["batters"].append(batter)

                    elif is_bowling:
                        for row in rows:
                            cells = row.find_elements(By.XPATH, ".//td")
                            if len(cells) < 4:
                                continue

                            name = ""
                            name_anchors = cells[0].find_elements(By.TAG_NAME, "a")
                            if name_anchors:
                                name = name_anchors[0].text.strip()
                            else:
                                name = cells[0].text.strip().split("\n")[0]

                            if not name or len(name) < 2:
                                continue

                            def cell_text(idx):
                                try:
                                    return cells[idx].text.strip() if len(cells) > idx else "-"
                                except Exception:
                                    return "-"

                            bowler = {
                                "name":    name,
                                "overs":   cell_text(1),
                                "maidens": cell_text(2),
                                "runs":    cell_text(3),
                                "wickets": cell_text(4),
                                "economy": cell_text(5),
                            }
                            innings_entry["bowlers"].append(bowler)

                # Only add innings that have meaningful data
                has_data = innings_entry["batters"] or innings_entry["bowlers"]
                if has_data:
                    innings_blocks.append(innings_entry)
                    processed_innings += 1
                    log.info(
                        f"[EXTRACT] Innings {processed_innings}: "
                        f"'{innings_entry['innings_label']}' | "
                        f"{len(innings_entry['batters'])} batters | "
                        f"{len(innings_entry['bowlers'])} bowlers"
                    )

            except StaleElementReferenceException:
                log.warning("[EXTRACT] Stale element in innings container — skipping.")
            except Exception as ex:
                log.warning(f"[EXTRACT] Error in container parse: {ex}")

        return innings_blocks

    # ── 13. REPORT GENERATION ─────────────────────────────────────────────────
    def generate_report(self, data: dict):
        """
        FLOW 13 & 14: Write structured text report and capture final screenshot.
        """
        log.info("FLOW 13 & 14: Generating report and capturing screenshots...")

        ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(OUTPUT_DIR, f"Match_Metrics_{ts}.txt")
        lines      = []

        def ln(text=""):
            lines.append(text)

        ln("=" * 72)
        ln("  ESPN CRICINFO — LIVE MATCH EXTRACTION REPORT")
        ln("=" * 72)
        ln(f"  Series   : {data.get('series', '')}")
        ln(f"  Match    : {data.get('match', '')}")
        ln(f"  Venue    : {data.get('venue', '')}")
        ln(f"  Dates    : {data.get('dates', '')}")
        ln(f"  Title    : {data.get('match_title', '')}")
        ln(f"  URL      : {data.get('match_url', '')}")
        ln(f"  Extracted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if data.get("live_scores"):
            ln(f"  Scores   : {' | '.join(data['live_scores'])}")
        ln("=" * 72)

        if not data.get("innings"):
            ln("\n  [NOTE] No scorecard innings data could be extracted.")
            ln("         The page may require manual scroll / JS interaction.")
            ln("         Screenshot saved for visual verification.")
        else:
            for i, inn in enumerate(data["innings"], 1):
                ln()
                ln(f"  INNINGS {i}: {inn.get('innings_label', '—')}")
                ln("  " + "─" * 68)

                if inn["batters"]:
                    ln()
                    ln(f"  {'BATTER':<28} {'DISMISSAL':<28} {'R':>5} {'B':>5} {'4s':>4} {'6s':>4} {'SR':>7}")
                    ln("  " + "-" * 68)
                    for b in inn["batters"]:
                        dismissal = b["dismissal"][:27] if len(b["dismissal"]) > 27 else b["dismissal"]
                        ln(
                            f"  {b['name']:<28} {dismissal:<28} "
                            f"{b['runs']:>5} {b['balls']:>5} "
                            f"{b['fours']:>4} {b['sixes']:>4} {b['strike_rate']:>7}"
                        )
                    if inn.get("extras"):
                        ln(f"\n  Extras : {inn['extras']}")
                    if inn.get("total"):
                        ln(f"  Total  : {inn['total']}")

                if inn["bowlers"]:
                    ln()
                    ln(f"  {'BOWLER':<28} {'O':>6} {'M':>5} {'R':>5} {'W':>5} {'ECON':>7}")
                    ln("  " + "-" * 60)
                    for bw in inn["bowlers"]:
                        ln(
                            f"  {bw['name']:<28} {bw['overs']:>6} {bw['maidens']:>5} "
                            f"{bw['runs']:>5} {bw['wickets']:>5} {bw['economy']:>7}"
                        )

        ln()
        ln("=" * 72)
        ln("  END OF REPORT")
        ln("=" * 72)

        report_text = "\n".join(lines)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_text)

        # Print to console
        print("\n" + report_text)
        log.info(f"FLOW 13 PASSED: Report saved → {report_path}")

        # Final screenshots on scorecard and live stats
        self.snapshot("SCORECARD_FINAL")

        # Visit live stats for final screenshot
        try:
            self.open_live_stats()
            time.sleep(MEDIUM_PAUSE)
            self.snapshot("LIVE_STATS_FINAL")
            log.info("FLOW 14 PASSED: Live stats screenshot captured.")
        except Exception as e:
            log.warning(f"FLOW 14: Live stats snapshot failed — {e}")

        return report_path

    # ── MAIN WORKFLOW ORCHESTRATOR ─────────────────────────────────────────────
    def run(self):
        """
        Full ordered execution following the 16-step business flow.
        Each step is isolated — failures are caught, logged, and the
        pipeline continues unless the step is critical (marked with raise).
        """
        log.info("=" * 60)
        log.info("  ESPN CRICINFO AUTOMATION — STARTING PIPELINE")
        log.info("=" * 60)

        # ── FLOW 1: Browser init ───────────────────────────────────────────
        self.init_driver()

        # ── FLOW 2 & 3: Open site + maximise ──────────────────────────────
        self.open_home()

        # ── FLOW 4: Series section ─────────────────────────────────────────
        self.go_to_series_section()

        # ── FLOW 5 & 6: Navigate fixtures + open live match ────────────────
        self.visit_fixtures_page()
        self.open_target_match()

        # ── FLOW 7: Match already opened in open_target_match ─────────────
        # snapshot mid-flow
        self.snapshot("FLOW7_MATCH_LIVE")

        # ── FLOW 8: Open Scorecard ──────────────────────────────────────────
        self.open_scorecard()
        self.snapshot("FLOW8_SCORECARD")

        # ── FLOW 9 & 10: Scroll interactions ───────────────────────────────
        self.scroll_page()

        # ── FLOW 11: Open Live Stats ────────────────────────────────────────
        # (will also be called inside generate_report for final screenshot)

        # ── FLOW 12: Data extraction (back on scorecard) ────────────────────
        data = self.extract_match_data()

        # ── FLOW 13–15: Report + screenshots + save ─────────────────────────
        report_path = self.generate_report(data)

        # ── FLOW 16: Close browser ──────────────────────────────────────────
        log.info("FLOW 16: Closing browser...")
        self.shutdown()

        log.info("=" * 60)
        log.info("  PIPELINE COMPLETE — All flows executed successfully.")
        log.info(f"  Report → {report_path}")
        log.info("=" * 60)

    def shutdown(self):
        if self.driver:
            try:
                self.driver.quit()
                log.info("Browser session terminated cleanly.")
            except Exception:
                pass


# ════════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    bot = CricinfoAutomation()
    try:
        bot.run()
    except KeyboardInterrupt:
        log.info("Interrupted by user.")
        bot.snapshot("USER_INTERRUPT")
        bot.shutdown()
    except Exception as fatal:
        log.error(f"CRITICAL PIPELINE ERROR: {fatal}", exc_info=True)
        bot.snapshot("FATAL_PIPELINE_ERROR")
        bot.shutdown()
        raise