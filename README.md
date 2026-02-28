# HuntTheMouse Pixel Grid Generator

This repo performs OCR on a folder of images containing pixel hints, validates the extracted pixel tuples, and reconstructs a 32×32 image based on those hints.

## Features

- Separates broken and valid hints
- Logs malformed tuples and OCR errors
- Allows users to manually fix broken hints via fixed_hints.txt
- Detects and logs pixel overwrites
- Marks conflicting overwrites in magenta (255, 0, 255) in the final image

---

# Dependencies

## Python Version

- Python 3.8 or higher recommended

## Required Python Packages

Install with:

    pip install pillow pytesseract opencv-python

### Package Purpose

- Pillow - Image creation and saving  
- pytesseract - OCR text extraction  
- opencv-python - Image preprocessing before OCR  

## Tesseract OCR

This project requires the Tesseract OCR engine.

### Windows Installation

1. Download from:  
   https://github.com/UB-Mannheim/tesseract/wiki

2. Install to:

    C:\Program Files\Tesseract-OCR\

3. Ensure this line in the script matches your install path:

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

If Tesseract is installed elsewhere, update the path accordingly.

---

# Project Structure

    project/
    ├── images/        # Input images for OCR
    ├── output/        # Auto-generated output files
    ├── script.py      # Main script
    └── README.md

---

# Expected OCR Format

Each image should contain exactly 4 pixel tuples formatted like:

    (x, y, #RRGGBB), (x, y, #RRGGBB), (x, y, #RRGGBB), (x, y, #RRGGBB)

Example:

    (12, 5, #FF00AA), (13, 6, #00FFAA), (11, 4, #AAFF00), (15, 6, #AA00FF)

Basically, as long as your image contains the full, clear and uncropped text of a proper pixel hint, it should work without any issues.

---

# Validation Rules

Each image must contain:

- Exactly 4 valid pixel tuples
- Each tuple must match: (number, number, #XXXXXX)
- XXXXXX must be a valid 6-digit hexadecimal color

Coordinates must satisfy:

- 0 ≤ x < 32
- 0 ≤ y < 32

Tuples outside this range are logged as errors.

---

# How to Use

## Step 1 - Add Images

Place all pixel hint images/screenshots inside:

    images/

Supported formats:

- .png  
- .jpg  
- .jpeg  
- .bmp  

## Step 2 - Run the Script

    python script.py

---

# Output Files

All outputs are saved in:

    output/

Files generated:

- all_hints.txt - Raw OCR results  
- fixed_hints.txt - Use this to manually fix your hints for overwrittes or OCR misreads
- errors.txt - OCR and validation errors  
- overwrites.txt - Identical overwrite logs  
- final_coin_image.png - Final reconstructed image  

---

# Overwrite Behavior

If two hints attempt to write to the same pixel:

- Pixel is marked magenta (255, 0, 255)
- Console prints: OVERWRITE at (x,y)

You can then use output/fixed_hints.txt to manually rectify overwrites

---

# Output Statistics

After execution, the script prints:

- Final image location  
- Pixels filled  
- Fill percentage  
- Overwrite count  
- Error log locations  

Example output:

    Image generation complete!
    Saved to: output/final_coin_image.png
    Pixels filled: 128/1024 (12.5%)
    Overwritten pixels (count): 3

---

# Customization

Unforunately, this was purely hardcoded for HuntTheMouse. But feel free to fork this repo and go wild.

If you encounter any common OCR issues, you can make the script automatically replace them by editing

    CHAR_REPLACE = { ... }

---

# Troubleshooting

cv2.imread returned None:
- Incorrect file path  
- Corrupted image  
- Unsupported format  

TesseractNotFoundError:
- Tesseract not installed  
- Incorrect tesseract_cmd path

Wrong pixel color/overwrite:
- Check output/overwrites.txt
- Check output/errors.txt
- Manually rectify errors in output/fixed_hints.txt and regenerate

No pixels filled:
- OCR failed  
- Formatting mismatch  
- All hints categorized as broken  

Check:

    output/errors.txt

---

IKWL!
