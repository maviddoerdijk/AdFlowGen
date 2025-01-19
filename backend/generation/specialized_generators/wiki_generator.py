"""
Goal of this generator: take contents from any wikipedia page, and generate a video with the contents.


Contents of the script:
1. 1 minute of introduction to why this explanation is important
2. 
"""
from backend.generation.voiceover import generate_voiceover
from backend.generation.main import generate_assets
import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI
from typing import Dict
import os
import json



def generate_wiki_assets(asset_folder, wikipedia_url):
    ## Step 1: Get the written voice-over script for the complete youtube video
    # Gather the contents of the wikipedia page
    all_text, all_imgs = scrape_wiki_page(wikipedia_url)   
    
    total_img_ids = list(all_imgs.keys())
    voiceover_info = generate_wiki_voiceover_info(all_text, total_img_ids)     
    
    files_to_generate = []
    img_ids = [image for sublist in voiceover_info['images'].values() for image in sublist]   
    for id in img_ids:
        if not id in all_imgs:
            continue
        src = all_imgs[id]['src']
        files_to_generate.append((id, src))
    
    
    ## Step 2: Generate the voice-over using ElevenLabs
    # Generate the voice-over script
    audio_path, subtitle_path, voiceover_duration = generate_voiceover(voiceover_info['total_transcript'], output_folder = asset_folder)
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    


    
    ## Step 3: Generate the config.json file for the video
    # Let chatGPT generate config.json file
    generate_wiki_config(asset_folder, files_to_generate, voiceover_duration, srt_content)
    
    # Step 3.1: Add some manual config.json changes
    with open(f"{asset_folder}/config.json", "r") as f:
        config = json.load(f)
        
    assets_to_add_end = [
      {
        "generation_method": "from_stlib",
        "filename": "bg_img_black_grid.jpg",
        "asset_type": "background_photo"
      },
      {
        "generation_method": "from_stlib",
        "filename": "thanks_for_watching.mp4",
        "asset_type": "overlay_video"
      }
    ]
    
    assets_to_add_beginning = [
      {
        "generation_method": "from_stlib",
        "filename": "intro.mp4",
        "asset_type": "overlay_video"
      }
    ]
    
    for asset in assets_to_add_end:
        config['assets'].append(asset)  
    
    for asset in assets_to_add_beginning:
        config['assets'].insert(0, asset)
        
    with open(f"{asset_folder}/config.json", "w") as f:
        json.dump(config, f, indent=4)

    
    ## Step 4: Gather remaining assets (downloading images, videos, etc) for the video based on the config.json file
    generate_assets(asset_folder)
    
    
