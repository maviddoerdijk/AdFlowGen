import os
import json
from pathlib import Path
from typing import Dict, Any
import logging
import shutil

from .stock_media import download_stock_video, download_stock_image, download_gif
from .voiceover import generate_voiceover
from .other import download_website_screenshot


def load_config(asset_folder: str) -> Dict[str, Any]:
    """
    Loads the config.json from the specified asset folder.
    """
    asset_path = Path(asset_folder)
    config_file = asset_path / 'config.json'
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file '{config_file}' not found in the asset folder.")
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config

def generate_assets(asset_folder: str):
    """
    Generates or downloads assets as specified in the config.json in the asset folder.
    """
    config = load_config(asset_folder)
    assets = config.get('assets', [])
    asset_path = Path(asset_folder)
    
    # List to hold additional entries to config.json
    additional_entries = []
    
    for asset in assets:
        generation_method = asset.get('generation_method')
        filename = asset.get('filename')
        if filename:
            output_file = asset_path / filename
        
        if generation_method == 'stock_video':
            # Download stock video
            logging.info(f"Downloading stock video '{filename}'...")
            download_stock_video(filename=filename, output_folder=asset_path, search_term=asset.get('search_term'))
        elif generation_method == 'stock_photo':
            # Download stock image
            logging.info(f"Downloading stock image '{filename}'...")
            orientation = asset.get('orientation', 'landscape')
            search_term = asset.get('search_term', '')
            download_stock_image(filename=filename, output_folder=asset_path, search_term=search_term, orientation=orientation)
        elif generation_method == 'website_picture':
            website_url = asset.get('website_url')
            logging.info(f'Generating website image: {website_url}')
            download_website_screenshot(website_url=website_url, output_folder=asset_path, filename=filename)
        elif generation_method == 'voice':
            # Generate voiceover
            text = asset.get('text', 'Sample text for voiceover.')
            logging.info(f"Generating voiceover ...")
            generate_voiceover(text=text, filename=filename, output_folder=asset_path)
        elif generation_method == 'generate_gif_animation':
            # Download gif animation
            logging.info(f"Downloading GIF animation '{filename}'...")
            download_gif(filename=filename, output_folder=asset_path)
        elif generation_method == 'from_stlib':
            # Get from stlib
            logging.info(f"Getting asset from stlib '{filename}'...")
            # copy from assets/stlib to asset_path
            stlib_filepath = Path("assets/stlib") / filename
            shutil.copy(stlib_filepath, output_file)
        elif generation_method == 'generate_voiceover':
            # Generate voiceover and additional subtitle
            voiceover_text = asset.get('voiceover_text', 'Default voiceover text.')
            logging.info(f"Generating voiceover '{filename}'...")
            
            # Base filename for voiceover files
            base_filename = "voiceover"
            audio_file = f"{base_filename}.mp3"
            subtitle_file = f"{base_filename}.srt"

            # Generate the voiceover files
            generate_voiceover(voiceover_text=voiceover_text, output_folder=asset_path, filename_base=base_filename)
            
            # Add generated audio and subtitle files to additional entries
            additional_entries.append({"asset_type": "audio", "filename": audio_file})
            additional_entries.append({"asset_type": "subtitle", "filename": subtitle_file})
        elif generation_method == 'subtitle_from_existing_audio':
            raise NotImplementedError("Subtitle generation from existing audio is not yet implemented.")
        else:
            logging.warning(f"Unknown generation method '{generation_method}'. Skipping.")
            
    # Update the config.json with additional entries after the loop
    if additional_entries:
        config['assets'].extend(additional_entries)
        updated_config_path = Path(asset_folder) / 'config.json'
        with open(updated_config_path, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logging.info(f"Updated config.json with additional entries: {additional_entries}")