# ... TODO: implement with https://screenshotlayer.com/
# download_website_screenshot(website_url=website_url, output_folder=asset_path, filename=filename)
# SCREENSHOT_LAYER_API_KEY
# http://api.screenshotlayer.com/api/capture

#     ? access_key = ad10faf599fb597d202984bfe3fc8cce
#     & url = http://google.com
#     & viewport = 1440x900
#     & width = 250

import requests
from pathlib import Path
import logging
import os

def download_website_screenshot(website_url: str, output_folder: str = ".", filename: str = "screenshot.png", viewport: str = "1024x768") -> None:
    """
    Downloads a screenshot of the specified website using the ScreenshotLayer API and saves it to the specified filename.

    Parameters:
        website_url (str): The URL of the website to capture.
        output_folder (str): The directory to save the screenshot in. Defaults to the current directory.
        filename (str): The name of the file to save the screenshot as. Defaults to 'screenshot.png'.
    """
    SCREENSHOT_LAYER_API_KEY = os.getenv("SCREENSHOT_LAYER_API_KEY")
    if not SCREENSHOT_LAYER_API_KEY:
        raise Exception("ScreenshotLayer API Key is not set. Please set it as an environment variable.")
    
    # Build the API request URL
    api_url = "http://api.screenshotlayer.com/api/capture"
    params = {
        'access_key': SCREENSHOT_LAYER_API_KEY,
        'url': website_url,
        'viewport': viewport,  # Default viewport size
        'width': None,  # Default width
    }
    
    # Common Viewports:
    # Device	Viewport
    # iPhone 4 (s)	320x480
    # iPhone 5 (c/s)	320x568
    # iPhone 6	375x667
    # iPhone 6 Plus	414x736
    # iPad (2/Mini/Retina)	1024x768
    # Samsung Galaxy S3, S4, S5	360x640
    # Macbook 13"	1440x900
    # iMac 27"	2560x1440

    try:
        # Make the API request to capture the screenshot
        response = requests.get(api_url, params=params, stream=True)
        if response.status_code == 200:
            # Save the screenshot to the specified file
            output_path = Path(output_folder) / filename
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Screenshot saved to {output_path}")
        else:
            raise Exception(f"ScreenshotLayer API request failed: {response.status_code} - {response.text}")
    except Exception as e:
        logging.error(f"An error occurred while downloading the screenshot: {e}")
        raise
