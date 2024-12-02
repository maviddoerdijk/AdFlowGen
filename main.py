import logging
from backend.generation.main import generate_assets
from backend.generation.stock_media import download_stock_video, download_stock_image
from backend.generation.other import download_website_screenshot
from backend.generation.voiceover import generate_voiceover

from dotenv import load_dotenv
import os

if __name__ == "__main__":
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    asset_folder = "assets/Campaign_Simpletest_01A"
    generate_assets(asset_folder=asset_folder)
    logging.info(f"Assets generated in folder: {asset_folder}")