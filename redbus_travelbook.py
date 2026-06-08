import os
import time
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException,
    WebDriverException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Setup logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger()

# Screenshot directory
screenshots_dir = "screenshots"
if not os.path.exists(screenshots_dir):
    os.makedirs(screenshots_dir)


def take_screenshot(driver, name):
    """Take screenshot and save to file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(screenshots_dir, f"{name}_{timestamp}.png")
    try:
        driver.save_screenshot(filepath)
        logger.info(f"[INFO] Screenshot saved: {filepath}")
    except Exception as e:
        logger.warning(f"[WARNING] Could not save screenshot {name}: {e}")


def wait_clickable(driver, locator, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable(locator))


def wait_visible(driver, locator, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.visibility_of_element_located(locator))


def wait_present(driver, locator, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located(locator))


def scroll_into_view(driver, element):
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
    time.sleep(1)


def scroll_page(driver, offset):
    driver.execute_script(f"window.scrollBy(0, {offset});")
    time.sleep(1)


def lazy_load_handler(driver):
    """Scroll to bottom to ensure all elements are loaded (for lazy-loaded content)."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


def click_element(driver, element):
    """Click element with JS if normal click fails."""
    try:
        element.click()
    except Exception:
        driver.execute_script("arguments[0].click();", element)


def handle_popup(driver):
    """Attempt to close common popups (cookie, login, ads)."""
    popup_texts = ["close", "Close", "×", "OK"]
    for txt in popup_texts:
        try:
            btn = driver.find_element(By.XPATH,
                                      f"//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{txt.lower()}') or contains(@class, '{txt.lower()}')]")
            if btn.is_displayed():
                btn.click()
                logger.info("[INFO] Closed popup")
                time.sleep(1)
        except Exception:
            continue


