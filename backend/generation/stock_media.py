import requests
from pathlib import Path
import logging
import os
import traceback
from pytubefix import YouTube
from pytubefix.cli import on_progress
from bing_image_downloader import downloader
            
def download_stock_video(filename: str, output_folder: str = ".", search_term: str = "") -> None:
    """
    Downloads a sample stock video and saves it to the specified filename.
    """
    search_term = "stock video" + search_term
    video_path = get_youtube_video_from_term(search_term, output_folder, filename)
    logging.info(f"Downloaded video from search term: {search_term} to {video_path}")
            
def get_youtube_video_from_term(search_term: str, output_folder: str, filename: str) -> str:
    video_urls = search_youtube_videos(search_term, max_results=5)
    for url in video_urls:
        success, video_path = download_youtube_video_from_url(url, output_folder, filename)
        if success:
            return video_path
        else:
            logging.warning(f"Failed to download video from URL: {url}. Traceback: {video_path}") 
            
def search_youtube_videos(search_term: str, max_results: int = 5) -> list:
    YOUTUBE_API_KEY = os.environ['YOUTUBE_API_KEY']
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={max_results}&q={search_term}&key={YOUTUBE_API_KEY}&type=video"
    response = requests.get(search_url)
    
    if response.status_code != 200:
        raise Exception(f"Failed to search YouTube videos: {response.text}")
    else:
        response_json = response.json()
        video_ids = [item['id']['videoId'] for item in response_json['items']]
        video_urls = [f"https://www.youtube.com/watch?v={video_id}" for video_id in video_ids]
        return video_urls
        
def download_youtube_video_from_url(url: str, output_folder: str, filename: str) -> tuple:
    try:
        yt = YouTube(url, on_progress_callback = on_progress)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        if video:
            video_path = video.download(output_path=output_folder, filename = filename)
            return True, video_path
    except Exception:
        return False, traceback.format_exc()

def download_stock_image_unsplash(filename: str, output_folder: str = ".", search_term: str = "", orientation: str = "landscape") -> None:
    """
    Downloads the first stock image that matches the search term from Unsplash and saves it to the specified filename,
    enforcing the specified dimensions.
    
    Parameters:
        filename (str): The name of the file to save the image as.
        output_folder (str): The directory to save the image in. Defaults to the current directory.
        search_term (str): The search term to query images. Defaults to an empty string.
        width (int): Desired width of the image.
        height (int): Desired height of the image.
    """
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
    if not UNSPLASH_ACCESS_KEY:
        raise Exception("Unsplash Access Key is not set. Please set it as an environment variable.")

    url = "https://api.unsplash.com/search/photos"
    params = {
        'query': search_term,
        'page': 1,
        'per_page': 1,  # Only fetch one image to simplify the process
        'client_id': UNSPLASH_ACCESS_KEY,
        # \/ Documentation : orientation	Filter by photo orientation. Optional. (Valid values: landscape, portrait, squarish)
        'orientation': orientation  # Ensure landscape images for better fit 
    }

    try:
        # Make the API request to fetch the image
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            
            if results:
                # Get the first image's URL
                image_url = results[0]['urls']['raw']  # Use 'raw' to enforce size

                # Download the image
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    # Save the image to the specified file
                    output_path = Path(output_folder) / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(image_response.content)
                    print(f"Image downloaded and saved to {output_path}")
                    return True
                else:
                    raise Exception(f"Failed to download image from URL: {image_url}")
            else:
                raise Exception("No images found for the given search term.")
        else:
            raise Exception(f"Unsplash API request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred while fetching image: {e}")
        
def download_images_bing(output_folder: str = ".", search_term: str = "", limit: int = 10) -> None:
    """
    Downloads images that match the search term from Bing and saves them to the specified filename,
    enforcing the specified dimensions.

    Parameters:
        filename (str): The name of the file to save the images as.
        output_folder (str): The directory to save the images in. Defaults to the current directory.
        search_term (str): The search term to query images. Defaults to an empty string.
        limit (int): The number of images to download. Defaults to 10.
    """
    # Output folder will be in output_folder/{search_term}
    output_path = Path(output_folder) / "bing_images" # the download() func will automatically save to output_path/{search_term}
    output_path.mkdir(parents=True, exist_ok=True)

    downloader.download(search_term, limit=limit, output_dir=str(output_path), adult_filter_off=True, force_replace=False, timeout=60, verbose=True)
    output_path_saved = Path(output_path) / search_term
    
    filepaths = list(output_path_saved.glob("*.*"))
    return filepaths
        


def download_stock_image_pexels(filename: str, output_folder: str = ".", search_term: str = "", orientation: str = "landscape") -> None:
    """
    Downloads the first stock image that matches the search term from Pexels and saves it to the specified filename,
    enforcing the specified dimensions.

    Parameters:
        filename (str): The name of the file to save the image as.
        output_folder (str): The directory to save the image in. Defaults to the current directory.
        search_term (str): The search term to query images. Defaults to an empty string.
        orientation (str): Desired photo orientation. Options: landscape, portrait, square. Defaults to 'landscape'.
    """
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    if not PEXELS_API_KEY:
        raise Exception("Pexels API Key is not set. Please set it as an environment variable.")

    url = "https://api.pexels.com/v1/search"
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    params = {
        'query': search_term,
        'per_page': 1,  # Only fetch one image to simplify the process
        'orientation': orientation
    }

    try:
        # Make the API request to fetch the image
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            photos = data.get('photos', [])
            
            if photos:
                # Get the first image's URL (original quality)
                image_url = photos[0]['src']['original']

                # Download the image
                image_response = requests.get(image_url)
                if image_response.status_code == 200:
                    # Save the image to the specified file
                    output_path = Path(output_folder) / filename
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, 'wb') as f:
                        f.write(image_response.content)
                    print(f"Image downloaded and saved to {output_path}")
                    return True
                else:
                    raise Exception(f"Failed to download image from URL: {image_url}")
            else:
                raise Exception("No images found for the given search term.")
        else:
            raise Exception(f"Pexels API request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred while fetching image: {e}")
        

def download_gif(filename: str, output_folder: str = ".", url: str = None) -> None:
    """
    Downloads a sample GIF animation and saves it to the specified filename.
    """
    if not url:
        # Use a sample GIF URL
        url = "https://media.giphy.com/media/3o6fJ1BM7osQBajvS0/giphy.gif"
    gif_response = requests.get(url)
    if gif_response.status_code != 200:
        raise Exception(f"Failed to download GIF: {gif_response.text}")
    output_path = Path(output_folder) / filename
    with open(output_path, 'wb') as f:
        f.write(gif_response.content)


