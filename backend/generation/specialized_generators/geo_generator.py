import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from typing import List, Dict, Union
from openai import OpenAI
import json
import os
from backend.generation.utils import check_configs
import shutil

def plot_europe_descriptions(country_strings: Union[List[str], Dict[str, str]] = None, output_path='geo_europe_descriptions.png'):
    """
    Plots a map of Europe and annotates each country at its centroid with either the country name
    or a user-provided string. The annotated map is saved as 'geo_europe_descriptions.png' by default.
    
    Parameters
    ----------
    country_strings : list of str, dict of form str:str, optional
        A list of strings to annotate each country. Must be the same length as the number of European countries
        in the dataset. If None, the country names will be used.
        Alternatively, a dictionary of the form {country_name: annotation_string} can be provided.
    
    output_path : str, optional
        The path (including filename) where the output image will be saved.
    """

    # Load world data
    # url = "https://www.naturalearthdata.com/downloads/110m-cultural-vectors/"

    # world = gpd.read_file(url)
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
    
    # Filter for Europe only
    europe = world[world['continent'] == 'Europe'].copy()
    
    # If no custom strings provided, use country names
    if country_strings is None:
        country_strings = europe['name'].tolist()
    
    # Validate the length of provided strings
    if len(country_strings) != len(europe):
        raise ValueError("Length of 'country_strings' must match the number of European countries.")
    
    # Add the annotation strings as a new column
    if isinstance(country_strings, dict):
        europe['label'] = europe['name'].map(country_strings)
    elif isinstance(country_strings, list):
        europe['label'] = country_strings
    else:
        raise ValueError("'country_strings' must be a list or a dictionary.")
        
    # Plot the map
    # define colors
    cmap = cm.Reds
    min_rate, max_rate = 2, 2 + len(europe)
    norm = mcolors.Normalize(vmin=min_rate, vmax=max_rate)
    
    fig, ax = plt.subplots(figsize=(15, 10))
    europe.plot(ax=ax, color='white', edgecolor='black', norm=norm, cmap=cmap)
        
    lower_fontsizes = [
        "Slovenia",
        "Croatia",
        "Bosnia and Herz.",
        "Serbia",
        "Montenegro",
        "North Macedonia",
        "Albania",
        "Bulgaria",
        "Moldova",
        "Kosovo"
    ]
    
    # Annotate each country at its centroid
    # Note: Centroid calculations are in the map's current CRS (usually EPSG:4326 for naturalearth)
    # For labeling purposes, this is typically fine, but if needed, consider projecting first.
    for idx, row in europe.iterrows():
        centroid = row.geometry.centroid
        x, y = centroid.x, centroid.y
        a = row['name']
        if row['name'] == 'France':
            x, y = 2, 47
        if row['name'] == 'Russia':
            x, y = 38, 58
        if row['name'] in lower_fontsizes:
            fontsize = 7  
        else:
            fontsize = 11
        ax.text(x, y, row['label'], fontsize=fontsize, ha='center', va='center', fontweight='bold', color='black')
    
    aspect_ratio = 2.41
    height = 45    
    width = height * aspect_ratio
    ax.set_xlim(-25, width - 25)
    ax.set_ylim(30, 30 + height)   
    # 1982x1080
    # 1912x1080

    ax.axis('off')
    
    # Save the figure
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    
    
from pydantic import BaseModel

class EuropeAnnotationRequest(BaseModel):
    word: str
    response: Dict[str, str]   
    
