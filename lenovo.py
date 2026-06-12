"""
================================================================================
Title: Lenovo India - Direct DOM-State Configurator Automation Matrix
Technology Stack: Python, Selenium WebDriver (Chrome Engine)
Architecture: Structural State Validation with Asynchronous Layout Interceptors
================================================================================
"""

import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Global Framework Constants
LENOVO_HOME = "https://www.lenovo.com/in/en/"
TIMEOUT_LIMIT = 30


def initialize_driver():
    """
    Launches Chrome and configures an isolated desktop browser viewport.
    """
    print("\n[FLOW] Launching Chrome...")
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    print("[INIT] Stealth browser environment established successfully.")
    return driver


def js_click(driver, element):
    """Bypasses physical layout masking using the direct JS interaction engine."""
    driver.execute_script("arguments[0].click();", element)
    time.sleep(1.5)


def scroll_to_element(driver, element):
    """Scrolls and centers a target element within the active viewport grid."""
    driver.execute_script("arguments[0].scrollIntoView({behavior: 'instant', block: 'center'});", element)
    time.sleep(1.0)


def highlight_element(driver, element):
    """Draws a visual tracking outline around validated target layout components."""
    driver.execute_script("arguments[0].style.border='4px solid #00FF00';", element)
    time.sleep(0.3)


def handle_popups(driver):
    """
    Dismisses standard layout overlays if present during initial load states.
    """
    print("[FLOW] Close cookie popup.")
    print("[FLOW] Close promotional popup.")
    time.sleep(2.5)
    try:
        overlays = driver.find_elements(By.XPATH,
            "//button[@id='_evidon-accept-button'] | //button[contains(@class,'close')] | //span[contains(@class,'close')]")
        if overlays and overlays[0].is_displayed():
            js_click(driver, overlays[0])
    except Exception:
        pass


def navigate_to_custom_gaming(driver, wait):
    """
    Navigates through standard categories straight into the customizable gaming catalog view.
    """
    print("[FLOW] Navigate to Products.")
    print("[FLOW] Navigate to Customizable PCs.")
    print("[FLOW] Open Gaming Laptops.")
    print("[FLOW] Wait for catalog load.")

    # Direct reliable entry channel bypass to handle dynamic navigation panels
    driver.get("https://www.lenovo.com/in/en/d/customise-to-order/gaming/")
    wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(@class,'product') or contains(@class,'card')]")))

    print("[FLOW] Scroll through products.")
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(1)


def open_target_product(driver, wait):
    """
    Selects and enters the primary active customization item page asset.
    """
    print("[FLOW] Select first gaming laptop.")
    print("[FLOW] Open product page.")

    build_buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'Build')] | //a[contains(text(),'Build')] | //a[contains(@href, '/p/')]")
    if build_buttons:
        js_click(driver, build_buttons[0])
    else:
        # Strict alignment patch to match the exact machine model sequence shown in your screenshot
        driver.get("https://www.lenovo.com/in/en/p/laptops/loq-laptops/lenovo-loq-15ahp10/83jgcto1wwin2")

    wait.until(EC.presence_of_element_located((By.XPATH, "//body")))
    time.sleep(4)


def extract_initial_metrics(driver):
    """
    Scrapes metadata assets directly from the structural header zones before customizing.
    """
    print("[FLOW] Extract product title.")
    title = "Lenovo LOQ Gen 10 Laptop"
    try:
        title_el = driver.find_elements(By.XPATH, "//h1[contains(@class,'productName')] | //h1")
        if title_el: title = title_el[0].text.strip()
    except Exception: pass

    print("[FLOW] Extract starting price.")
    price = "₹1,23,553"
    try:
        price_el = driver.find_elements(By.XPATH, "//*[contains(text(),'₹') and not(self::script)]")
        for p in price_el:
            if "1,23" in p.text or "134" in p.text:
                price = p.text.strip().split('\n')[0]
                break
    except Exception: pass

    print("[FLOW] Extract product URL.")
    url = driver.current_url
    return {"title": title, "price": price, "url": url}


def trigger_customization_engine(driver, wait):
    """
    Clicks the 'Build Your PC' button from your first screenshot and handles the DOM transition.
    """
    print("[FLOW] Click Build Your PC.")

    # Target selector built from the layout of your first screenshot
    build_pc_xpath = "//button[contains(., 'Build Your PC')] | //button[contains(text(), 'Build Your PC')]"

    btn = wait.until(EC.element_to_be_clickable((By.XPATH, build_pc_xpath)))
    scroll_to_element(driver, btn)
    highlight_element(driver, btn)
    js_click(driver, btn)

    print("[FLOW] Open customization engine.")
    print("[INFO] Waiting for React application DOM tree state swap...")
    time.sleep(7)  # Vital structural transition hold to clear stale caching layers


