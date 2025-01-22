"""
Goal of this generator: take contents from any wikipedia page, and generate a video with the contents.


Contents of the script:
1. 1 minute of introduction to why this explanation is important
2. 
"""
from backend.generation.voiceover import generate_voiceover
from backend.generation.main import generate_assets
from backend.generation.stock_media import download_images_bing
import requests
from bs4 import BeautifulSoup
import re
from openai import OpenAI
from typing import Dict
import os
import json
import shutil



def generate_wiki_assets(asset_folder, wikipedia_url, target_language):
    ## Step 1: Get the written voice-over script for the complete youtube video
    # Gather the contents of the wikipedia page
    all_text, all_imgs = scrape_wiki_page(wikipedia_url)   
    
    total_img_ids = list(all_imgs.keys())
    voiceover_info = generate_wiki_voiceover_info(all_text, total_img_ids, target_language)     
    
    files_to_generate = []
    img_ids = [image for sublist in voiceover_info['images'].values() for image in sublist]   
    for id in img_ids:
        if not id in all_imgs:
            continue
        src = all_imgs[id]['src']
        files_to_generate.append((id, src))
        
    # Get search term
    search_term = wikipedia_url.split('/')[-1].replace('_', ' ')
    # Get extra files for the video to use from bing
    bing_filepaths = download_images_bing(output_folder=asset_folder, search_term=search_term, limit=40)
    # Copy all the images from the filepaths to the asset folder
    bing_filenames = []
    for index, filepath in enumerate(bing_filepaths, start=1):
        new_filename = f"Bing Image {index}.jpg"
        bing_filenames.append(new_filename)
        new_filepath = os.path.join(asset_folder, new_filename)
        shutil.copy(filepath, new_filepath)     
    
    ## Step 2: Generate the voice-over using ElevenLabs
    # Generate the voice-over script
    audio_path, subtitle_path, voiceover_duration = generate_voiceover(voiceover_info['total_transcript'], output_folder = asset_folder)
    with open(subtitle_path, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    


    
    ## Step 3: Generate the config.json file for the videos
    config = {
      "general": {
          "max_duration_seconds": voiceover_duration + 12, # intro + outro 
      },
      "assets": []
    }
    if voiceover_duration / (len(files_to_generate) + len(bing_filenames) + 1) < 5:
      duration_per_overlay = 5
      max_overlays = voiceover_duration / 5
      total_overlays = 0  
    else:
      duration_per_overlay = voiceover_duration / (len(files_to_generate) + len(bing_filenames) + 1)
      max_overlays = 3000
      total_overlays = 0
    
    config['assets'].extend([
        {
            "asset_type": "voiceover",
            "filename": "voiceover.mp3"
        },
        {
            "asset_type": "subtitle",
            "filename": "voiceover.srt"
        },
        {
            "generation_method": "from_stlib",
            "filename": "intro.mp4",
            "asset_type": "overlay_video"
        }])
      
    
    
    for asset in files_to_generate:
        if total_overlays >= max_overlays:
            break
        config['assets'].append({
            "generation_method": "from_url",
            "url": asset[1],
            "filename": f"{asset[0]}.jpg",
            "asset_type": "overlay_photo",
            "duration": duration_per_overlay
        })
        total_overlays += 1
    for asset in bing_filenames:
      if total_overlays >= max_overlays:
          break
      config['assets'].append({
          "filename": asset,
          "asset_type": "overlay_photo",
          "duration": duration_per_overlay
      })
      total_overlays += 1

    
    config['assets'].append({
          "generation_method": "from_stlib",
          "filename": "bg_img_black_grid.jpg",
          "asset_type": "background_photo",
          "duration": voiceover_duration + 7
    })
    
    config['assets'].append({
          "generation_method": "from_stlib",
          "filename": "thanks_for_watching.mp4",
          "asset_type": "overlay_video"
    })
        
    with open(f"{asset_folder}/config.json", "w") as f:
        json.dump(config, f, indent=4)

    
    ## Step 4: Gather remaining assets (downloading images, videos, etc) for the video based on the config.json file
    generate_assets(asset_folder)
    
    
def generate_wiki_voiceover_info(all_text, img_ids, target_language):  
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

Based on these contents, write a script in {target_language} explaining the complete wikipedia page in a compelling youtube video format, focusing on intriguing and educating the listener. 

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

Only give the content of the script itself in {target_language}
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
                        "description": "The opening hook of the voice-over script in the target language."
                    },
                    "introduction": {
                        "type": "string",
                        "description": "The introduction segment of the voice-over script in the target language."
                    },
                    "context_and_background": {
                        "type": "string",
                        "description": "Background context of the topic for the voice-over script in the target language."
                    },
                    "current_situation": {
                        "type": "string",
                        "description": "Details on the current situation in Myanmar for the voice-over script in the target language."
                    },
                    "why_it_matters": {
                        "type": "string",
                        "description": "Explanation of why the topic matters in the voice-over script in the target language."
                    },
                    "challenges_and_solutions": {
                        "type": "string",
                        "description": "Challenges and potential solutions related to the topic in the voice-over script in the target language."
                    },
                    "call_to_action": {
                        "type": "string",
                        "description": "Call to action at the end of the voice-over script in the target language."
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
              caption = img_identifier
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