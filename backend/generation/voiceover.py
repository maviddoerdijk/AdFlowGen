import os
import base64
from pathlib import Path
import logging
from elevenlabs import ElevenLabs
# Note: there is a bug in elevenlabs where you might get an error due to their pathnames being too long.
# If this occurs, do this (on windows):
# 1. Windows Key + R
# 2. Search for 'regedit'
# 3. Go to Computer\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem
# 4. Change variable LongPathsEnabled from 0 to 1
# 5. Run again

def generate_voiceover(voiceover_text: str, output_folder: str, filename_base: str = "voiceover",
                       max_sentence_length: int = 100, max_seconds_length: float = 5.0):
    """
    Generate a voiceover from text using ElevenLabs Text-to-Speech with timing and save audio and subtitles.

    Parameters:
        voiceover_text (str): The text for the voiceover.
        output_folder (str): The folder where output files should be saved.
        filename_base (str): Base name for the output files (audio and subtitle). Defaults to "voiceover".
    """
    try:
        # Initialize the ElevenLabs client
        client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY'], timeout=400)
        
        # Generate TTS with timing
        response = client.text_to_speech.convert_with_timestamps(
            voice_id="21m00Tcm4TlvDq8ikWAM",  # Replace with your preferred voice ID
            text=voiceover_text,
        )
        
        # Extract audio and timing data
        audio_base64 = response['audio_base64']
        characters = response['alignment']['characters']
        character_start_times = response['alignment']['character_start_times_seconds']
        
        # Define output paths
        audio_path = Path(output_folder) / f"{filename_base}.mp3"
        subtitle_path = Path(output_folder) / f"{filename_base}.srt"
        
        # Save audio file
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        with open(audio_path, 'wb') as f:
            f.write(base64.b64decode(audio_base64))
        logging.info(f"Audio file saved to {audio_path}")
        
        srt_content, voiceover_duration = generate_srt_content(characters, character_start_times, max_sentence_length, max_seconds_length)
        with open(subtitle_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        logging.info(f"SRT file saved to {subtitle_path}")
        
        return audio_path, subtitle_path, voiceover_duration
    
    except Exception as e:
        logging.error(f"An error occurred while generating the voiceover: {e}")
        raise

def generate_srt_content(chars, start_times, max_sentence_length, max_seconds_length):
    """
    Generate SRT content using character timing, max sentence length, and max seconds length.

    Parameters:
        chars (list of str): List of characters.
        start_times (list of float): Start times corresponding to each character.
        max_sentence_length (int): Maximum number of characters in a subtitle.
        max_seconds_length (float): Maximum duration in seconds of a subtitle.
    """
    srt_entries = []
    srt_index = 1
    current_text = ""
    current_start_time = None
    last_end_time = 0.0

    for i, char in enumerate(chars):
        if current_start_time is None:
            current_start_time = start_times[i]
        
        current_text += char
        end_time = start_times[i]
        
        # Check if the current text exceeds limits or is at a natural boundary
        if (
            len(current_text.strip()) > max_sentence_length or
            (end_time - current_start_time) > max_seconds_length or
            char in ".!?…\n"
        ):
            # Adjust timing slightly for natural breaks
            subtitle_end_time = min(end_time + 0.2, start_times[-1])
            
            # Ensure we do not cut words in half
            if len(current_text.strip()) > max_sentence_length:
                last_space_index = current_text[:max_sentence_length].rfind(' ')
                if last_space_index != -1:
                    end_time = start_times[i - (len(current_text) - last_space_index - 1)]
                    current_text = current_text[:last_space_index + 1]
            
            # Add the subtitle entry
            if current_text.strip():
                srt_entries.append(
                    f"{srt_index}\n"
                    f"{format_time(current_start_time)} --> {format_time(subtitle_end_time)}\n"
                    f"{current_text.strip()}\n"
                )
                srt_index += 1

            # Reset for the next subtitle
            current_text = ""
            current_start_time = None if i == len(chars) - 1 else start_times[i + 1]

    # Append the last subtitle if there is remaining text
    if current_text.strip():
        srt_entries.append(
            f"{srt_index}\n"
            f"{format_time(current_start_time)} --> {format_time(start_times[-1] + 0.2)}\n"
            f"{current_text.strip()}\n"
        )
        
    # Get the total duration of the voiceover
    voiceover_duration = start_times[-1] - start_times[0]

    return "\n".join(srt_entries), voiceover_duration


def format_time(seconds):
    """Format time in SRT format (HH:MM:SS,ms)."""
    ms = int((seconds % 1) * 1000)
    total_seconds = int(seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"