def generate_wiki_voiceover_info(all_text, img_ids):  
    """
    Specifically generate the voice-over script for the wikipedia video with custom prompt for it, etc.
    """ 
    prompt = f"""
    Total wikipedia page contents:
```
{all_text}
```

All available img_identifier variables:
```
{img_ids}
```

Based on these contents, write a script explaining the complete wikipedia page in a compelling youtube video format, focusing on intriguing and educating the listener. 

Script Format with chapters:
```
Opening Hook (10 sentences):
* Start with a powerful statement, question, or fact to grab the audience’s attention.
* Emphasize why the topic matters and why people should care.
Introduction (20 sentences):
* Briefly introduce the topic with clear, easy-to-understand language.
* Set up the key questions or themes to explore.
Context and Background (20 sentences):
* Provide historical context or foundational information.
* Highlight significant events, causes, or developments leading to the current situation.
Current Situation (20 sentences):
* Describe the latest developments or ongoing issues.
* Include statistics, expert perspectives, or examples to add depth.
Why It Matters (10 sentences):
* Explain the broader significance of the topic.
* Address its impact on people, communities, or the global landscape.
Challenges and Solutions (10 sentences):
* Present obstacles or problems.
* Offer potential solutions, actions, or what’s being done.
Call to Action / Closing (10 sentences):
* Leave viewers with a thought-provoking question or action point.
* End with a powerful conclusion that reinforces the importance of the topic.
```

Along all img_identifier variables, see if any of them seem to have to do with that chapter's contents and add it to the answer if that is the case
    """
    
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
            "name": "wiki_voiceover_info",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                "transcriptions": {
                    "type": "object",
                    "properties": {
                    "opening_hook": {
                        "type": "string",
                        "description": "The opening hook of the voice-over script."
                    },
                    "introduction": {
                        "type": "string",
                        "description": "The introduction segment of the voice-over script."
                    },
                    "context_and_background": {
                        "type": "string",
                        "description": "Background context of the topic for the voice-over script."
                    },
                    "current_situation": {
                        "type": "string",
                        "description": "Details on the current situation in Myanmar for the voice-over script."
                    },
                    "why_it_matters": {
                        "type": "string",
                        "description": "Explanation of why the topic matters in the voice-over script."
                    },
                    "challenges_and_solutions": {
                        "type": "string",
                        "description": "Challenges and potential solutions related to the topic in the voice-over script."
                    },
                    "call_to_action": {
                        "type": "string",
                        "description": "Call to action at the end of the voice-over script."
                    }
                    },
                    "required": [
                    "opening_hook",
                    "introduction",
                    "context_and_background",
                    "current_situation",
                    "why_it_matters",
                    "challenges_and_solutions",
                    "call_to_action"
                    ],
                    "additionalProperties": False
                },
                "images": {
                    "type": "object",
                    "properties": {
                    "opening_hook": {
                        "type": "array",
                        "description": "Image identifiers related to the opening hook.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "introduction": {
                        "type": "array",
                        "description": "Image identifiers related to the introduction.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "context_and_background": {
                        "type": "array",
                        "description": "Image identifiers related to the context and background.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "current_situation": {
                        "type": "array",
                        "description": "Image identifiers related to the current situation.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "why_it_matters": {
                        "type": "array",
                        "description": "Image identifiers related to why the topic matters.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "challenges_and_solutions": {
                        "type": "array",
                        "description": "Image identifiers related to challenges and solutions.",
                        "items": {
                        "type": "string"
                        }
                    },
                    "call_to_action": {
                        "type": "array",
                        "description": "Image identifiers related to the call to action.",
                        "items": {
                        "type": "string"
                        }
                    }
                    },
                    "required": [
                    "opening_hook",
                    "introduction",
                    "context_and_background",
                    "current_situation",
                    "why_it_matters",
                    "challenges_and_solutions",
                    "call_to_action"
                    ],
                    "additionalProperties": False
                },
                "total_transcript": {
                    "type": "string",
                    "description": "The complete transcript combining all sections of the voice-over script."
                }
                },
                "required": [
                "transcriptions",
                "images",
                "total_transcript"
                ],
                "additionalProperties": False
            }
            }
        },
    )
    response = completion.choices[0].message.content
    response_json = json.loads(response)

    # response_json = {"transcriptionsopening_hook":"Imagine a country where the single longest-running civil war still rages on— a nation where ethnic factions vie for rights and identities seemingly forgotten by history. Welcome to Myanmar, a land steeped in beauty but drowned in strife. Yet, amidst the chaos, the resilience of its people echoes the promise of change. Why should the world pay heed to this Southeast Asian spectacle? Because Myanmar's conflict is a crude mosaic of our global challenges, intertwining ethnicity, geopolitics, religion, and human rights in a saga that resonates far beyond its borders.","introduction":"Myanmar, a nation of unparalleled scenic landscapes, harbors a less picturesque reality. Formerly known as Burma, this Southeast Asian country's struggle is rooted in its complex ethnic mosaic and political unrest. Post-independence dreams in 1948 rapidly crumbled into the world's longest civil war. With the military, known as the Tatmadaw, entrenched in power over decades and the recent 2021 coup, Myanmar is a dynamic theater of conflict, resistance, and resilience. Throughout its journey, Myanmar raises crucial questions of sovereignty, ethnic diversity, democracy, and the power of institutions.","context_and_background":"At the heart of the Myanmar narrative lies the turbulent transition from British colonial rule to an unending internal conflict. The erstwhile British colony stepped into independence cloaked in potential but laden with fractures. Prominent leader Aung San's assassination derailed dreams of inclusivity for ethnic minorities, culminating in reneged promises like those in the Panglong Agreement.\n\nMilitary coups in 1962 and 1988 reshaped the political landscape, consolidating military power and sidelining ethnic autonomy movements. Over the decades, the Tatmadaw's dominance faced fierce ethnic insurgencies, most notably from the Kachin, Karen, and Shan groups. The tragic 1988 uprising saw a violent crackdown and briefly highlighted the revolutionary spark within Burma, while the new millennium spurred hope with limited political reforms before the cycle of conflict circled back. encapsulates the effect of failed peace negotiations during Ne Win's regime, leading many back to rebel bases.","current_situation":"Today, Myanmar is embroiled in a state of flux. The February 2021 military coup shattered the fledgling democracy after a decade-long honeycomb of reforms. Popular resistance swelled into nationwide protests with protesters arming themselves and insurgent groups resuming offensives against the Tatmadaw.\n\nEthnic armed groups, like the Kachin Independence Army and the Karen National Union, have bolstered the civilian resistance, with the newly-formed People's Defense Force fighting to restore democratic governance. Yet, internal displacement, political imprisonment, and human rights abuses punctuate everyday life as international actors oscillate between sanctions and mediations. They exemplify the role and impact of ethnic groups on the ground.","why_it_matters":"Myanmar's turmoil garners global attention due to its multifaceted impact. Human rights violations, like those against the Rohingya minority, highlight international legal and ethical imperatives. In pursuit of democratization and autonomy, the cries of Myanmar echo complex challenges faced worldwide.\n\nIt's a locus for regional power dynamics, with China, India, and ASEAN juggling trade interests and political influence. Moreover, Myanmar serves as a poignant narrative on identity, challenging ethnic and religious reconciliations amidst globalization. Understanding its journey, challenges, and aspirations offers insights into confronting similar trajectories globally. This sheds light on widespread internal conflict and its variables.","challenges_and_solutions":"Navigating Myanmar's quagmire of challenges involves addressing entrenched ethnic divisions, military authoritarianism, and stalled reforms. Diplomatic engagement, international pressure, and regional cooperation are instrumental, albeit fraught with complexity.\n\nProposals for federalism and inclusive dialogues echo the people's aspirations for unity amidst diversity. While the path ahead is fraught with challenges, grassroots activism coupled with international advocacy continues to illuminate alternatives for peace-building. What you see here represents figures emblematic of enduring resilient leadership amidst political turmoil.","call_to_action":"In closing, Myanmar's narrative implores all to reflect on the universal pursuit of peace, identity, and the struggle for democracy. In a shrinking world marked by interdependencies, the ongoing strife in Myanmar serves as a clarion call for collective empathic action. Will the global community intervene with discerning wisdom to alleviate the Myanmar quagmire? Can we learn to champion an approach where freedom and peace are shared entitlements, and not dormant idealisms confined by geography? The image embodies the urgency and advocacy for harmonious coexistence amidst prevailing tensions."},"images":{"opening_hook":[],"introduction":[],"context_and_background":["they_have_gone_back"],"current_situation":["cadets_of_the_kachin","a_knla_medic_treatsidpsinhpapun"],"why_it_matters":["map_of_insurgent_activity"],"challenges_and_solutions":["state_counselloraung_san_suu"],"call_to_action":["stop_civil_war_in"]}}
    voiceover_script = ""
    for key, value in response_json['transcriptions'].items():
        voiceover_script += value + "\n\n"
        
    response_json['total_transcript'] = voiceover_script
        
    return response_json

