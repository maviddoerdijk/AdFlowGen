filename = 'stock_image.jpg'
orientation = 'landscape'
search_term = 'white house'
asset_path = ''

from backend.generation.stock_media import download_stock_image
from dotenv import load_dotenv
load_dotenv()

download_stock_image(filename=filename, output_folder=asset_path, search_term=search_term, orientation=orientation)