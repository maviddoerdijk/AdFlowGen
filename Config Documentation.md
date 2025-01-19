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
