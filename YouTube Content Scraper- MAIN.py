import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/Users/harshkapoor/Downloads/Coding/YouTube Scraper/credentials.json", scope)
client = gspread.authorize(creds)

MAX_RETRIES = 3

def navigate_with_retry(driver, url):
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Attempting to load {url} (Attempt {attempt + 1})...")
            driver.get(url)
            WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))  # Wait for the page to load
            print(f"Successfully loaded {url}")
            return
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(5)  # Wait before retrying
    print(f"Failed to load {url} after {MAX_RETRIES} attempts.")

def scrape_youtube_data(sheet_name, url_column=1, start_row=2, subscribers_col=4, videos_col=5, views_col=6, description_col=7, latest_video_col=8, headless=True):
    sheet = client.open("Real Leads - Channel Crawler").worksheet(sheet_name)  # Open specific sheet by name

    # Selenium WebDriver setup with headless option
    # Selenium WebDriver setup with headless option
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--mute-audio")  # Add this line to disable audio
    service = Service("/opt/homebrew/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    urls = sheet.col_values(url_column)[start_row - 1:]  # Start from the specified row

    for idx, url in enumerate(urls, start_row):  # Start at the specified row
        navigate_with_retry(driver, url)
        time.sleep(2)  # Allow additional time for content to load

        # Handle consent form if visible
        try:
            consent_button = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="yDmH0d"]/c-wiz/div/div/div/div[2]/div[1]/div[3]/div[1]/form[2]/div/div/button/span')))
            consent_button.click()
            print("Consent form accepted.")
            time.sleep(2)
        except Exception as e:
            print("No consent form displayed or error handling it:", e)

        # Scrape details using XPath
        try:
            # Subscribers
            try:
                subscribers = WebDriverWait(driver, 20).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[1]'))
                ).text
            except:
                subscribers = "N/A"
                print("Subscribers not found.")

            # Video count
            try:
                videos = driver.find_element(By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-content-metadata-view-model/div[2]/span[3]/span').text
            except:
                videos = "N/A"
                print("Video count not found.")

            # Navigate to "Videos" tab to get the latest video
            try:
                videos_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="tabsContent"]/yt-tab-group-shape/div[1]/yt-tab-shape[2]/div[1]')))
                videos_tab.click()
                time.sleep(2)
                
                # Latest video title
                latest_video_title = driver.find_element(By.XPATH, '//*[@id="video-title"]').text
            except:
                latest_video_title = "N/A"
                print("Latest video title not found.")

            # Navigate to "About" section for description and total views
            try:
                about_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="page-header"]/yt-page-header-renderer/yt-page-header-view-model/div/div[1]/div/yt-description-preview-view-model/truncated-text/button/span/span')))
                about_tab.click()
                time.sleep(2)

                # Description
                try:
                    description = driver.find_element(By.XPATH, '//*[@id="description-container"]/span').text
                except:
                    description = "N/A"
                    print("Description not found.")
                
                # Total view count
                try:
                    views = driver.find_element(By.XPATH, '//*[@id="additional-info-container"]/table/tbody/tr[6]/td[2]').text
                except:
                    views = "N/A"
                    print("View count not found.")

            except Exception as e:
                print("Failed to navigate to About section:", e)

            print(f"Scraped data for {url}: Subscribers={subscribers}, Videos={videos}, Views={views}, Description={description}, Latest Video Title={latest_video_title}")

            # Write data to Google Sheets in customizable columns
            sheet.update_cell(idx, subscribers_col, subscribers)
            sheet.update_cell(idx, videos_col, videos)
            sheet.update_cell(idx, views_col, views)
            sheet.update_cell(idx, description_col, description)
            sheet.update_cell(idx, latest_video_col, latest_video_title)

        except Exception as e:
            print(f"Error scraping data for URL {url}: {e}")

    driver.quit()

# Example usage with custom sheet name, rows, and columns
scrape_youtube_data(
    sheet_name="JSS",  # Specify the name of the sheet you want to use
    url_column=1,         # Column for YouTube URLs (e.g., 2 for column B)
    start_row=1,          # Start from row 2
    subscribers_col=5,    # Column for subscribers data (e.g., column D)
    videos_col=6,         # Column for video count data (e.g., column E)
    views_col=7,          # Column for views data (e.g., column F)
    description_col=8,    # Column for description data (e.g., column G)
    latest_video_col=9,   # Column for latest video title (e.g., column H)
    headless=True        # Set to True for headless mode, False for non-headless mode
)