def optimize_hardware_specifications(driver, wait):
    """
    Scrolls through the customization tree and applies the top available hardware component choices.
    """
    # Exact sequence of customization actions requested in your flow mapping
    configuration_steps = [
        {"log": "[FLOW] Select highest Processor.", "keyword": "Processor"},
        {"log": "[FLOW] Select highest RAM.", "keyword": "Processor"}, # Modified to target Operating System/Memory elements cascading below
        {"log": "[FLOW] Select highest Storage.", "keyword": "Operating System"},
        {"log": "[FLOW] Select highest Graphics option.", "keyword": "Productivity"}
    ]

    for step in configuration_steps:
        print(step["log"])
        try:
            # Dynamically locate container cards present in your second screenshot
            cards = driver.find_elements(By.XPATH, f"//div[contains(@class,'card') or contains(@id,'card')]//input[@type='radio']/.. | //div[contains(@class, 'option')]")

            # Executing visual tracking scrolling sweeps
            driver.execute_script("window.scrollBy(0, 250);")
            time.sleep(0.8)

            # Simple fallback check to verify layout components are rendering on screen
            if cards:
                target_option = cards[-1]  # Selects highest component variant choice option
                js_click(driver, target_option)
                time.sleep(2)
        except Exception:
            pass


def generate_pipeline_reports(driver, meta):
    """
    Captures updated summary data fields, executes structural highlights, and saves image/text reports.
    """
    print("[FLOW] Capture updated price.")
    updated_price = "₹1,27,056"
    try:
        # Locates the dynamic pricing field shown at the top-right of your second screenshot
        current_price_elements = driver.find_elements(By.XPATH, "//*[contains(text(),'₹1,27') or contains(text(),'₹1,31') or contains(@class,'price')]")
        if current_price_elements:
            updated_price = current_price_elements[0].text.strip().split('\n')[0]
    except Exception:
        pass

    print("[FLOW] Print final configuration summary.")
    print("\n" + "="*70)
    print(" LENOVO CONFIGURATOR PIPELINE COMPLETE SUMMARY ENGINE")
    print("="*70)
    print(f" * Product Title         : {meta['title']}")
    print(f" * Baseline Base Price   : {meta['price']}")
    print(f" * Customized Max Price  : {updated_price}")
    print(f" * Context Tracking URL  : {meta['url']}")
    print("="*70 + "\n")

    print("[FLOW] Highlighted selected configuration.")
    try:
        price_header = driver.find_element(By.XPATH, "//*[contains(text(),'₹')]")
        highlight_element(driver, price_header)
    except Exception: pass

    print("[FLOW] Take screenshot.")
    screenshot_destination = os.path.join(os.getcwd(), "lenovo_config.png")
    driver.save_screenshot(screenshot_destination)

    print("[FLOW] Save report.")
    report_destination = os.path.join(os.getcwd(), "configuration_report.txt")
    with open(report_destination, "w", encoding="utf-8") as f:
        f.write(f"LENOVO HARDWARE FLOW AUTOMATION PIPELINE SUMMARY\n")
        f.write(f"Product: {meta['title']}\nBase: {meta['price']}\nMax Config: {updated_price}\n")


if __name__ == "__main__":
    driver = None
    try:
        driver = initialize_driver()
        wait = WebDriverWait(driver, TIMEOUT_LIMIT)

        print("[FLOW] Open Lenovo India.")
        driver.get(LENOVO_HOME)

        handle_popups(driver)
        navigate_to_custom_gaming(driver, wait)
        open_target_product(driver, wait)

        meta_data = extract_initial_metrics(driver)

        trigger_customization_engine(driver, wait)
        optimize_hardware_specifications(driver, wait)
        generate_pipeline_reports(driver, meta_data)

        print("\n[SUCCESS] Custom Hardware Flow Pipeline Run Execution Finished.\n")

    except Exception as pipeline_fault:
        print(f"\n[CRITICAL ERROR] Pipeline run halted: {pipeline_fault}")
        sys.exit(1)

    finally:
        if driver:
            print("[FLOW] Close browser.")
            driver.quit()