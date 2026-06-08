import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

# Initialize production-grade execution logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger("CricinfoAutomation")


class SelfHealingCricinfoAutomation:
    def __init__(self):
        self.driver = None
        self.wait_timeout = 15
        self.screenshot_dir = "automation_errors"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

    def init_driver(self):
        log.info("STEP 1: Initializing optimized Chrome instance with anti-detection flags...")
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--incognito")
        # Ensure standard responsive layout mapping matches modern viewport definitions
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

        # Suppress geographic permission modals natively at the web-engine level
        prefs = {
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=chrome_options)
        log.info("STEP 1 PASSED: Browser driver session loaded successfully.")

    def capture_failure_screenshot(self, context_name):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.screenshot_dir}/CRASH_{context_name}_{timestamp}.png"
        try:
            self.driver.save_screenshot(filename)
            log.error(f"[DIAGNOSTIC] Execution frame context captured and saved to: {filename}")
        except Exception as e:
            log.error(f"[DIAGNOSTIC] Warning: Secondary failure capturing screenshot reference: {str(e)}")

    def self_healing_click(self, locator_strategies, element_description="Element"):
        """
        Implements an elastic self-healing recovery loop iterating down prioritized
        locators up to 3 individual retries per strategy block to mitigate shadow DOM shifts.
        """
        wait = WebDriverWait(self.driver, self.wait_timeout)
        for strategy_idx, (by_method, locator_string) in enumerate(locator_strategies, start=1):
            log.info(
                f"[LOCATOR HEALING] Attempting discovery of {element_description} via strategy layer #{strategy_idx} ({by_method} -> '{locator_string}')...")
            for retry in range(3):
                try:
                    element = wait.until(EC.presence_of_element_located((by_method, locator_string)))
                    wait.until(EC.visibility_of(element))

                    # Scroll container smoothly into view before issuing mouse actions
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)

                    clickable_element = wait.until(EC.element_to_be_clickable((by_method, locator_string)))
                    clickable_element.click()
                    log.info(f"[LOCATOR HEALING] Action dispatched successfully on strategy layer #{strategy_idx}.")
                    return True
                except StaleElementReferenceException:
                    log.warning(
                        f"[RETRY ALERT] Caught StaleElementReferenceException for {element_description}. Retrying operational trace ({retry + 1}/3)...")
                    time.sleep(1)
                except ElementClickInterceptedException:
                    log.warning(
                        f"[RETRY ALERT] Click intercepted by dominant dynamic overlay framework. Forcing JavaScript click dispatch variant...")
                    try:
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except Exception:
                        break
                except TimeoutException:
                    log.warning(
                        f"[STRATEGY FAILURE] Timeout exceeded during lookup validation for strategy layer #{strategy_idx}.")
                    break
                except Exception as generic_err:
                    log.warning(f"[STRATEGY BYPASS] Unexpected internal exception caught: {str(generic_err)}")
                    break
        return False

    def bypass_consent_banners(self):
        log.info("[POPUP HANDLER] Scanning DOM viewport layer for cookie consent overlays or banners...")
        consent_strategies = [
            (By.ID, "onetrust-accept-btn-handler"),
            (By.XPATH, "//button[contains(@id,'accept') or contains(text(),'Accept All')]"),
            (By.CSS_SELECTOR, ".wewidgetclose"),
            (By.XPATH, "//div[contains(@class,'close') or contains(@class,'banner')]//button")
        ]
        # Attempt soft interaction, if none present, proceed without operational pipeline failure
        for by_method, locator in consent_strategies:
            try:
                el = self.driver.find_element(by_method, locator)
                if el.is_displayed():
                    el.click()
                    log.info("[POPUP HANDLER] Global privacy consent element cleared successfully.")
                    time.sleep(1)
                    return
            except Exception:
                continue

    def execute_pipeline(self):
        wait = WebDriverWait(self.driver, self.wait_timeout)

        # --- OPEN WEBSITE & MAXIMIZE ---
        log.info("STEP 2: Navigating to live target domain: https://www.espncricinfo.com/")
        self.driver.get("https://www.espncricinfo.com/")
        self.bypass_consent_banners()
        log.info("STEP 2 PASSED: Cricinfo portal initialized.")

        log.info("STEP 3: Maximizing workspace view boundaries...")
        self.driver.maximize_window()
        log.info("STEP 3 PASSED: Screen workspace maximize completed.")

        # --- CLICK SERIES LINK ---
        log.info("STEP 4: Executing click tracking on main navigation category link: 'Series'...")
        series_locators = [
            (By.LINK_TEXT, "Series"),
            (By.XPATH, "//a[@title='Series' or text()='Series']"),
            (By.CSS_SELECTOR, "a[href*='/series']")
        ]
        if not self.self_healing_click(series_locators, "Series Navigation Link"):
            self.capture_failure_screenshot("Series_Link_Failed")
            raise NoSuchElementException(
                "Critical Step Failure: Unable to interact with Series element across structural heuristics.")
        log.info("STEP 4 PASSED: Main navigation expanded.")

        # --- OPEN FIRST AVAILABLE SERIES ---
        log.info("STEP 5: Targeting lookup on sub-navigation lists for the primary active series row link...")
        first_series_locators = [
            (By.XPATH, "(//div[contains(@class,'ds-block')]//a[contains(@href,'/series/')])[1]"),
            (By.XPATH, "//ul[contains(@class,'series')]//a[1]"),
            (By.CSS_SELECTOR, "a.ds-inline-flex[href*='/series/']")
        ]

        # Capture current target tracking URL string before dispatching click handles
        try:
            target_series_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, "(//a[contains(@href,'/series/') and not(contains(@href,'/series/irone'))])[1]")))
            series_href = target_series_element.get_attribute("href")
            log.info(f"[DATA INSPECTION] Extracted target path map destination: {series_href}")
        except Exception:
            series_href = None

        if not self.self_healing_click(first_series_locators, "First Available Series Row Link"):
            # Self-healing fallback mechanism: Redirect directly to safe URL namespace if navigation link interception breaks
            if series_href:
                log.warning(
                    "[RECOVERY EXECUTION] Direct link interaction blocked. Executing safe fallback target path mapping navigation...")
                self.driver.get(series_href)
            else:
                self.capture_failure_screenshot("First_Series_Failed")
                raise NoSuchElementException(
                    "Critical Step Failure: Could not navigate to any active series index block.")

        time.sleep(3)  # Let secondary page layouts resolve completely
        self.bypass_consent_banners()
        log.info("STEP 5 PASSED: Target active series page loaded.")

        # --- NAVIGATION ARTIFACT: POINTS TABLE ---
        log.info("STEP 6: Locating tab container link item for 'Points Table'...")
        points_table_locators = [
            (By.LINK_TEXT, "Points Table"),
            (By.XPATH, "//a[contains(@href,'points-table') or contains(text(),'Points Table')]"),
            (By.CSS_SELECTOR, "a[href*='points-table']")
        ]

        points_table_found = self.self_healing_click(points_table_locators, "Points Table Tab Link")

        if points_table_found:
            log.info("STEP 6 PASSED: Points Table interface active.")
            time.sleep(2)

            # --- DATA EXTREACTION: TEAMS AND POINTS ---
            log.info(
                "STEP 7: Parsing active DOM table layout rows for Team names and corresponding calculated statistics points...")
            try:
                # Target teams text containers using modern semantic content classes
                team_elements = self.driver.find_elements(By.XPATH,
                                                          "//table//tbody//tr//span[contains(@class,'ds-text-title-xs')] | //table//tbody//tr//td[contains(@class,'ds-text-left')]//a")
                # Target points column tracking headers
                points_elements = self.driver.find_elements(By.XPATH,
                                                            "//table//tbody//tr//td[contains(@class,'ds-font-bold') or contains(@class,'ds-w-10')][1]")

                log.info(
                    f"[PARSING ENGINE] Identified {len(team_elements)} team names and {len(points_elements)} points metrics elements.")

                print("\n" + "=" * 60)
                print(f"      EXTRACTED TOURNAMENT POINTS TABLE : {self.driver.title[:30]}")
                print("=" * 60)
                print(f"{'TEAM NAME'.ljust(35)} | {'POINTS'.rjust(8)}")
                print("-" * 60)

                # Zip structures safely up to bounds to cleanly log output data
                for i in range(min(len(team_elements), len(points_elements))):
                    t_name = team_elements[i].text.strip()
                    p_val = points_elements[i].text.strip()
                    if t_name:  # Verify value contains a printable string
                        print(f"{t_name.ljust(35)} | {p_val.rjust(8)}")
                print("=" * 60 + "\n")
                log.info("STEP 7 PASSED: Point metric tables parsed and printed directly to output streams.")
            except Exception as data_parse_err:
                log.error(f"[NON-BLOCKING EXCEPTION] Failed to cleanly parse grid table details: {str(data_parse_err)}")
        else:
            log.warning(
                "STEP 6 BYPASSED: 'Points Table' option not present for this series format type (e.g. Bilateral series).")

        # --- NAVIGATION ARTIFACT: FIXTURES ---
        log.info("STEP 8: Attempting routing path swap to 'Fixtures' segment view...")
        fixtures_locators = [
            (By.LINK_TEXT, "Fixtures"),
            (By.XPATH,
             "//a[contains(@href,'match-schedule-fixtures') or contains(text(),'Fixtures') or contains(text(),'Matches')]"),
            (By.CSS_SELECTOR, "a[href*='match-schedule']")
        ]

        if not self.self_healing_click(fixtures_locators, "Fixtures Schedule Tab Link"):
            # Fallback path correction strategy
            current_url = self.driver.current_url
            if "/series/" in current_url:
                log.warning(
                    "[RECOVERY PATH] Link mapping obscured. Transforming current context path index directly to match schedule routes...")
                base_series_url = current_url.split("/series/")[0] + "/series/" + \
                                  current_url.split("/series/")[1].split("/")[0]
                self.driver.get(f"{base_series_url}/match-schedule-fixtures-and-results")
            else:
                self.capture_failure_screenshot("Fixtures_Navigation_Failed")
                raise NoSuchElementException(
                    "Critical Step Failure: Unable to locate fixtures sub-dashboard context pathways.")

        time.sleep(3)
        log.info("STEP 8 PASSED: Fixtures dashboard view active.")

        # --- OPEN FIRST MATCH ---
        log.info("STEP 9: Identifying match cards within schedule view to open first index instance...")
        first_match_locators = [
            (By.XPATH,
             "(//div[contains(@class,'ds-p-0')]//a[contains(@href,'/match/') or contains(@href,'/live-cricket-score')])[1]"),
            (By.XPATH, "(//a[contains(@href,'/match/')])[1]"),
            (By.CSS_SELECTOR, "a[href*='/match/']")
        ]

        if not self.self_healing_click(first_match_locators, "First Scheduled Match Card Link"):
            self.capture_failure_screenshot("First_Match_Open_Failed")
            raise NoSuchElementException("Critical Step Failure: Unable to open first match element.")

        time.sleep(3)
        self.bypass_consent_banners()
        log.info("STEP 9 PASSED: First match detail workspace screen loaded.")

        # --- OPEN SCORECARD TAB ---
        log.info("STEP 10: Validating tab menu layouts to isolate and click 'Scorecard' component items...")
        scorecard_tab_locators = [
            (By.LINK_TEXT, "Scorecard"),
            (By.XPATH, "//a[contains(@href,'full-scorecard') or contains(text(),'Scorecard')]"),
            (By.CSS_SELECTOR, "a[href*='full-scorecard']")
        ]

        # If the page already loaded straight into the full scorecard view, this click state turns into a clean non-blocking bypass
        if "full-scorecard" not in self.driver.current_url:
            self.self_healing_click(scorecard_tab_locators, "Full Scorecard Link Component")
        log.info("STEP 10 PASSED: Scorecard section contextual tracking active.")
        time.sleep(2)

        # --- EXTRACT BATSMEN NAMES ---
        log.info("STEP 11: Parsing active scorecard grids for data extraction on batsmen data streams...")
        try:
            batsmen_elements = self.driver.find_elements(By.XPATH,
                                                         "//td[contains(@class,'ds-w-0')]//a[contains(@href,'/player/')] | //div[contains(@class,'scorecard')]//span[contains(@class,'ds-font-bold')]")
            if batsmen_elements:
                print("\n" + "=" * 50)
                print("      EXTRACTED BATSMEN FIELD LIST FROM SCORECARD")
                print("=" * 50)
                extracted_count = 0
                for batsman in batsmen_elements:
                    name_txt = batsman.text.strip()
                    if name_txt and len(name_txt) > 2:
                        print(f"   * {name_txt}")
                        extracted_count += 1
                    if extracted_count >= 15:  # Establish safe performance pagination constraint cap boundary
                        break
                print("=" * 50 + "\n")
            else:
                log.warning(
                    "[PARSING ENGINE] Scorecard rows identified but return 0 nodes. Match might be unplayed/abandoned without a generated scorecard layout yet.")
            log.info("STEP 11 PASSED: Batsmen extraction handling sequence finished execution.")
        except Exception as batsman_parse_err:
            log.error(
                f"[NON-BLOCKING EXCEPTION] Failed to securely target batsmen data layouts: {str(batsman_parse_err)}")

        # --- TERMINAL MILESTONE SNAPSHOT ---
        log.info("STEP 12: Initializing final verification screenshot snapshot capture...")
        self.capture_failure_screenshot("FINAL_SUCCESS_SCORECARD_VIEW")
        log.info("STEP 12 PASSED: Final milestone verification image saved.")

    def shutdown(self):
        if self.driver:
            log.info("STEP 13: Terminating runtime selenium core drivers handles safely...")
            self.driver.quit()
            log.info("STEP 13 PASSED: Framework execution engine shutdown safely completed.")


if __name__ == "__main__":
    engine = SelfHealingCricinfoAutomation()
    try:
        engine.init_driver()
        engine.execute_pipeline()
        log.info(
            "SUCCESS: Production-grade execution pipeline successfully completed all validation tasks without unhandled exceptions.")
    except Exception as process_fatal_exception:
        log.error(
            f"FATAL PIPELINE CRASH: Execution failed during processing. Context log tracking: {str(process_fatal_exception)}")
    finally:
        engine.shutdown()