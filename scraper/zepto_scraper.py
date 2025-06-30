from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import quote
import time
import re
from utils.driver_setup import get_driver

def zepto_scraper(search_item, progress_callback=None):
    encoded_query = quote(search_item)
    url = f"https://www.zeptonow.com/search?query={encoded_query}"

    driver = get_driver()
    print(f"Navigating to {url}")
    driver.get(url)

    try:
        select_location_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH,
                "//span[normalize-space()='Select Location']"
            ))
        )
        select_location_btn.click()
        time.sleep(2)
    except Exception as e:
        print("Select Location button not found:", e)

    try:
        location_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search a new address']"))
        )
        location_input.clear()
        location_input.send_keys("Delhi")
        time.sleep(2)

        first_result = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "(//div[@data-testid='address-search-item'])[1]"))
        )
        first_result.click()
        time.sleep(3)
    except Exception as e:
        print("Location selection failed:", e)

    try:
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Confirm & Continue']"))
        )
        confirm_btn.click()
        time.sleep(3)
    except Exception as e:
        print("Confirm & Continue button not found or click failed:", e)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-testid='product-card']"))
        )
    except Exception:
        print("No products found.")
        driver.quit()
        return []

    max_scroll_attempts = 6
    scroll_pause_time = 2
    for i in range(max_scroll_attempts):
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(scroll_pause_time)
        if progress_callback:
            progress_callback((i + 1) / max_scroll_attempts)

    cards = driver.find_elements(
        By.XPATH, "//a[@data-testid='product-card']"
    )

    search_keywords = search_item.lower().split()
    products = []

    for i, card in enumerate(cards, start=1):
        try:
            out_of_stock_elem = card.find_element(
                By.XPATH,
                ".//button[@aria-label='Notify']"
            )
            continue
        except NoSuchElementException:
            pass

        try:
            product_name = card.find_element(
                By.XPATH,
                ".//h5[@data-testid='product-card-name']"
            ).text.strip()
        except Exception:
            product_name = None

        if product_name:
            name_lower = re.sub(r'[^a-z]', '', product_name.lower())
            if not all(word in name_lower for word in search_keywords):
                continue

        try:
            product_quantity = card.find_element(
                By.XPATH,
                ".//p[contains(@class,'text-[#5A6477]')]"
            ).text.strip()
        except Exception:
            product_quantity = None

        try:
            product_price = card.find_element(
                By.XPATH,
                ".//p[contains(@class,'text-[20px]')]"
            ).text.strip()
        except Exception:
            product_price = None

        try:
            product_image_elem = card.find_element(
                By.XPATH,
                ".//img"
            )
            product_image = product_image_elem.get_attribute("src")
        except Exception:
            product_image = None

        try:
            href = card.get_attribute("href")
            product_link = (
                f"https://www.zeptonow.com{href}"
                if href and href.startswith("/")
                else href
            )
        except Exception:
            product_link = None

        if all([product_price, product_image, product_name, product_quantity, product_link]):
            products.append({
                "name": product_name,
                "quantity": product_quantity,
                "price": product_price,
                "image": product_image,
                "link": product_link
            })

    print(f"Scraped {len(products)} products from Zepto.")
    driver.quit()
    return products
