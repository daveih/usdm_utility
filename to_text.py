import os
import argparse
from PIL import Image
from pytesseract import pytesseract

# See https://www.nutrient.io/blog/how-to-use-tesseract-ocr-in-python/

def save_text(file_path, data):
    with open(file_path, "w") as f:
        f.write(data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='USDM Simple Text from Images Program',
        description='Will display text exracted from image',
        epilog='Note: Not that sophisticated! :)'
    )
    parser.add_argument('filename', help="The name of the image file.") 
    args = parser.parse_args()
    filename = args.filename
    
    input_path, tail = os.path.split(filename)
    if not input_path:
        input_path = os.getcwd()
    root_filename, file_extension = os.path.splitext(filename)
    full_input_filename = os.path.join(input_path, tail)
    full_output_filename = os.path.join(input_path, f"{root_filename}.txt")

    print(f"Input filename:  {full_input_filename}")
    print(f"Output filename: {full_output_filename}")

    image = Image.open(full_input_filename)
    extracted_text = pytesseract.image_to_string(image)
    save_text(full_output_filename, extracted_text)