def get_europe_annotations(word):
    """
    Returns a dictionary mapping country names to the translation of a given word
    ('dog', 'cat', etc.) into the country's local or most widely spoken language.

    Parameters:
        word (str): The word to be translated into local languages.

    Returns:
        dict: A dictionary where the keys are country names in English and the values are the translations of the word.
    """
    countries = [
        'Russia', 'Norway', 'France', 'Sweden', 'Belarus', 'Ukraine', 'Poland', 'Austria', 
        'Hungary', 'Moldova', 'Romania', 'Lithuania', 'Latvia', 'Estonia', 'Germany', 
        'Bulgaria', 'Greece', 'Albania', 'Croatia', 'Switzerland', 'Luxembourg', 'Belgium', 
        'Netherlands', 'Portugal', 'Spain', 'Ireland', 'Italy', 'Denmark', 'United Kingdom', 
        'Iceland', 'Slovenia', 'Finland', 'Slovakia', 'Czechia', 'Bosnia and Herz.', 
        'North Macedonia', 'Serbia', 'Montenegro', 'Kosovo'
    ]

    prompt = (
        f"Translate {word} into the single official or most widely spoken language (Choose the best single language for each country) "
        "for each of the following European countries, and return a Python dictionary where each key is the country name "
        "in English and the value is the translation in the local language(s). Ensure accurate, concise translations of only the word itself."
        "If a country has multiple widely spoken languages, still provide a single translations using the most important language."
        f"```Countries: {countries}```"
        "Answer in JSON format with only the single best word in the single best language. (no '/', '()' or symbols allowed)"
    )
    client = OpenAI()  # Instantiate OpenAI client
            
    try:
        # Create chat completion using the OpenAI SDK
        completion = client.chat.completions.create(
            model="gpt-4o",  # Use the desired model,
            messages=[
                {"role": "system", "content": "You are a translator that answers in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                "name": "country_annotation_list",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                    "country_annotations": {
                        "type": "array",
                        "description": "A list of dictionaries, each containing information about a country and its associated annotation.",
                        "items": {
                        "type": "object",
                        "properties": {
                            "country_name": {
                            "type": "string",
                            "description": "The name of the country."
                            },
                            "annotation": {
                            "type": "string",
                            "description": "An annotation or comment related to the country."
                            }
                        },
                        "required": [
                            "country_name",
                            "annotation"
                        ],
                        "additionalProperties": False
                        }
                    }
                    },
                    "required": [
                    "country_annotations"
                    ],
                    "additionalProperties": False
                }
                }
            }
        )

        # Extract and parse the response content
        response_content = completion.choices[0].message.content
        
        # Attempt to parse the response as JSON
        as_list = json.loads(response_content)
        
        # rewrite to dict of form {country_name: annotation}
        return {entry['country_name']: entry['annotation'] for entry in as_list['country_annotations']}
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse the OpenAI response as JSON: {e}")
    except Exception as e:
        raise RuntimeError(f"An error occurred while generating the reference: {e}")



def get_country_strings(continent='europe'):
    if continent == 'europe':
        # world = gpd.read_file(url)
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        
        # Filter for Europe only
        europe = world[world['continent'] == 'Europe'].copy()
        
        country_strings = europe['name'].tolist()
    else:
        raise ValueError("Only Europe is supported at the moment.")
    return country_strings



