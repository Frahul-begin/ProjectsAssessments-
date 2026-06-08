import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

# ==============================================================================
# STEP 1: INITIALIZATION & SETUP
# ==============================================================================
print("[INFO] Initializing Chrome Driver for Mobile Automation demo...")
options = webdriver.ChromeOptions()
options.add_argument("--disable-notifications")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

try:
    # ==============================================================================
    # STEP 2: NAVIGATE TO AMAZON
    # ==============================================================================
    print("[INFO] Navigating to Amazon.in...")
    driver.get("https://www.amazon.in")

    # ==============================================================================
    # STEP 3: SEARCH FOR MOBILES
    # ==============================================================================
    print("[INFO] Searching for 'Mobiles'...")
    search_box = wait.until(EC.element_to_be_clickable((By.ID, "twotabsearchtextbox")))
    search_box.send_keys("Mobiles")

    search_button = driver.find_element(By.ID, "nav-search-submit-button")
    search_button.click()

    # ==============================================================================
    # STEP 4: FILTER BY BRAND (SAMSUNG)
    # ==============================================================================
    print("[INFO] Applying Brand Filter: Samsung...")
    # Using a text-based XPath to ensure we hit the Samsung checkbox regardless of ID
    brand_filter = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//span[@class='a-size-base a-color-base' and text()='Samsung']")))
    brand_filter.click()

    # ==============================================================================
    # STEP 5: SORT RESULTS (Price: High to Low)
    # ==============================================================================
    print("[INFO] Sorting mobiles by 'Price: High to Low'...")
    sort_dropdown_trigger = wait.until(EC.element_to_be_clickable((By.ID, "s-result-sort-select")))

    select_sort = Select(sort_dropdown_trigger)
    select_sort.select_by_visible_text("Price: High to Low")

    # Wait for the mobile results grid to reload after sorting
    time.sleep(3)

    # ==============================================================================
    # STEP 6: VISUAL FEAT - SMOOTH SCROLLING
    # ==============================================================================
    print("[INFO] Scrolling through premium mobile listings...")
    for i in range(0, 1000, 250):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.4)

    # ==============================================================================
    # STEP 7: SELECT FIRST VALID MOBILE LINK
    # ==============================================================================
    print("[INFO] Identifying and clicking the flagship mobile product...")

    wait.until(EC.presence_of_element_located((By.XPATH, "//div[@data-component-type='s-search-result']")))

    # Target links containing Amazon's canonical /dp/ product identifier
    all_links = driver.find_elements(By.XPATH, "//a[contains(@href, '/dp/')]")

    product_link = None
    for link in all_links:
        try:
            title_text = link.text.strip()
            # Mobiles often have shorter titles; checking for 20+ chars
            if len(title_text) > 20:
                product_link = link
                print(f"[DATA] Selected Mobile: {title_text[:60]}...")
                break
        except Exception:
            continue

    if not product_link:
        raise Exception("Could not find a valid mobile product link.")

    print("[INFO] Executing stable JavaScript click...")
    driver.execute_script("arguments[0].click();", product_link)
    time.sleep(2)

    # ==============================================================================
    # STEP 8: WINDOW / TAB MANAGEMENT
    # ==============================================================================
    print("[INFO] Switching to product details tab...")
    parent_window = driver.current_window_handle
    all_windows = driver.window_handles

    if len(all_windows) > 1:
        for window in all_windows:
            if window != parent_window:
                driver.switch_to.window(window)
                print("[INFO] Tab switch successful.")
                break

    # ==============================================================================
    # STEP 9: DATA EXTRACTION
    # ==============================================================================
    print("[INFO] Extracting Mobile specifications and pricing...")

    try:
        final_title_el = wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
        final_title = final_title_el.text.strip()
        print(f"\n==================================================")
        print(f"SUCCESSFULLY SCRAPED MOBILE DETAILS:")
        print(f"Model: {final_title[:70]}...")
    except Exception as e:
        print(f"[WARN] Could not extract title: {str(e)}")

    try:
        # Multi-selector fallback for mobile pricing
        price_selectors = ["span.a-price-whole", "span.a-offscreen", "span#priceblock_ourprice"]
        product_price = "Pricing hidden or out of stock"
        for sel in price_selectors:
            try:
                found_price = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                if found_price:
                    product_price = found_price
                    break
            except:
                continue
        print(f"Price: ₹{product_price}")
        print(f"==================================================\n")
    except Exception:
        print("[WARN] Mobile price layout varied.")

    # ==============================================================================
    # STEP 10: FINAL VISUAL SHOWCASE
    # ==============================================================================
    print("[INFO] Displaying product specifications view...")
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(5)

finally:
    # ==============================================================================
    # STEP 11: CLEANUP
    # ==============================================================================
    print("[INFO] Closing browser and finishing automation session.")
    driver.quit()