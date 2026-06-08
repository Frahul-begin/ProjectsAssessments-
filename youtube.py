from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

if not os.path.exists("screenshots"):
    os.makedirs("screenshots")

driver = webdriver.Chrome()
driver.maximize_window()

driver.get("https://www.youtube.com")

wait = WebDriverWait(driver, 20)

time.sleep(5)

search_box = wait.until(
    EC.presence_of_element_located(
        (By.NAME, "search_query")
    )
)

search_box.send_keys("Python Selenium Tutorial")
search_box.send_keys(Keys.ENTER)
time.sleep(5)

# Click first video
first_video = wait.until(
    EC.element_to_be_clickable(
        (By.ID, "video-title")
    )
)
first_video.click()
time.sleep(5)

driver.save_screenshot(
    "screenshots/youtube_video.png"
)

print(driver.title)

driver.quit()