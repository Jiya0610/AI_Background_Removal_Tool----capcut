# Clearcut — AI Background Remover

A local Streamlit application that removes image backgrounds with the pretrained U²-NetP model via `rembg`. It supports transparent PNG exports and color or image background replacement.

## Run locally

Python 3.10–3.12 is recommended.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

The first background-removal run downloads model weights and therefore needs an internet connection. The app does not save uploaded images or results to disk. Model weights are cached by `rembg` in its normal user cache.

## Features

- JPG/JPEG/PNG validation, readable-image checks, upload-size and pixel limits
- EXIF orientation correction and RGB decoding
- OpenCV aspect-preserving downscaling for inference, with original dimensions retained in exports
- Cached U²-NetP model session and `rembg` foreground mask generation
- Draggable before/after reveal comparison and inspectable foreground mask
- Adjustable edge softness without rerunning AI inference
- Transparent PNG, customized PNG, and JPEG downloads
- Solid-color presets, custom colors, two-color gradients, and uploaded-image backgrounds
- Processing duration, errors, and reset/upload-another-image control
- Light theme with responsive styling and animated hover, focus, and press states

## Limits

- Input: JPG/JPEG or PNG, at most 20 MB
- Dimensions: at most 12,000 pixels per side and 40 million pixels total
- Model inference: longest side capped at 2,000 pixels to manage memory
- Background images: JPG/PNG up to 10,000 pixels per side

Segmentation quality depends on the input image and model. The app does not claim a measured accuracy score.
