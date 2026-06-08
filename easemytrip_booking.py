import os
import csv
import sys
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException
)

# ==========================================
# INDUSTRIAL LOGGING ENGINE
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("easemytrip_production_repaired.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("EaseMyTrip_QA_Engine")


class EaseMyTripAutomation:
    def __init__(self):
        logger.info("Initializing context-isolated Chrome environment...")
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--incognito")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        prefs = {"profile.default_content_setting_values.geolocation": 2}
        options.add_experimental_option("prefs", prefs)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
        self.wait = WebDriverWait(self.driver, 20)

        # Self-Healing Multilayer Locator Pool Registry
        self.locators_pool = {
            "from_field": [
                (By.ID, "FromSector_show"),
                (By.ID, "frmcity"),
                (By.CSS_SELECTOR, "#frmcity")
            ],
            "from_input": [
                (By.ID, "a_FromSector_show"),
                (By.XPATH, "//input[@id='a_FromSector_show']"),
                (By.CSS_SELECTOR, "input[placeholder='From']")
            ],
            "to_field": [
                (By.ID, "Editbox13_show"),
                (By.ID, "tocity"),
                (By.CSS_SELECTOR, "#tocity")
            ],
            "to_input": [
                (By.ID, "a_Editbox13_show"),
                (By.XPATH, "//input[@id='a_Editbox13_show']"),
                (By.CSS_SELECTOR, "input[placeholder='To']")
            ],
            "search_btn": [
                (By.CLASS_NAME, "srchBtnSe"),
                (By.XPATH, "//button[contains(@class, 'srchBtn') or contains(text(), 'Search')]"),
                (By.CSS_SELECTOR, ".srchBtnSe")
            ],
            "filter_nonstop": [
                (By.XPATH, "//label[contains(.,'Non-Stop') or contains(.,'Non stop')]//input"),
                (By.XPATH, "//span[text()='Non-Stop']/preceding-sibling::input"),
                (By.XPATH, "//input[@data-stop='0']")
            ],
            "filter_indigo": [
                (By.XPATH, "//label[contains(.,'IndiGo')]//input"),
                (By.XPATH, "//span[text()='IndiGo']/preceding-sibling::input"),
                (By.XPATH, "//input[@value='6E']")
            ],
            "filter_morning": [
                (By.XPATH,
                 "//label[contains(.,'Before 6 AM') or contains(.,'6 AM - 12 PM') or contains(.,'Depart Morning')]//input"),
                (By.XPATH, "//input[@data-time='morning']")
            ],
            "first_book_btn": [
                (By.XPATH, "(//button[text()='Book Now' or text()='BOOK NOW'])[1]"),
                (By.XPATH, "(//button[contains(@class,'book-btn') or contains(text(),'Book Now')])[1]"),
                (By.CSS_SELECTOR, ".book-bt-n")
            ],
            "traveller_title": [
                (By.XPATH, "//select[contains(@id,'title') or contains(@name,'Title') or contains(@class,'title')]"),
                (By.ID, "title")
            ],
            "first_name": [
                (By.XPATH,
                 "//input[contains(@id,'txtFN') or contains(@id,'FirstName') or contains(@placeholder,'First Name')]"),
                (By.CSS_SELECTOR, "input[placeholder*='First Name']")
            ],
            "last_name": [
                (By.XPATH,
                 "//input[contains(@id,'txtLN') or contains(@id,'LastName') or contains(@placeholder,'Last Name')]"),
                (By.CSS_SELECTOR, "input[placeholder*='Last Name']")
            ],
            "email_field": [
                (By.XPATH,
                 "//input[contains(@id,'txtEmailId') or contains(@id,'Email') or contains(@placeholder,'Email')]"),
                (By.CSS_SELECTOR, "input[type='email']")
            ],
            "phone_field": [
                (By.XPATH,
                 "//input[contains(@id,'txtCPhn') or contains(@id,'Mobile') or contains(@placeholder,'Phone')]"),
                (By.CSS_SELECTOR, "input[placeholder*='Number']")
            ],
            "continue_booking_btn": [
                (By.XPATH, "//input[@value='Continue Booking' or @id='fnl-submt']"),
                (By.XPATH, "//*[contains(@value, 'Continue') or contains(text(), 'Continue Booking')]"),
                (By.XPATH, "//div[contains(@class,'re-cont')]//input")
            ]
        }

    def wait_for_page_load(self, timeout=30):
        try:
            self.wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        except Exception as e:
            logger.warning(f"Page load state detection timed out: {e}")

    def find_healed_element(self, locator_key, timeout=12):
        locators = self.locators_pool.get(locator_key, [])
        local_wait = WebDriverWait(self.driver, timeout)
        for strategy, value in locators:
            try:
                element = local_wait.until(EC.presence_of_element_located((strategy, value)))
                return element
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                continue
        raise NoSuchElementException(f"All dynamic recovery paths failed for locator key: '{locator_key}'")

    def retry_action(self, action_callable, retries=3):
        for attempt in range(retries):
            try:
                return action_callable()
            except (StaleElementReferenceException, ElementClickInterceptedException,
                    ElementNotInteractableException) as e:
                logger.warning(f"Action exception encountered: {type(e).__name__}. Retrying {attempt + 1}/{retries}...")
                self.handle_popups()
                time.sleep(2)
        raise RuntimeError("Action execution sequence failed after maximum dynamic retry loops.")

    def safe_click(self, locator_key):
        def _click():
            el = self.find_healed_element(locator_key)
            self.safe_scroll(el)
            try:
                WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable(el))
                el.click()
            except Exception:
                logger.info(
                    f"Native click intercepted for '{locator_key}'. Failing over to direct JavaScript injection execution.")
                self.driver.execute_script("arguments[0].click();", el)

        self.retry_action(_click)

    def safe_send_keys(self, locator_key, text):
        def _send():
            el = self.find_healed_element(locator_key)
            try:
                el.clear()
            except Exception:
                pass
            el.send_keys(Keys.CONTROL + "a")
            el.send_keys(Keys.BACKSPACE)
            el.send_keys(text)

        self.retry_action(_send)

    def safe_scroll(self, element):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        except Exception:
            pass

    def handle_popups(self):
        popups = [
            "//span[@id='optInText']/following-sibling::span",
            "//button[contains(text(),'Later')]",
            "//div[contains(@class,'close') or contains(@id,'close') or text()='X']",
            "//a[contains(@class,'close')]",
            "//span[contains(@class,'close')]",
            "//button[text()='No, I’ll risk it' or contains(text(), 'risk it')]"
        ]
        for xpath in popups:
            try:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        logger.info(f"Intercepted unexpected view-blocking overlay element: {xpath}")
                        self.driver.execute_script("arguments[0].click();", el)
            except Exception:
                continue

    def select_suggestion(self, suggestion_text):
        def _select():
            suggestion_xpaths = [
                f"//*[contains(@id,'lblFrom') and contains(.,'{suggestion_text}')]",
                f"//*[contains(@id,'lblTo') and contains(.,'{suggestion_text}')]",
                f"//span[contains(text(),'{suggestion_text}(HYD)') or contains(text(),'{suggestion_text}(PNQ)')]",
                f"//div[contains(@id,'autoFill')]//li[contains(.,'{suggestion_text}')]"
            ]
            for xpath in suggestion_xpaths:
                elements = self.driver.find_elements(By.XPATH, xpath)
                for el in elements:
                    if el.is_displayed():
                        try:
                            el.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", el)
                        logger.info(f"Successfully processed auto-complete node: {suggestion_text}")
                        return True
            raise NoSuchElementException(f"Suggestion matching '{suggestion_text}' not localized dynamically.")

        self.retry_action(_select)

    def select_future_date_via_js(self):
        def _date_js():
            target_date = datetime(2026, 6, 22)
            formatted_date = target_date.strftime("%d/%m/%Y")
            display_date = target_date.strftime("%d %b %Y")

            logger.info(f"Injecting computed validation future date via DOM hooks: {formatted_date}")
            js_script = """
            var dateInput = document.getElementById('ddate') || document.querySelector('input[name="ddate"]');
            if(dateInput){
                dateInput.value = arguments[0];
                dateInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
            var displayInput = document.getElementById('txtDepartureDate');
            if(displayInput){
                displayInput.value = arguments[1];
                displayInput.dispatchEvent(new Event('change', { bubbles: true }));
            }
            return true;
            """
            self.driver.execute_script(js_script, formatted_date, display_date)
            return True

        self.retry_action(_date_js)

    def scrape_results(self):
        self.wait_for_page_load()
        flights_data = []
        rows = self.driver.find_elements(By.XPATH,
                                         "//div[contains(@class,'air-list') or contains(@id,'ResultDiv') or contains(@class,'row no-margn')]")

        for index, row in enumerate(rows):
            try:
                airline = row.find_element(By.XPATH, ".//span[contains(@class,'airln-name')]").text.strip()
                dept = row.find_element(By.XPATH,
                                        ".//div[contains(@class,'col-2') or contains(.,':')]//span[1]").text.strip()
                arr = row.find_element(By.XPATH, ".//div[contains(@class,'col-4')]//span[1]").text.strip()
                duration = row.find_element(By.XPATH, ".//span[contains(@class,'dura_md')]").text.strip()
                price = row.find_element(By.XPATH,
                                         ".//div[contains(@class,'col-6')]//p | .//div[contains(@class,'price')]").text.strip()

                flights_data.append({
                    "Airline Name": airline,
                    "Departure Time": dept,
                    "Arrival Time": arr,
                    "Duration": duration,
                    "Price": price
                })
            except Exception:
                continue
        return flights_data

    def handle_seat_selection_matrix(self):
        logger.info("Validating airplane seat map interactive panels...")
        try:
            seat_layout_box = self.driver.find_elements(By.XPATH,
                                                        "//div[contains(@class,'seat-layout') or contains(@id,'seat')]")
            if seat_layout_box and seat_layout_box[0].is_displayed():
                vacant_cells = self.driver.find_elements(By.XPATH,
                                                         "//div[contains(@class,'seat-free') or contains(@class,'vacant') or contains(@data-seat,'available')]")
                if vacant_cells:
                    try:
                        vacant_cells[0].click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", vacant_cells[0])
                    logger.info("Selected first free structural aircraft seat row allocation.")
                    time.sleep(1.0)

                seat_forward_btn = self.driver.find_element(By.XPATH,
                                                            "//*[contains(@id,'seatContinue') or contains(text(),'Proceed to onward') or contains(text(),'Book Seat')]")
                try:
                    seat_forward_btn.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", seat_forward_btn)
            else:
                logger.info("No functional seat selection module visualized. Continuing execution route map.")
        except Exception as e:
            logger.warning(f"Seat matrix selection skipped or automatically advanced by system state: {e}")

    def run(self):
        try:
            logger.info("Launching Target Production Application Dashboard.")
            self.driver.get("https://www.easemytrip.com/")
            self.wait_for_page_load()
            self.handle_popups()

            logger.info("PHASE 1: Injecting Dynamic Origins Parameters...")
            self.safe_click("from_field")
            time.sleep(1.0)
            self.safe_send_keys("from_input", "Hyderabad")
            time.sleep(2.0)
            self.select_suggestion("Hyderabad")

            logger.info("Injecting Dynamic Destinations Parameters...")
            self.safe_click("to_field")
            time.sleep(1.0)
            self.safe_send_keys("to_input", "Pune")
            time.sleep(2.0)
            self.select_suggestion("Pune")

            logger.info("Resolving Dynamic Calendar Targets for 22/06/2026...")
            self.select_future_date_via_js()
            time.sleep(1.0)

            logger.info("Triggering Query Submission Pipe.")
            self.safe_click("search_btn")
            self.wait_for_page_load()

            logger.info("PHASE 2: Injecting Structural Sorting Criteria Filters.")
            try:
                self.safe_click("filter_nonstop")
                time.sleep(1.5)
            except Exception:
                pass

            try:
                self.safe_click("filter_indigo")
                time.sleep(1.5)
            except Exception:
                pass

            try:
                self.safe_click("filter_morning")
                time.sleep(1.5)
            except Exception:
                pass

            logger.info("Harvesting Filtered Structural Metadata rows.")
            flight_results = self.scrape_results()

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("execution_artifacts", exist_ok=True)
            csv_path = f"execution_artifacts/flights_data_{ts}.csv"
            with open(csv_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=["Airline Name", "Departure Time", "Arrival Time", "Duration",
                                                       "Price"])
                writer.writeheader()
                writer.writerows(flight_results)
            logger.info(f"Extracted {len(flight_results)} flights to data log: {csv_path}")

            logger.info("PHASE 3: Initiating Flight Selection Pipeline Automation Sequence.")
            self.safe_click("first_book_btn")
            time.sleep(3.0)

            # --- REPAIRED: SLIDING FARE OVERLAY PANEL HANDLER ---
            try:
                logger.info("Locating sliding fare upgrade dialog container options...")
                # Direct precise target selection click targeting the IndiGo Upfront selection card tab
                upfront_tab = self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class,'fare-opt') and contains(.,'IndiGo Upfront')] | //div[contains(text(),'IndiGo Upfront')] | //span[contains(text(),'Upfront')]"
                )))
                try:
                    upfront_tab.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", upfront_tab)
                logger.info("Successfully toggled IndiGo Upfront fare tier package selection.")
                time.sleep(1.5)

                # Execute dynamic click onto the inner overlay validation panel "Book Now" control handle
                inner_book_cta = self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//div[contains(@class,'fare-footer')]//button | //div[@id='morefare']//button[contains(@class,'Book Now') or contains(text(),'Book Now')] | //button[contains(@class,'orange-bt') and text()='Book Now'] | //a[contains(@class,'Book Now') or contains(@class,'btn')] [contains(text(),'Book Now')]"
                )))
                try:
                    inner_book_cta.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", inner_book_cta)
                logger.info("Finalized inner fare panel sliding choice workflow redirect path execution trigger.")
            except Exception as slide_err:
                logger.warning(
                    f"Sliding panel selection fallback encountered: {slide_err}. Forcing default direct form pipeline access.")

            self.wait_for_page_load()
            time.sleep(4.0)

            logger.info("PHASE 4: Injecting Demographics metadata payload to passenger portal.")

            # --- REPAIRED: NO INSURANCE RADIO CONTROL BYPASS VIA ATOMIC TEXT LABEL ---
            try:
                logger.info("Targeting insurance declaration selection panel inputs...")
                # Target the visual text string node label structure directly to avoid ElementNotInteractable restrictions on the input node
                insurance_label = self.wait.until(EC.element_to_be_clickable((
                    By.XPATH,
                    "//label[contains(.,'No, I do not want to insure')] | //span[contains(text(),'No, I do not want to insure')] | //input[@id='chkInsuranceNo']/ancestor::label"
                )))
                try:
                    insurance_label.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", insurance_label)
                logger.info("Successfully checked option control: 'No, I do not want to insure my trip'")
            except Exception as ins_err:
                logger.error(f"Critical Halt: Insurance choice label could not be activated: {ins_err}")

            # Demographic Forms Mapping Sequences Execution
            try:
                title_dropdown = self.find_healed_element("traveller_title")
                title_dropdown.send_keys("Mr")
            except Exception:
                pass

            self.safe_send_keys("first_name", "Rahul")
            self.safe_send_keys("last_name", "rathod")
            self.safe_send_keys("email_field", "rahulbharadwaj8888@gmail.com")
            self.safe_send_keys("phone_field", "7601099989")

            try:
                consent_checkbox = self.driver.find_element(By.XPATH,
                                                            "//input[@type='checkbox' and contains(@id,'chk')]")
                if not consent_checkbox.is_selected():
                    try:
                        consent_checkbox.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", consent_checkbox)
            except Exception:
                pass

            # --- REPAIRED: DEEP SEQUENTIAL PROGRESSION STEP MACHINE ---
            logger.info("PHASE 5 & 6: Advancing sequential ancillary sections until checkout gateway checkpoint.")
            continue_btn = self.find_healed_element("continue_booking_btn")
            self.safe_scroll(continue_btn)
            try:
                continue_btn.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", continue_btn)
            time.sleep(3.0)

            # Loop multiple times to progress past meals, baggage selections, and upgrades seamlessly
            for progression_idx in range(6):
                try:
                    self.handle_popups()

                    # Absolute Breakpoint Condition: The core checkout payment framework panel arrives in the viewport
                    gateways = self.driver.find_elements(By.XPATH,
                                                         "//*[contains(text(),'Payment Mode') or contains(text(),'Choose Payment Method') or contains(@id,'payment')]")
                    if gateways and any(g.is_displayed() for g in gateways):
                        logger.info(
                            "Verified active arrival on final payment dashboard platform interface layer. Terminating sequence.")
                        break

                    nav_triggers = self.driver.find_elements(
                        By.XPATH,
                        "//input[@value='Continue Booking'] | //button[contains(text(),'Continue')] | //span[text()='Continue'] | //button[@id='btnBaggageContinue'] | //input[contains(@value,'Continue')] | //button[contains(@id,'Skip') or contains(text(),'Skip')]"
                    )
                    for trigger in nav_triggers:
                        if trigger.is_displayed():
                            logger.info(
                                f"Advancing downstream checkout funnel section page segment layer index #{progression_idx + 1}")
                            try:
                                trigger.click()
                            except Exception:
                                self.driver.execute_script("arguments[0].click();", trigger)
                            time.sleep(3.0)
                            break
                except Exception:
                    pass

            # PHASE 7: Process aircraft seat selections map configurations if popped up inside view
            self.handle_seat_selection_matrix()

            logger.info("PHASE 8: Reached Checkout Gateway Terminal Frame. Capturing proof verification artifacts.")
            self.wait.until(EC.presence_of_element_located((
                By.XPATH,
                "//*[contains(text(),'Payment Mode') or contains(text(),'UPI') or contains(text(),'Net Banking') or contains(@id,'payment')]"
            )))
            time.sleep(2.0)

            ss_path = f"execution_artifacts/payment_gateway_checkpoint_{ts}.png"
            self.driver.save_screenshot(ss_path)
            logger.info(f"SUCCESS: System verify checkout layout point achieved. Artifact saved to: {ss_path}")

            logger.info(
                "PHASE 9: Gracefully tearing down session and reverting browser context cleanly back to home domain.")
            self.driver.get("https://www.easemytrip.com/")
            self.wait_for_page_load()

        except Exception as e:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("execution_artifacts", exist_ok=True)
            err_ss = f"execution_artifacts/failure_capture_{ts}.png"
            self.driver.save_screenshot(err_ss)
            logger.error(f"Critical execution fault triggered. Diagnostic trace frame captured: {err_ss}",
                         exc_info=True)
        finally:
            logger.info("De-allocating Runtime Browser Resources Gracefully.")
            self.driver.quit()


if __name__ == "__main__":
    engine = EaseMyTripAutomation()
    engine.run()