def generate_wiki_config(current_asset_folder: str, files_to_generate: list, voiceover_duration: int, srt_content: str) -> Dict:
    files_gathered = os.listdir(current_asset_folder)
    
    total_video_duration = voiceover_duration + 12 # 12 seconds for intro and outro videos
    
    documentation_as_str = """
# Configuration File Format

The `config.json` file is used to specify the assets and general settings for combining them into a video ad creative. Below is the detailed format of the configuration file.

## File Structure

The configuration file must be a JSON object with the following top-level keys:

- `general`: Contains general settings for the video.
- `assets`: A list of asset configuration objects.

### Example

```json
{
  "general": {
    "max_duration_seconds": 60
  },
  "assets": [
    {
      "asset_type": "background_video",
      "filename": "video1.mp4"
    },
    {
      "asset_type": "background_photo",
      "filename": "image1.jpg",
      "duration": 10
    },
    {
      "asset_type": "voiceover",
      "filename": "voiceover.mp3"
    },
    {
      "asset_type": "background_audio",
      "filename": "background_music.mp3"
    },
    {
      "asset_type": "subtitle",
      "filename": "subtitles.srt"
    },
    {
      "asset_type": "gif_animation",
      "filename": "animation.gif",
      "position": [0.5, 0.5]
    },
    {
      "generation_method": "direct_image_url",
      "image_identifier": "map_of_insurgent_activity",
      "src": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Burma1989.png/190px-Burma1989.png",
      "filename": "map_image.png"
    }
  ]
}
```

## General Settings

### `general`

- **`max_duration_seconds`** (optional): Maximum duration of the final video in seconds. If not provided, the video will use the combined duration of the background assets.

## Asset Configuration

Each object in the `assets` array describes an individual asset. The following keys are supported:

### Common Keys

- **`asset_type`** (required): Type of the asset. Supported values:

  - `background_video`
  - `background_photo`
  - `overlay_video`
  - `overlay_photo`
  - `voiceover`
  - `background_audio`
  - `subtitle`
  - `gif_animation`

Important: Every asset in the config.json MUST have an asset_type without exceptions.

- **`filename`** (required): Name of the asset file located in the specified `asset_folder`. This must be relative to the `config.json` file's location.

## Additional Generation Methods

Important note about generation methods: the defined asset must also have an asset_type, without exception.

### `direct_image_url`

Allows downloading an image from a specified URL. This method is useful for assets where you already have a direct URL to the image.

- **Additional Keys**:
  - `image_identifier` (required): A unique identifier for the image (e.g., `map_of_insurgent_activity`).
  - `src` (required): URL of the image to download.
  - `filename` (required): The name to save the image as, relative to the asset folder.

### Example

```json
{
  "generation_method": "direct_image_url",
  "image_identifier": "map_of_insurgent_activity",
  "src": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b8/Burma1989.png/190px-Burma1989.png",
  "filename": "map_image.png"
}
```

### `stock_video`

Downloads a stock video based on a search term.

- **Additional Keys**:
  - `search_term` (required): The search term for finding the video.
  - `filename` (required): The name to save the video as.

### `stock_photo`

Downloads a stock image based on a search term.

Note: search_term must be a physical object like 'playground', and can never be a concept like 'fun' or 'playing'

- **Additional Keys**:
  - `search_term` (required): The search term for finding the image.
  - `orientation` (optional): Orientation of the image (`landscape` or `portrait`). Defaults to `landscape`.
  - `filename` (required): The name to save the image as.

### `website_picture`

Generates a screenshot of a specified website.

- **Additional Keys**:
  - `website_url` (required): The URL of the website to capture.
  - `filename` (required): The name to save the screenshot as.

### `voice`

Generates a voiceover from provided text.

- **Additional Keys**:
  - `text` (required): The text to generate the voiceover from.
  - `filename` (required): The name to save the voiceover as.

### `generate_gif_animation`

Downloads a GIF animation based on a search term or URL.

- **Additional Keys**:
  - `filename` (required): The name to save the GIF as.

### `from_stlib`

Copies a file from the standard library (`stlib`).

- **Additional Keys**:
  - `filename` (required): The name of the file to copy.

### `subtitle_from_existing_audio`

Generates subtitles from an existing audio file.

- **Additional Keys**:
  - **Not yet implemented**.

## Behavior with Multiple Background Assets

When multiple background assets (e.g., videos and photos) are included in the `assets` array, they are processed in the order they appear:

1. **Sequential Addition**: Each background asset is added to the timeline in sequence. For example:

   - If you specify three `background_video` or `overlay_video` assets followed by one `background_photo` or `overlay_photo`, the videos will play sequentially, followed by the photo.
   - The total duration of the video will be the sum of the durations of the videos and the photo.

2. **Transition**: There are no automatic transitions (e.g., fades) between assets unless manually configured. Each asset starts immediately after the previous one ends.

3. **Duration Limitation**: If `max_duration_seconds` is specified in the `general` settings, the timeline will be trimmed to fit within the specified duration. Assets exceeding this duration will not be included in the final output.

## Notes

1. **File Location**: All files specified in the `filename` field must be placed in the same folder as `config.json` or its subfolders.
2. **Error Handling**: If a file specified in the `filename` field is missing, it will be skipped, and a warning will be logged.
3. **Compatibility**: Ensure that file formats are compatible with MoviePy (e.g., supported video, audio, and subtitle formats).
4. **Preview**: You can enable the `preview` mode in the script to review the video before exporting it.

## Troubleshooting

- If the video fails to generate, check the console logs for warnings or errors about missing files or unsupported formats.
- Make sure `max_duration_seconds` is not shorter than the combined duration of your background assets.

---

By adhering to this format, you can efficiently configure the assets for your video generation process.
    """
    
    
    client = OpenAI()
    completion = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "system",
        "content": [
            {
            "type": "text",
            "text": f"Config documentation:\n\n` ` ` {documentation_as_str}  ` ` `\n\n"
            }
        ]
        },
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": f"List of files already gathered:\n ` ` `{files_gathered} ` ` `\n\nList of files we still have to generate with a generation_method:\n ` ` `{files_to_generate} ` ` `\n\n\n  Script based on which images must be accompanied:  ` ` `  {srt_content}  ` ` `\n\n\n      Based on all that information, create a complete config.json file, complying with the following requirements:\n* with the durations of images and videos set such that it exactly matches the total duration of {total_video_duration} seconds\n* use ALL assets\n* Images may not have a duration longer than 7 seconds each\n*For extra images, use generation method 'stock_photo' with images that make sense at that point of the video (e.g. 'man in black and white suit' search term for when talking about the president, or the search term 'poker chips and cards' for when talking about 'gambling' rather than simply the search term 'gambling' or the search term 'person alone' rather than 'real world anxiety')\n*ALL assets must have an 'asset_type' without exceptions.\n*The asset_type of all added images is overlay_photo\n*If the max duration is 335 seconds, then there should be in total 335/7 = 47 images defined in the config.json file"
             }
        ]
        },
    ],
    response_format={
        "type": "json_object"
    },
    )
    
    # save wiki config to asset folder as config.json
    with open(f"{current_asset_folder}/config.json", "w") as f:
        response_content = completion.choices[0].message.content
        parsed_json = json.loads(response_content)
        json.dump(parsed_json, f, indent=4)
    
