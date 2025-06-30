from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import quote
import time
import re
from utils.driver_setup import get_driver

def blinkit_scraper(search_item, progress_callback=None):
    encoded_query = quote(search_item)
    url = f"https://blinkit.com/s/?q={encoded_query}"

    driver = get_driver()
    print(f"Navigating to {url}")
    driver.get(url)

    try:
        location_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//input[@placeholder='search delivery location']")
            )
        )
        location_input.clear()
        location_input.send_keys("Delhi")
        print("Typed Delhi into the location box.")
        time.sleep(2)

        first_option = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "(//div[contains(@class,'LocationSearchList__LocationDetailContainer')])[1]"))
        )
        first_option.click()
        print("Selected the first location option.")
        time.sleep(2)

    except Exception as e:
        print("Could not select location:", e)
        driver.quit()
        return []

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@data-pf='reset' and contains(@style, 'padding: 8px')]")
            )
        )
    except Exception:
        print("No products found.")
        driver.quit()
        return []

    max_scroll_attempts = 6
    scroll_pause_time = 2
    for i in range(max_scroll_attempts):
        try:
            driver.find_element(
                By.XPATH,
                "//div[contains(@class, 'tw-text-400') and contains(@class, 'tw-font-bold') and contains(text(), 'Showing related products')]"
            )
            break
        except NoSuchElementException:
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(scroll_pause_time)
            if progress_callback:
                progress_callback((i + 1) / max_scroll_attempts)

    cards = driver.find_elements(
        By.XPATH, "//div[@data-pf='reset' and contains(@style, 'padding: 8px')]"
    )

    search_keywords = search_item.lower().split()
    products = []

    for i, card in enumerate(cards, start=1):
        try:
            out_of_stock_elem = card.find_element(
                By.XPATH,
                ".//div[contains(text(), 'Out of Stock')]"
            )
            continue
        except NoSuchElementException:
            pass

        try:
            product_name = card.find_element(
                By.XPATH,
                ".//div[contains(@class, 'tw-text-300') and contains(@class, 'tw-font-semibold')]"
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
                ".//div[contains(@class, 'tw-text-200') and contains(@class, 'tw-font-medium')]"
            ).text.strip()
        except Exception:
            product_quantity = None

        try:
            product_price = card.find_element(
                By.XPATH,
                ".//div[contains(@class, 'tw-text-200') and contains(@class, 'tw-font-semibold') and contains(@style,'--colors-black-900')]"
            ).text.strip()
        except Exception:
            product_price = None

        try:
            product_image_elem = card.find_element(
                By.XPATH, ".//img[contains(@class, 'tw-h-full')]"
            )
            product_image = product_image_elem.get_attribute("src")
        except Exception:
            product_image = None

        try:
            product_link_elem = card.find_element(
                By.XPATH, ".//div[contains(@class, 'tw-items-start')]"
            )
            product_link_elem = product_link_elem.get_attribute("id")
            text = product_name.lower() if product_name else ""
            text = re.sub(r'[^a-z0-9]+', '-', text)
            text = text.strip('-')
            product_link = f"https://blinkit.com/prn/{text}/prid/{product_link_elem}"
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

    print(f"Scraped {len(products)} products from Blinkit.")
    driver.quit()
    return products
