# web_control.py
import webbrowser
import time
import os
import urllib.parse
# try to import selenium; if missing we'll fallback
try:
    from selenium import webdriver
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.common.by import By
    EDGE_AVAILABLE = True
except Exception:
    EDGE_AVAILABLE = False

# path to msedgedriver.exe (adjust)
try:
    EDGE_DRIVER_PATH = r"D:\rosyai\msedgedriver.exe"
except Exception as e:
    EDGE_DRIVER_PATH = r"D:\rosyai\msedgedriver32.exe" # default path, adjust if needed

import pyautogui

def search_youtube(query: str):
    q = query.strip()
    if q == "":
        q = "music"
    url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(q)
    webbrowser.open(url)

def _selenium_start_edge(headless=False):
    # return driver or None
    if not EDGE_AVAILABLE:
        return None
    try:
        options = Options()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--user-agent=Mozilla/5.0")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
        service = Service(EDGE_DRIVER_PATH)
        driver = webdriver.Edge(service=service, options=options)
        return driver
    except Exception as e:
        print("Selenium Edge start error:", e)
        return None

def play_first_youtube(use_selenium_first=True, wait=2):
    """
    After you call search_youtube(query), call play_first_youtube() to click the first result.
    This will prefer Selenium if available, otherwise use pyautogui fallback.
    """
    if use_selenium_first and EDGE_AVAILABLE and os.path.exists(EDGE_DRIVER_PATH):
        try:
            # open the same search url in selenium and click first video
            # get latest open windows URL from browser? Instead open search anew for reliability:
            driver = _selenium_start_edge(headless=False)
            # try to reuse query by reading clipboard? Simpler: open YouTube home and rely on DOM search
            # Instead take URL from currently active browser - not trivial, so we open a generic search prompt.
            # For best results, pass query to this function. For now open YouTube homepage and click first video from the trending panel:
            driver.get("https://www.youtube.com")
            time.sleep(2)
            # try to find first video link element
            try:
                first = driver.find_element(By.XPATH, "//ytd-rich-item-renderer//a[@id='thumbnail']")
                href = first.get_attribute("href")
                if href:
                    driver.get(href)
                    return True
            except Exception:
                # fallback: open search manually
                pass
            driver.quit()
        except Exception as e:
            print("selenium play error:", e)
            try:
                driver.quit()
            except Exception:
                pass

    # fallback: pyautogui heuristic:
    # Wait for the search results page to load on your default browser and then click first thumbnail position.
    time.sleep(wait)  # give browser time to load
    # typical first video coordinates for 1920x1080: x~400,y~300, but this depends on window and layout.
    # safer: press Tab multiple times then Enter (often focuses first result)
    try:
        # Try a sequence to focus first video
        pyautogui.press('tab', presses=12, interval=0.08)
        time.sleep(0.15)
        pyautogui.press('enter')
        return True
    except Exception as e:
        print("pyautogui play fallback error:", e)
        return False

def youtube_play_pause():
    # 'k' toggles play/pause on YouTube when player focused.
    try:
        pyautogui.press('k')
        return True
    except Exception:
        return False

def youtube_next():
    # Shift+n (or press '>' on some players) goes to next suggested video
    try:
        pyautogui.hotkey('shift', 'n')
        return True
    except Exception:
        return False

def youtube_seek_forward(sec=10):
    # press right arrow
    try:
        for _ in range(sec//5):
            pyautogui.press('right')
        return True
    except Exception:
        return False