def scrape_wiki_page(wikipedia_url):
    response = requests.get(wikipedia_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract all paragraphs
    paragraphs = soup.find_all('p')
    all_text = ""
    for paragraph in paragraphs:
        all_text += paragraph.text + "\n"   
    
    all_imgs = {} # save dicts with 'caption' and 'src'
    # Extract all https://upload.wikimedia.org/ images
    images = soup.find_all('img', src=re.compile(r'https://upload.wikimedia.org/'))
    links = soup.find_all('a', href=re.compile(r'https://upload.wikimedia.org/'))
    # find all text in general containing https://upload.wikimedia.org/
    wikimedia = soup.find_all(href=re.compile(r'https://upload.wikimedia.org/'))
    
    # find all text containing /wiki/File
    wikifiles = soup.find_all(href=re.compile(r'/wiki/File'))    
    
    for wikifile in wikifiles:
        # Extract caption from the 'alt' attribute of the <img> tag
        img_tag = wikifile.find('img')
            
        if img_tag:
          if img_tag.has_attr('alt'):
            caption = img_tag['alt'].strip()
            caption_short = ' '.join(caption.split()[:7])
            img_identifier = caption_short.replace(' ', '_').replace('.', '').replace(',', '').replace("'", '').replace('"', '').replace(":", '').replace(";", '').lower()
          else:
            if wikifile.has_attr('href'):
              # get identifier from href of form
              # /wiki/File:20140114_Hwang_Dong-hyuk.jpg
              href = wikifile['href']
              img_identifier = href.split(':')[-1].split('.')[0]
            else:
              # likely not an image in this case
              continue
          if img_tag.has_attr('src'):
            src = f"https:{img_tag['src']}"
          else:
            continue
        # Add the data to the dictionary
        if img_identifier:  # Ensure identifier isn't empty
            all_imgs[img_identifier] = {'caption': caption, 'src': src}
    return all_text, all_imgs