def main():
    try:
        logger.info("[INFO] Initializing Chrome driver")
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        # options.add_argument("--headless")  # Uncomment for headless mode
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()

        # Navigate to redBus
        driver.get("https://www.redbus.in")
        logger.info("[INFO] Navigating to redBus homepage")
        time.sleep(3)
        take_screenshot(driver, "homepage")

        # Handle any initial popups (login, ads, cookies)
        handle_popup(driver)

        # Define source and destination
        source_city = "Pune"
        destination_city = "Hyderabad"

        # Locate source city input
        source_locators = [
            (By.ID, "src"),
            (By.ID, "fromCity"),
            (By.ID, "sourceCity"),
            (By.XPATH, "//span[text()='From']"),
            (By.XPATH, "//input[contains(@aria-label, 'From')]"),
            (By.XPATH, "//input[@placeholder='From']"),
            (By.XPATH, "//input[@placeholder='Enter Source City']"),
            (By.XPATH, "//div[contains(text(),'From')]//input")
        ]
        from_input = None
        for locator in source_locators:
            try:
                from_input = wait_clickable(driver, locator)
                if from_input:
                    break
            except Exception:
                continue
        if not from_input:
            logger.error("[FAIL] Could not locate source city input field")
            driver.quit()
            return

        # Click and type source
        scroll_into_view(driver, from_input)
        try:
            driver.execute_script("arguments[0].click();", from_input)
        except Exception:
            from_input.click()
        from_input.clear()
        from_input.send_keys(source_city)
        time.sleep(2)
        from_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(1)
        from_input.send_keys(Keys.ENTER)
        logger.info(f"[INFO] Set source city to '{source_city}'")

        # Locate destination city input
        dest_locators = [
            (By.ID, "dest"),
            (By.ID, "toCity"),
            (By.XPATH, "//span[text()='To']"),
            (By.XPATH, "//input[contains(@aria-label, 'To')]"),
            (By.XPATH, "//input[@placeholder='To']"),
            (By.XPATH, "//input[@placeholder='Enter Destination City']"),
            (By.XPATH, "//div[contains(text(),'To')]//input")
        ]
        to_input = None
        for locator in dest_locators:
            try:
                to_input = wait_clickable(driver, locator)
                if to_input:
                    break
            except Exception:
                continue
        if not to_input:
            logger.error("[FAIL] Could not locate destination city input field")
            driver.quit()
            return

        scroll_into_view(driver, to_input)
        try:
            driver.execute_script("arguments[0].click();", to_input)
        except Exception:
            to_input.click()
        to_input.clear()
        to_input.send_keys(destination_city)
        time.sleep(2)
        to_input.send_keys(Keys.ARROW_DOWN)
        time.sleep(1)
        to_input.send_keys(Keys.ENTER)
        logger.info(f"[INFO] Set destination city to '{destination_city}'")

        # Select journey date: try clicking 'Tomorrow' if present
        try:
            tomorrow_elem = driver.find_element(By.XPATH, "//div[normalize-space(text())='Tomorrow']")
            if tomorrow_elem.is_displayed():
                tomorrow_elem.click()
                logger.info("[INFO] Selected journey date: Tomorrow")
            else:
                raise Exception("Tomorrow option not visible")
        except Exception:
            # Fallback: open calendar and select tomorrow
            try:
                cal_label = driver.find_element(By.CSS_SELECTOR, "[for='onward_cal']")
                cal_label.click()
                time.sleep(1)
                tomorrow_date = datetime.now().date() + timedelta(days=1)
                target_day = tomorrow_date.day
                # navigate calendar to correct month if necessary
                while True:
                    try:
                        date_elem = driver.find_element(By.XPATH,
                                                        f"//div[@id='rb-calendar_onward_cal']//td[.='{target_day}']")
                        if date_elem.is_displayed():
                            date_elem.click()
                            logger.info(f"[INFO] Selected journey date: {tomorrow_date.strftime('%d-%m-%Y')}")
                            break
                    except NoSuchElementException:
                        next_btn = driver.find_element(By.CSS_SELECTOR, "#rb-calendar_onward_cal .next")
                        next_btn.click()
                        time.sleep(1)
                        continue
            except Exception as e:
                logger.warning(f"[WARNING] Could not select journey date automatically: {e}")

        time.sleep(1)

        # Locate and click Search button
        search_locators = [
            (By.XPATH, "//button[contains(text(),'Search')]"),
            (By.XPATH, "//button[contains(text(),'Search buses')]"),
            (By.CSS_SELECTOR, "button.search"),
            (By.CSS_SELECTOR, "button[type='submit']")
        ]
        search_button = None
        for locator in search_locators:
            try:
                search_button = wait_clickable(driver, locator)
                if search_button:
                    break
            except Exception:
                continue
        if not search_button:
            logger.error("[FAIL] Could not locate Search button")
            driver.quit()
            return
        scroll_into_view(driver, search_button)
        try:
            search_button.click()
        except Exception:
            driver.execute_script("arguments[0].click();", search_button)
        logger.info("[INFO] Search button clicked")
        take_screenshot(driver, "search_page")
        time.sleep(5)

        # Wait for results to load (presence of results container or items)
        try:
            results_section = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "searchResult"))
            )
        except TimeoutException:
            # fallback: presence of any result listing
            try:
                results_section = WebDriverWait(driver, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.XPATH, "//div[contains(@class,'busItem') or contains(@class,'bus-info')]"))
                )
            except TimeoutException:
                logger.warning("[WARNING] Search results did not load as expected")
                results_section = None

        take_screenshot(driver, "results_page")
        # Extract total bus count
        bus_count = 0
        try:
            # try to get text like "x buses found"
            count_elem = driver.find_element(By.XPATH,
                                             "//*[contains(text(),'buses available') or contains(text(),'buses found') or contains(text(),'results for')]")
            text = count_elem.text
            import re
            match = re.search(r'\d+', text)
            if match:
                bus_count = int(match.group())
        except Exception:
            # fallback: count listed results
            try:
                bus_items = driver.find_elements(By.XPATH, "//div[contains(@class,'bus-items')]/div")
                bus_count = len(bus_items)
            except Exception:
                bus_count = 0
        logger.info(f"[INFO] Total buses found: {bus_count}")

        # Apply filters: AC, Sleeper, Departure Time
        # AC filter
        try:
            ac_filter = driver.find_element(By.XPATH, "//label[contains(text(),'AC') or contains(text(),'A/c')]/input")
            if not ac_filter.is_selected():
                ac_filter.click()
                logger.info("[INFO] Filter 'AC' applied")
        except Exception:
            logger.warning("[WARNING] 'AC' filter not available")
        # Sleeper filter
        try:
            sleeper_filter = driver.find_element(By.XPATH, "//label[contains(text(),'Sleeper')]/input")
            if not sleeper_filter.is_selected():
                sleeper_filter.click()
                logger.info("[INFO] Filter 'Sleeper' applied")
        except Exception:
            logger.warning("[WARNING] 'Sleeper' filter not available")
        # Departure Time filter (pick first option if available)
        try:
            dep_filter_section = driver.find_element(By.XPATH, "//div[contains(text(),'Departure Time')]")
            scroll_into_view(driver, dep_filter_section)
            dep_options = dep_filter_section.find_elements(By.XPATH, ".//following-sibling::div//label")
            if dep_options:
                dep_options[0].click()
                logger.info("[INFO] Departure Time filter applied")
        except Exception:
            logger.warning("[WARNING] 'Departure Time' filter not available")

        time.sleep(2)
        # Sorting: Fare Low to High or Rating High to Low
        try:
            sort_dropdown = driver.find_element(By.XPATH, "//select[@id='sortBy']")
            for option in sort_dropdown.find_elements(By.TAG_NAME, "option"):
                if "Fare - Low to High" in option.text:
                    option.click()
                    logger.info("[INFO] Sorting by Fare (Low to High) applied")
                    break
            else:
                for option in sort_dropdown.find_elements(By.TAG_NAME, "option"):
                    if "Rating" in option.text:
                        option.click()
                        logger.info("[INFO] Sorting by Rating applied")
                        break
        except Exception:
            logger.warning("[WARNING] Sort dropdown not available, skipping sort")

        time.sleep(3)

        # Select first bus and view seats
        try:
            first_view = driver.find_element(By.XPATH, "(//button[contains(text(),'View Seats')])[1]")
            scroll_into_view(driver, first_view)
            first_view.click()
            logger.info("[INFO] Clicked on first bus 'View Seats'")
        except Exception:
            try:
                first_view = driver.find_element(By.XPATH, "(//button[contains(.,'View Seats')])[1]")
                scroll_into_view(driver, first_view)
                driver.execute_script("arguments[0].click();", first_view)
                logger.info("[INFO] Clicked on first bus 'View Seats' (JS fallback)")
            except Exception:
                logger.error("[FAIL] Could not click 'View Seats' on first bus")
                driver.quit()
                return

        # Wait for seats layout page to load
        time.sleep(5)
        take_screenshot(driver, "bus_seats_page")

        # Extract bus details on the seats page
        source = source_city
        destination = destination_city
        travel_date = datetime.now().date() + timedelta(days=1)  # assuming tomorrow
        selected_bus = ""
        bus_type = ""
        departure_time = ""
        arrival_time = ""
        duration = ""
        rating = ""
        fare = ""
        available_seats = ""

        try:
            bus_heading = driver.find_element(By.XPATH,
                                              "//div[contains(@class,'title') or contains(@class,'travels-name')]")
            selected_bus = bus_heading.text
        except Exception:
            selected_bus = ""
        try:
            bus_type_el = driver.find_element(By.XPATH, "//div[contains(@class,'bus-type')]")
            bus_type = bus_type_el.text
        except Exception:
            bus_type = ""
        try:
            times = driver.find_elements(By.XPATH, "//div[contains(@class,'time')]")
            if times:
                departure_time = times[0].text
                if len(times) > 1:
                    arrival_time = times[1].text
        except Exception:
            departure_time = arrival_time = ""
        try:
            dur_el = driver.find_element(By.XPATH, "//div[contains(@class,'duration')]")
            duration = dur_el.text
        except Exception:
            duration = ""
        try:
            rating_el = driver.find_element(By.XPATH, "//div[contains(@class,'rating-stars')]")
            rating = rating_el.text
        except Exception:
            rating = ""
        try:
            fare_el = driver.find_element(By.XPATH, "//div[contains(@class,'fare')]")
            fare = fare_el.text
        except Exception:
            fare = ""
        try:
            seats_el = driver.find_element(By.XPATH,
                                           "//div[contains(text(),'available') or contains(text(),'seats left')]")
            available_seats = seats_el.text
        except Exception:
            available_seats = ""

        logger.info(f"[INFO] Selected Bus: {selected_bus}")
        logger.info(f"[INFO] Bus Type: {bus_type}")
        logger.info(f"[INFO] Departure Time: {departure_time}")
        logger.info(f"[INFO] Arrival Time: {arrival_time}")
        logger.info(f"[INFO] Duration: {duration}")
        logger.info(f"[INFO] Rating: {rating}")
        logger.info(f"[INFO] Fare: {fare}")
        logger.info(f"[INFO] Available Seats: {available_seats}")

        # Scroll through seat layout (canvas)
        try:
            scroll_page(driver, 1000)
            time.sleep(1)
        except Exception:
            pass
        take_screenshot(driver, "seat_layout")

        # Journey summary
        logger.info("\n[INFO] Journey Summary:")
        logger.info(f"Source: {source}")
        logger.info(f"Destination: {destination}")
        logger.info(f"Date of Journey: {travel_date}")
        logger.info(f"Total Buses Found: {bus_count}")
        logger.info(f"Selected Bus: {selected_bus}")
        logger.info(f"Fare: {fare}")
        logger.info(f"Rating: {rating}")

    except Exception as e:
        logger.error(f"[FAIL] Unexpected error: {e}")
        take_screenshot(driver, "error")
    finally:
        time.sleep(2)
        driver.quit()
        logger.info("[INFO] Browser closed")


if __name__ == "__main__":
    main()
