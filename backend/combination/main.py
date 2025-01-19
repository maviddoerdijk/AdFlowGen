import os
from pathlib import Path
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    CompositeAudioClip,
    TextClip,
    concatenate_videoclips,
    concatenate_audioclips,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from typing import List, Dict, Any
import logging

def combine_assets(asset_folder: str, output_filename: str = "output_video.mp4", preview=False) -> str:
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
    configs = load_configs(asset_path)
    asset_configs = configs.get('assets', [])
    general_configs = configs.get('general', {})
    max_duration_seconds = general_configs.get('max_duration_seconds', None)

    # Initialize lists to hold different asset types
    background_clips: List[Any] = []
    voiceover_audio_clips: List[Any] = []
    background_audio_clips: List[Any] = []
    overlay_clips: List[Any] = []
    subtitle_clips: List[Any] = []
    
    total_duration_bg = 0
    total_duration_overlay = 0
    
    wanted_width = 1920  
    wanted_height = 1080
    wanted_ratio = wanted_width / wanted_height
    wanted_fps = 24

    # Process each asset based on its type
    for config in asset_configs:
        asset_type = config.get('asset_type')
        if not asset_type:
            # Some assets configs (e.g. "generation_method": "generate_voiceover") are not assets themselves, but instructions for creating assets
            continue
        filename = config.get('filename')
        if filename:
            asset_file = asset_path / filename
            if not asset_file.exists():
                logging.warning(f"Asset file '{filename}' does not exist. Skipping.")
                continue

        if asset_type == 'background_video':
            start_time = total_duration_bg 
            clip = VideoFileClip(str(asset_file)).with_start(start_time)
            if clip.w / clip.h != wanted_ratio:
                if clip.w / clip.h > wanted_ratio:
                    clip = clip.resized(width=wanted_width)
                else:
                    clip = clip.resized(height=wanted_height)
            else:
                if clip.w != wanted_width:
                    clip = clip.resized(width=wanted_width)
            total_duration_bg += clip.duration
            background_clips.append(clip)

        elif asset_type == 'background_photo':
            duration = int(config.get('duration', 5))
            start_time = total_duration_bg
            img_clip = ImageClip(str(asset_file), duration=duration).with_start(start_time) # .with_duration(duration)  # Default duration
            if img_clip.w / img_clip.h != wanted_ratio:
                if img_clip.w / img_clip.h > wanted_ratio:
                    img_clip = img_clip.resized(width=wanted_width)
                else:
                    img_clip = img_clip.resized(height=wanted_height)
            else:
                if img_clip.w != wanted_width:
                    img_clip = img_clip.resized(width=wanted_width)
            img_clip.fps = 24
            background_clips.append(img_clip)
            total_duration_bg += duration
            img_clip = img_clip.with_end(total_duration_bg)
        
        elif asset_type == 'overlay_photo':
            duration = int(config.get('duration', 5))
            start_time = total_duration_overlay
            img_clip = ImageClip(str(asset_file), duration=duration).with_start(start_time) # .with_duration(duration)  # Default duration
            if img_clip.w / img_clip.h != wanted_ratio:
                if img_clip.w / img_clip.h > wanted_ratio:
                    img_clip = img_clip.resized(width=wanted_width)
                else:
                    img_clip = img_clip.resized(height=wanted_height)
            else:
                if img_clip.w != wanted_width:
                    img_clip = img_clip.resized(width=wanted_width)
            img_clip.fps = 24
            img_clip = img_clip.with_position(("center", "center"))
            overlay_clips.append(img_clip)
            total_duration_overlay += duration
            img_clip = img_clip.with_end(total_duration_overlay)
        
        elif asset_type == 'overlay_video':
            duration = int(config.get('duration', 5))
            start_time = total_duration_overlay
            clip = VideoFileClip(str(asset_file)).with_start(start_time)
            if clip.w / clip.h != wanted_ratio:
                if clip.w / clip.h > wanted_ratio:
                    clip = clip.resized(width=wanted_width)
                else:
                    clip = clip.resized(height=wanted_height)
            else:
                if clip.w != wanted_width:
                    clip = clip.resized(width=wanted_width)
            clip = clip.with_position(("center", "center")) 
            overlay_clips.append(clip)
            total_duration_overlay += duration
            clip = clip.with_end(total_duration_overlay)
            

        elif asset_type == 'voiceover':
            audio_clip = AudioFileClip(str(asset_file))
            voiceover_audio_clips.append(audio_clip)
            
        elif asset_type == 'background_audio':
            audio_clip = AudioFileClip(str(asset_file))
            background_audio_clips.append(audio_clip)

        elif asset_type == 'gif_animation':
            gif_position = config.get('position', (0.5, 0.5)) 
            gif_position = tuple(gif_position) # In JSON, position is represented as [0.5, 0.5]
            gif_clip = VideoFileClip(str(asset_file))  # Resize if necessary
            gif_clip = gif_clip.resized(height=200)
            overlay_clips.append(gif_clip.with_position(gif_position))

        elif asset_type == 'subtitle':
            if filename.endswith('.srt'):
                # Parse the .srt file
                # def subtitle_generator(txt):
                #     return TextClip(txt, fontsize=24, color='white', stroke_color='black', stroke_width=2)
                # TODO: Implement a more advanced subtitle generator 
                # with white text with a black border, such as in fireship videos
                # much larger text
                subtitle_generator = lambda text: TextClip(font='C:\\Windows\\Fonts\\arial.ttf', text=text,
                                font_size=72, color='white', method='caption', size=(int(wanted_width*3/4), None), stroke_color='black', stroke_width=2)

                subtitles = SubtitlesClip(str(asset_file), make_textclip=subtitle_generator)
                subtitle_clips.append(subtitles.with_position(("center", "bottom")))
            else:
                logging.warning(f"Unsupported subtitle format in file '{filename}'. Skipping.")
        else:
            logging.warning(f"Unknown asset type '{asset_type}'. Skipping.")

    # Combine background clips
    # TODO: Find a way to more naturally combine video/photo lengths. Idea: max_duration_bg_seconds in general configs
    if background_clips:
        final_background = concatenate_videoclips(background_clips, method="compose")
    else:
        raise ValueError("No background clips found to create the video.")

    # Combine overlay clips
    if overlay_clips:
        final_overlays = CompositeVideoClip([final_background] + overlay_clips) # use_bgclip=True  the first clip in the list should be used as the ‘background’ on which all other clips are blitted
    else:
        final_overlays = final_background

    # Add subtitles if any
    if subtitle_clips:
        final_with_subtitles = CompositeVideoClip([final_overlays] + subtitle_clips)
    else:
        final_with_subtitles = final_overlays
        
    # Combine voiceover and background audio
    if voiceover_audio_clips and background_audio_clips:
        # Combine the voiceover and background audio clips into a composite audio clip
        combined_all_audio = CompositeAudioClip([concatenate_audioclips(voiceover_audio_clips),
                                                concatenate_audioclips(background_audio_clips)])
    elif voiceover_audio_clips:
        # If only voiceover audio clips are available
        combined_all_audio = concatenate_audioclips(voiceover_audio_clips)
    elif background_audio_clips:
        # If only background audio clips are available
        combined_all_audio = concatenate_audioclips(background_audio_clips)
    else:
        # If no audio clips are available, set to None
        combined_all_audio = None

    # Add all audio to final video
    if combined_all_audio:
        combined_all_audio = combined_all_audio.with_end(final_with_subtitles.duration)
        print(f"Clipping duration of background audio: {final_with_subtitles.duration}s")
        final_with_subtitles = final_with_subtitles.with_audio(combined_all_audio)
    
    # Set the final video duration
    if max_duration_seconds:
        final_with_subtitles = final_with_subtitles.with_duration(max_duration_seconds)
        
    if preview:
        preview_clip = final_with_subtitles.resized(height=600)  # Adjust height to fit your screen
        preview_clip.preview(audio=True)
        return
    # Write the final video to a file
    final_with_subtitles.write_videofile(str(asset_path / output_filename), codec='libx264', audio_codec='aac', temp_audiofile='temp-audio.m4a', remove_temp=True)

    return str(asset_path / output_filename)

def load_configs(asset_path: Path) -> Dict[str, List[Dict[str, Any]]]:
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

    return configs


if __name__ == "__main__":
    output_video = combine_assets(asset_folder="assets/Campaign_Simpletest_01A", output_filename="ad_creative.mp4")
    logging.info(f"Video created at: {output_video}")   