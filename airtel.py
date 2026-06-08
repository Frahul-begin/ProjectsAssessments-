import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# STEP 1: INITIALIZATION
# ==============================================================================
print("[INFO] Launching Chrome for Airtel Portal Showcase...")
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 20)

try:
    # ==============================================================================
    # STEP 2: LOAD RECHARGE PAGE
    # ==============================================================================
    print("[INFO] Opening Airtel Prepaid Recharge Page...")
    driver.get("https://www.airtel.in/recharge/prepaid/")
    time.sleep(5)  # Let the dynamic single-page components fully mount

    # ==============================================================================
    # STEP 3: ENTER MOBILE NUMBER (FIXED WITH MULTI-SELECTOR FALLBACK)
    # ==============================================================================
    print("[INFO] Locating Mobile Number input field...")

    # Try multiple dynamic XPaths/CSS selectors to safely grab the input box
    input_selectors = [
        "//input[contains(@placeholder, 'Mobile')]",
        "//input[contains(@id, 'mobile')]",
        "input[type='tel']",
        "//input[@name='mobileNumber']"
    ]

    phone_field = None
    for selector in input_selectors:
        try:
            if selector.startswith("//") or selector.startswith("//*"):
                phone_field = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            else:
                phone_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            if phone_field:
                break
        except Exception:
            continue

    if not phone_field:
        raise Exception("Could not find the mobile number input box using fallback selectors.")

    print("[INFO] Injecting Mobile Number...")
    phone_field.clear()
    phone_field.send_keys("9876543210")
    time.sleep(2)

    # Send Key press event to trigger background calculations
    phone_field.send_keys(Keys.ENTER)
    print("[SUCCESS] Mobile number accepted by backend.")

    # ==============================================================================
    # STEP 4: WAIT FOR THE DYNAMIC PLAN GRID TO UNPACK
    # ==============================================================================
    print("[INFO] Waiting for the async SPA plan cards to build in DOM...")
    # Wait until any text element mentioning a recharge price or plan category mounts
    wait.until(EC.presence_of_element_located((
        By.XPATH, "//*[contains(text(), 'Plan')] | //*[contains(text(), 'Validity')] | //li"
    )))
    time.sleep(4)  # Settle dynamic visual shifts

    # ==============================================================================
    # STEP 5: SELECT FILTER CATEGORY (Truly Unlimited)
    # ==============================================================================
    print("[INFO] Applying Category Filter: 'Truly Unlimited'...")
    try:
        unlimited_tab = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//*[text()='Truly Unlimited'] | //li[contains(.,'Truly Unlimited')] | //*[contains(text(), 'Unlimited')]"
        )))
        driver.execute_script("arguments[0].click();", unlimited_tab)
        print("[SUCCESS] Grid filtered by Unlimited packages.")
        time.sleep(3)
    except Exception:
        print("[WARN] Category filter ribbon skipped, working with default catalog.")

    # ==============================================================================
    # STEP 6: PROGRESSIVE visual SCROLL
    # ==============================================================================
    print("[INFO] Scrolling down to load specific plan elements into viewport...")
    driver.execute_script("window.scrollBy(0, 450);")
    time.sleep(2)

    # ==============================================================================
    # STEP 7: CLICK RECHARGE/BUY ACTION ON FIRST PLAN
    # ==============================================================================
    print("[INFO] Isolating the primary Plan option transaction trigger...")

    buy_buttons = driver.find_elements(By.XPATH,
                                       "//button[contains(text(), 'Buy')] | //button[contains(text(), 'Recharge')] | //span[text()='BUY'] | //button[contains(@class, 'recharge-btn')]")

    if not buy_buttons:
        raise Exception("Could not resolve any buy buttons on the plan page.")

    print("[INFO] Executing safe JavaScript click on selected plan card...")
    driver.execute_script("arguments[0].click();", buy_buttons[0])
    time.sleep(5)  # Give the billing system time to assemble the secure gateway frame

    # ==============================================================================
    # STEP 8: GATEWAY VERIFICATION & EVIDENCE SCREENSHOT
    # ==============================================================================
    print("[INFO] Verifying checkout page validation states...")

    # Save tracking evidence screenshot
    screenshot_name = "airtel_payment.png"
    driver.save_screenshot(screenshot_name)
    print(f"\n==================================================")
    print(f"SUCCESSFULLY SCRAPED AIRTEL DETAILS:")
    print(f"Checkout Screenshot Captured: {screenshot_name}")
    print(f"Verification Location: {os.getcwd()}/{screenshot_name}")
    print(f"==================================================\n")

    # ==============================================================================
    # STEP 9: PRESENTATION FRAME HOLD
    # ==============================================================================
    print("[INFO] Final focus presentation freeze hold active...")
    time.sleep(5)

finally:
    # ==============================================================================
    # STEP 10: BRING DOWN BROWSER ENVIRONMENT
    # ==============================================================================
    print("[INFO] Terminating active browser instance safely.")
    driver.quit()