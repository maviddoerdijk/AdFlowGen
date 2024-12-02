import os
from pathlib import Path
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    TextClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from typing import List, Dict, Any
import logging

def combine_assets(asset_folder: str, output_filename: str = "output_video.mp4") -> str:
    """
    Combines assets from the specified folder into a single video ad creative.

    Parameters:
    - asset_folder (str): Path to the folder containing asset configuration files.
    - output_filename (str): Name of the output video file.

    Returns:
    - str: Path to the generated video file.
    """

    # Resolve the asset folder path
    asset_path = Path(asset_folder).resolve()

    if not asset_path.exists() or not asset_path.is_dir():
        raise FileNotFoundError(f"The asset folder '{asset_folder}' does not exist or is not a directory.")

    # Load asset configurations
    asset_configs = load_asset_configs(asset_path)

    # Initialize lists to hold different asset types
    background_clips: List[Any] = []
    audio_clips: List[Any] = []
    overlay_clips: List[Any] = []
    subtitle_clips: List[Any] = []

    # Process each asset based on its type
    for config in asset_configs:
        asset_type = config.get('asset_type')
        filename = config.get('filename')
        if filename:
            asset_file = asset_path / filename
            if not asset_file.exists():
                logging.warning(f"Asset file '{filename}' does not exist. Skipping.")
                continue

        if asset_type == 'background_video':
            clip = VideoFileClip(str(asset_file))
            background_clips.append(clip)

        elif asset_type == 'background_photo':
            img_clip = ImageClip(str(asset_file)).with_duration(10)  # Default duration
            background_clips.append(img_clip)

        elif asset_type == 'voice':
            audio_clip = AudioFileClip(str(asset_file))
            audio_clips.append(audio_clip)

        elif asset_type == 'gif_animation':
            gif_clip = VideoFileClip(str(asset_file))  # Resize if necessary
            gif_clip = gif_clip.resized(height=200)
            overlay_clips.append(gif_clip.with_position(("center", "bottom")))

        elif asset_type == 'subtitle':
            subtitles = config.get('subtitles', [])
            for subtitle in subtitles:
                # Create the TextClip with the specified duration
                txt_clip = TextClip(
                    text=subtitle['text'],
                    fontsize=24,
                    color='white',
                    stroke_color='black',
                    stroke_width=2,
                    duration=subtitle['duration']  # Set the duration here
                ).with_position(('bottom'))

                # Set the start time of the subtitle
                txt_clip = txt_clip.with_start(subtitle['start'])

                subtitle_clips.append(txt_clip)

        else:
            logging.warning(f"Unknown asset type '{asset_type}'. Skipping.")

    # Combine background clips
    if background_clips:
        final_background = concatenate_videoclips(background_clips, method="compose")
    else:
        raise ValueError("No background clips found to create the video.")

    # Combine overlay clips
    if overlay_clips:
        final_overlays = CompositeVideoClip([final_background] + overlay_clips)
    else:
        final_overlays = final_background

    # Add subtitles if any
    if subtitle_clips:
        final_with_subtitles = CompositeVideoClip([final_overlays] + subtitle_clips)
    else:
        final_with_subtitles = final_overlays

    # Combine audio clips
    if audio_clips:
        final_audio = concatenate_audioclips(audio_clips)
        final_with_subtitles = final_with_subtitles.with_audio(final_audio)

    # Write the final video to a file
    final_with_subtitles.write_videofile(str(asset_path / output_filename), codec='libx264', audio_codec='aac')

    return str(asset_path / output_filename)

def load_asset_configs(asset_path: Path) -> List[Dict[str, Any]]:
    """
    Loads asset configurations from the asset folder.

    Assumes that asset configurations are stored in a 'config.json' file.

    Parameters:
    - asset_path (Path): Path to the asset folder.

    Returns:
    - List[Dict[str, Any]]: List of asset configuration dictionaries.
    """

    import json

    config_file = asset_path / 'config.json'

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file '{config_file}' not found in the asset folder.")

    with open(config_file, 'r') as f:
        configs = json.load(f)

    return configs.get('assets', [])


if __name__ == "__main__":
    output_video = combine_assets(asset_folder="assets/Campaign_Mock_01A", output_filename="ad_creative.mp4")
    logging.info(f"Video created at: {output_video}")