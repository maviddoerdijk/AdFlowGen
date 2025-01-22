"""
This script generates wiki assets and combines them into a video file.

Usage:
    python main.py --urls <comma_separated_urls> --target_language <language> --target_script <script> --output_filename <filename>

Example:
    python main.py 
        --urls "https://en.wikipedia.org/wiki/Great_Wall_of_China"\
        --target_language "Amharic"\
        --target_script "ethiopian"\
        --output_filename "result.mp4"
"""

import logging
import os
import argparse
from backend.generation.specialized_generators.wiki_generator import generate_wiki_assets
from backend.combination.main import combine_assets
from dotenv import load_dotenv

def main(urls, target_language, target_script, output_filename):
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    logging.info(f"Generating wiki assets for {urls} in {target_language} using {target_script} script")
    
    for wikipedia_url in urls:
        campaign_id = wikipedia_url.split("/")[-1]
        asset_folder = f"assets/Campaign_{campaign_id}_1A"
        os.makedirs(asset_folder, exist_ok=True)
        generate_wiki_assets(asset_folder=asset_folder, wikipedia_url=wikipedia_url, target_language=target_language)
        combine_assets(asset_folder=asset_folder, output_filename=output_filename, target_script=target_script, preview=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate wiki assets and combine them into a video file.")
    parser.add_argument('--urls', type=str, required=True, help="Comma separated list of Wikipedia URLs")
    parser.add_argument('--target_language', type=str, required=True, help="Target language for the assets")
    parser.add_argument('--target_script', type=str, required=True, help="Target script for the assets")
    parser.add_argument('--output_filename', type=str, required=True, help="Output filename for the combined video")

    args = parser.parse_args()
    urls = args.urls.split(',')

    main(urls, args.target_language, args.target_script, args.output_filename)