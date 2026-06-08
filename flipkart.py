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
# STEP 1: INITIALIZATION & SETUP
# ==============================================================================
print("[INFO] Launching Chrome for Flipkart Earphones Showcase...")
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

try:
    # ==============================================================================
    # STEP 2: NAVIGATE TO FLIPKART
    # ==============================================================================
    print("[INFO] Loading Flipkart.com portal...")
    driver.get("https://www.flipkart.com")

    # ==============================================================================
    # STEP 3: DYNAMIC POPUP INTERCEPTOR
    # ==============================================================================
    print("[INFO] Running interceptor checks for floating login overlays...")
    try:
        popup_close_selectors = [
            "//span[@class='_30XB9F']",
            "//button[contains(text(),'✕')]",
            "/html/body/div[2]/div/div/button"
        ]
        for xpath in popup_close_selectors:
            elements = driver.find_elements(By.XPATH, xpath)
            if elements and elements[0].is_displayed():
                elements[0].click()
                print("[SUCCESS] Login overlay detected and bypassed.")
                break
    except Exception:
        print("[INFO] No login popup detected. Proceeding...")

    # ==============================================================================
    # STEP 4: SEARCH FOR EARPHONES
    # ==============================================================================
    print("[INFO] Searching for 'Earphones'...")
    search_box = wait.until(EC.element_to_be_clickable((By.NAME, "q")))
    search_box.send_keys("Earphones")
    search_box.send_keys(Keys.ENTER)
    print("[SUCCESS] Search submitted via Keyboard Enter.")

    # ==============================================================================
    # STEP 5: FILTER BY WIRELESS EARPHONES
    # ==============================================================================
    print("[INFO] Applying Category Filter: Wireless Earphones...")
    try:
        wireless_filter = wait.until(EC.element_to_be_clickable((
            By.XPATH, "//*[text()='Wireless Earphones']"
        )))
        driver.execute_script("arguments[0].click();", wireless_filter)
        print("[SUCCESS] Wireless Earphones filter applied.")
        time.sleep(4)
    except Exception:
        print("[WARN] Filter selection skipped.")

    # ==============================================================================
    # STEP 6: SORT RESULTS (Price -- High to Low)
    # ==============================================================================
    print("[INFO] Sorting by 'Price -- High to Low'...")
    high_to_low_sort = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Price -- High to Low']")))
    high_to_low_sort.click()
    time.sleep(4)

    # ==============================================================================
    # STEP 7: SMOOTH SCROLLING
    # ==============================================================================
    print("[INFO] Performing smooth visual scroll...")
    for i in range(0, 1000, 250):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.4)

    # ==============================================================================
    # STEP 8: SELECT FIRST ORGANIC PRODUCT
    # ==============================================================================
    print("[INFO] Identifying and clicking the first product...")
    all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/p/')]")
    product_link = None
    for link in all_links:
        try:
            title_text = link.text.strip()
            if len(title_text) > 20:
                product_link = link
                print(f"[DATA] Selected Product: {title_text[:60]}...")
                break
        except Exception:
            continue

    driver.execute_script("arguments[0].click();", product_link)
    time.sleep(3)

    # ==============================================================================
    # STEP 9: TAB MANAGEMENT & SCREENSHOT (NEW STEP)
    # ==============================================================================
    print("[INFO] Switching to product details tab...")
    parent_window = driver.current_window_handle
    all_windows = driver.window_handles

    for window in all_windows:
        if window != parent_window:
            driver.switch_to.window(window)
            print("[INFO] Tab switch successful.")
            break

    # NEW: Capture visual evidence
    print("[INFO] Capturing evidence screenshot...")
    driver.save_screenshot("flipkart.png")
    print(f"[SUCCESS] Screenshot saved as: {os.getcwd()}/flipkart.png")

    # ==============================================================================
    # STEP 10: DATA EXTRACTION
    # ==============================================================================
    print("[INFO] Extracting specifications...")
    try:
        title_element = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@class='VU-ZEz'] | //h1")))
        print(f"\n==================================================")
        print(f"SUCCESSFULLY SCRAPED DETAILS:")
        print(f"Product: {title_element.text.strip()[:70]}...")

        price_els = driver.find_elements(By.CSS_SELECTOR, "div.Nx937a, div.CxhGGd")
        if price_els:
            print(f"Price: {price_els[0].text.strip()}")
        print(f"==================================================\n")
    except Exception as e:
        print(f"[WARN] Extraction failed: {str(e)}")

    # ==============================================================================
    # STEP 11: FINAL VIEW
    # ==============================================================================
    driver.execute_script("window.scrollTo(0, 400);")
    time.sleep(5)

finally:
    print("[INFO] Closing browser.")
    driver.quit()