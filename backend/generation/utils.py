import os
import json

def check_configs(asset_folder):
    """
    Check the asset folder for the presence of a 'config.json' file. If not, create completely new.
    
    If there is a config file, load the configs and add any missing assets to the .json file.
    """
    config_path = os.path.join(asset_folder, 'config.json')
    config = {
        "general": {},
        "assets": []
    }

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = json.load(f)

    asset_types = {
        '.png': 'background_photo',
        '.jpg': 'background_photo',
        '.jpeg': 'background_photo',
        '.mp4': 'background_video',
        '.avi': 'background_video',
        '.mov': 'background_video',
        '.mp3': 'background_audio',
        '.wav': 'background_audio'
    }

    for root, _, files in os.walk(asset_folder):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in asset_types:
                asset = {
                    "asset_type": asset_types[ext],
                    "filename": file
                }
                config["assets"].append(asset)

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)