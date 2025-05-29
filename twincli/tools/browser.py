# twincli/tools/browser.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

# Global browser instance to maintain session
_browser_instance = None

def _get_browser():
    """Get or create browser instance."""
    global _browser_instance
    if _browser_instance is None:
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # Remove headless mode so you can see what's happening
        # options.add_argument("--headless")  # Uncomment for headless mode
        
        try:
            _browser_instance = webdriver.Chrome(options=options)
        except Exception as e:
            return None, f"Failed to start browser: {e}"
    
    return _browser_instance, None

def open_browser_tab(url: str) -> str:
    """Open a URL in browser."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        browser.get(url)
        return f"Successfully opened: {url}"
    except Exception as e:
        return f"Error opening URL: {e}"

def get_page_info() -> str:
    """Get current page title and URL."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        title = browser.title
        url = browser.current_url
        return f"Page: {title}\nURL: {url}"
    except Exception as e:
        return f"Error getting page info: {e}"

def find_elements_by_text(text: str) -> str:
    """Find elements containing specific text."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        # Find elements by partial text
        elements = browser.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
        if not elements:
            return f"No elements found containing text: '{text}'"
        
        results = []
        for i, elem in enumerate(elements[:5]):  # Limit to first 5
            tag = elem.tag_name
            elem_text = elem.text[:50] + "..." if len(elem.text) > 50 else elem.text
            results.append(f"{i+1}. <{tag}>: {elem_text}")
        
        return f"Found {len(elements)} elements containing '{text}':\n" + "\n".join(results)
    except Exception as e:
        return f"Error finding elements: {e}"

def click_element_by_text(text: str) -> str:
    """Click an element containing specific text."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        # Try different strategies
        selectors = [
            f"//button[contains(text(), '{text}')]",
            f"//a[contains(text(), '{text}')]",
            f"//input[@value='{text}']",
            f"//*[contains(text(), '{text}')]"
        ]
        
        element = None
        for selector in selectors:
            try:
                element = WebDriverWait(browser, 2).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                break
            except TimeoutException:
                continue
        
        if element:
            element.click()
            return f"Successfully clicked element containing: '{text}'"
        else:
            return f"No clickable element found with text: '{text}'"
            
    except Exception as e:
        return f"Error clicking element: {e}"

def fill_form_field(field_name: str, value: str) -> str:
    """Fill a form field by name, id, or placeholder text."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        # Try different strategies to find the field
        selectors = [
            f"input[name='{field_name}']",
            f"input[id='{field_name}']",
            f"input[placeholder*='{field_name}']",
            f"textarea[name='{field_name}']",
            f"textarea[id='{field_name}']"
        ]
        
        element = None
        for selector in selectors:
            try:
                element = browser.find_element(By.CSS_SELECTOR, selector)
                break
            except NoSuchElementException:
                continue
        
        if element:
            element.clear()
            element.send_keys(value)
            return f"Successfully filled field '{field_name}' with: {value}"
        else:
            return f"No form field found matching: '{field_name}'"
            
    except Exception as e:
        return f"Error filling form field: {e}"

def take_screenshot(filename: str = None) -> str:
    """Take a screenshot of current page."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        if filename is None:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"
        
        # Save to current directory
        browser.save_screenshot(filename)
        return f"Screenshot saved as: {filename}"
    except Exception as e:
        return f"Error taking screenshot: {e}"

def get_page_text() -> str:
    """Get all visible text from the current page."""
    browser, error = _get_browser()
    if error:
        return error
    
    try:
        # Get page text, limiting to reasonable length
        body_text = browser.find_element(By.TAG_NAME, "body").text
        if len(body_text) > 2000:
            body_text = body_text[:2000] + "\n... (truncated)"
        
        return f"Page text:\n{body_text}"
    except Exception as e:
        return f"Error getting page text: {e}"

def close_browser() -> str:
    """Close the browser."""
    global _browser_instance
    if _browser_instance:
        try:
            _browser_instance.quit()
            _browser_instance = None
            return "Browser closed successfully"
        except Exception as e:
            return f"Error closing browser: {e}"
    else:
        return "No browser instance to close"

# Export the functions for tool registration
browser_tools = [
    open_browser_tab,
    get_page_info,
    find_elements_by_text,
    click_element_by_text,
    fill_form_field,
    take_screenshot,
    get_page_text,
    close_browser
]