def temp():
    from backend.generation.specialized_generators.geo_generator import plot_europe_descriptions, get_country_strings, get_europe_annotations
    # for wanted_word in ["'dog'", "'cat'", "the country's own name",]:
    general_words  = [
        "love",        # Universal yet nuanced in expression.
        "freedom",     # Core cultural value with varied interpretations.
        "friendship",  # Reflects social relationships.
        "home",        # Carries emotional and physical connotations.
        "dream",       # Connected to aspirations and subconscious.
        "happiness",   # Fundamental but culturally diverse in meaning.
        "forest",      # Key to understanding local nature and history.
        "snow",        # Rich vocabulary in northern countries.
        "moon",        # Gendered in many languages.
        "coffee",      # Deeply embedded in European culture (e.g., fika).
        "family",      # Reflects social structures and priorities.
        "work",        # Different cultural attitudes towards it.
        "holiday",     # Reflects leisure culture.
        "spirit",      # Encompasses emotions, ghosts, and alcohol.
        "light",       # Can relate to physical or metaphorical meaning.
        "bread",       # Staple food with cultural symbolism.
        "river",       # Often central to geography and folklore.
        "flower",      # Reflects local flora and aesthetic values.
        "mountain",    # Important in Alpine and Nordic cultures.
        "silence"      # Different connotations in various cultures.
    ]
    
    weather_words = [
        "rain",          # A common phenomenon with many poetic terms.
        "storm",         # Powerful and dramatic in nature.
        "snowflake",     # Intricate and specific to colder climates.
        "fog",           # Reflecting atmospheric conditions and mystery.
        "thunder",       # Symbolic and sensory.
        "wind",          # Dynamic and evocative of nature's movement.
        "hail",          # Rare but impactful.
        "dew",           # Quiet and delicate, often symbolic.
        "rainbow",       # Universally admired, often tied to myths.
        "sunshine",      # Associated with joy and optimism.
        "shadow",        # Tied to light and mystery.
        "mist",          # Evocative of landscapes and moods.
        "frost",         # Reflecting the cold beauty of nature.
        "ice",           # Versatile and central to colder climates.
        "drought",       # Extreme and impactful phenomenon.
        "lightning",     # Dramatic and visually stunning.
        "cloud",         # Everyday yet poetically significant.
        "temperature",   # A measure, but often nuanced (e.g., "chill").
        "twilight",      # Poetic and tied to time and ambiance.
        "breeze"         # Gentle and soothing natural force.
    ]

    internet_words = [
        "meme",           # Universal internet humor concept.
        "streaming",      # Reflects the rise of platforms like Netflix and Twitch.
        "vlog",           # A central concept in YouTube culture.
        "subscribe",      # Core action in online content consumption.
        "like",           # Social media and content feedback term.
        "viral",          # Reflects content popularity.
        "comment",        # A way for viewers to interact with creators.
        "hashtag",        # Social media categorization tool.
        "selfie",         # Popular internet phenomenon.
        "influencer",     # Social media celebrity term.
        "algorithm",      # Central to how content is recommended online.
        "reaction",       # A popular genre of video content.
        "challenge",      # Internet challenges drive trends.
        "trending",       # Represents what's popular at the moment.
        "collaboration",  # Creators working together.
        "tutorial",       # Popular educational video format.
        "gaming",         # A dominant YouTube content genre.
        "unboxing",       # Product reveal videos.
        "playlist",       # Organizing content for viewers.
        "community",      # Reflects the creator-viewer relationship.
    ]


    scientific_words = [
        "atom",         # Fundamental unit of matter in physics and chemistry.
        "gravity",      # Core concept in physics.
        "energy",       # Universal scientific concept with broad applications.
        "evolution",    # Key idea in biology.
        "cell",         # Basic structural unit of life.
        "gene",         # Foundational concept in genetics.
        "light",        # Central to optics and physics.
        "time",         # Universal yet conceptually diverse.
        "space",        # Integral to astronomy and physics.
        "force",        # Central to Newtonian mechanics.
        "matter",       # Core concept in physics and chemistry.
        "life",         # Defining concept in biology.
        "ecosystem",    # Critical to understanding environmental science.
        "planet",       # Key in astronomy and earth sciences.
        "star",         # Core object of study in astronomy.
        "theory",       # Basis of scientific understanding and methodology.
        "experiment",   # Foundational to the scientific process.
        "quantum",      # Key concept in modern physics.
        "bacteria",     # Central to microbiology and health sciences.
        "climate",      # Critical in environmental and earth sciences.
    ]
    
    taboo_words = [
        "burp",         # The sound and social reaction differ globally.
        "hiccup",       # Common bodily function, but some languages have fun names.
        "sneeze",       # Varies in onomatopoeia and related blessings/curses.
        "toilet",       # Words range from euphemistic to direct.
        "fart",         # Universally embarrassing but humorously named.
        "naked",        # Reflects societal attitudes toward nudity.
        "drunk",        # Culturally specific terms for intoxication.
        "hangover",     # How cultures deal with or describe the aftermath.
        "spit",         # Reflects hygiene and social norms.
        "vomit",        # Vivid or polite terms vary.
        "blush",        # A mix of physical and emotional descriptions.
        "flirt",        # Words and cultural contexts for courtship behaviors.
        "curse",        # Swear words vary greatly in creativity and offensiveness.
        "whistle",      # Associated with amusement or signaling.
        "snore",        # Onomatopoeia and how it's viewed socially.
        "gossip",       # Cultural attitudes towards idle talk.
        "awkward",      # Universally experienced but expressed differently.
        "kiss",         # Varies from romantic to social greetings.
        "wink",         # Friendly, flirtatious, or mischievous in different cultures.
        "cheat"         # Has academic, romantic, and moral implications.
    ]
    
    counting_words = [
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ten"
    ]
    
    controversial_words = [
        "sex",             # A universal yet highly varied topic in its openness.
        "death",           # Reflects cultural attitudes toward mortality.
        "god",             # Central to religion and philosophy.
        "abortion",        # A politically and socially charged term.
        "alcohol",         # Different societal norms around its consumption.
        "money",           # Tied to wealth, power, and taboos about discussing it.
        "drugs",           # Varied legal and cultural attitudes.
        "power",           # Reflects authority and governance.
        "violence",        # Societal acceptance and representation of it.
        "war",             # Central to history and collective memory.
        "shame",           # Deeply tied to moral and cultural norms.
        "sin",             # Religious and ethical connotations.
        "crime",           # Reflects law and justice systems.
        "freedom",         # Contrasting political and personal interpretations.
        "pain",            # Emotional and physical aspects.
        "love",            # Can be controversial in non-traditional contexts.
        "nudity",          # Different levels of acceptance and representation.
        "gender",          # A topic of significant cultural and political debate.
        "marriage",        # Reflects legal, social, and moral views.
        "hell",            # Reflects religious imagery and moral fear.
    ]
    
    fruits = [
        "apple",       # Common and symbolic in many cultures.
        "orange",      # Name often linked to its color.
        "banana",      # Non-native but widely consumed in Europe.
        "grape",       # Essential for wine-making traditions.
        "pear",        # Common yet with regional varieties.
        "peach",       # Associated with softness and sweetness.
        "cherry",      # Symbol of spring and romance.
        "strawberry",  # Popular in desserts and summer culture.
        "blueberry",   # Native to northern climates.
        "raspberry",   # Common in European gardens.
        "plum",        # Important for jams and spirits.
        "lemon",       # Used in Mediterranean cuisine and culture.
        "lime",        # Common in drinks and less so in northern Europe.
        "fig",         # Ancient and symbolic fruit in southern Europe.
        "pomegranate", # Exotic but historically significant.
        "melon",       # Popular in summer and varies regionally.
        "watermelon",  # Summery and universally loved.
        "kiwi",        # Imported but now widely grown.
        "blackberry",  # Found in the wild and widely used.
        "apricot"      # Essential in southern European cuisines.
    ]



    colors = [
        "red",         # Associated with passion, danger, and energy.
        "blue",        # Often symbolizes calmness or sadness.
        "green",       # Represents nature, growth, and prosperity.
        "yellow",      # Linked to happiness, sunlight, and caution.
        "black",       # Carries meanings of mystery, elegance, or mourning.
        "white",       # Represents purity, simplicity, or emptiness.
        "orange",      # Combines warmth and energy.
        "purple",      # Historically associated with royalty and luxury.
        "brown",       # Reflects earthiness and stability.
        "pink",        # Linked to softness, romance, and femininity.
        "gray",        # Neutral and often symbolizes balance or ambiguity.
        "gold",        # Associated with wealth, value, and the divine.
        "silver",      # Linked to technology, sophistication, and the moon.
    ]

    all_lists = [weather_words, internet_words, scientific_words, taboo_words, counting_words, controversial_words, fruits, colors]
    all_list_names = ["weather_words", "internet_words", "scientific_words", "taboo_words", "counting_words", "controversial_words", "fruits", "colors"]
    
    for i, current_list in enumerate(all_lists):
        folder_name = f"Campaign_geo_europe_descriptions_{all_list_names[i]}_01A"
        if not os.path.exists(f"assets/{folder_name}"):
            os.makedirs(f"assets/{folder_name}")
        # add 1 with empty list for an empty map
        plot_europe_descriptions(country_strings=[""] * 39, output_path=f'assets/{folder_name}/11aaaageo_europe_descriptions_empty.png')
        for wanted_word in current_list:
            country_strings = get_europe_annotations(wanted_word)
            plot_europe_descriptions(country_strings=country_strings, output_path=f'assets/{folder_name}/geo_europe_descriptions_{wanted_word}.png')
        # copy file audio.mp3 to folder from assets/stlib/classical_music.mp3
        shutil.copy("assets/stlib/classical_music.mp3", f'assets/{folder_name}/classical_music.mp3')
        
        # copy file thank's for thanks_for_watching.mp4 to folder from assets/stlib/thanks_for_watching.png
        shutil.copy("assets/stlib/thanks_for_watching.mp4", f'assets/{folder_name}/thanks_for_watching.mp4')
        
        # Create a config file for the assets so they can be easily combined later
        check_configs(f"assets/{folder_name}")