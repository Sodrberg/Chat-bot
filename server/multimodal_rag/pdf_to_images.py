import fitz
import os
from PIL import Image

def pdf_to_images(pdf_path, output_folder, width=None, height=None):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    # Open the PDF file
    pdf_document = fitz.open(pdf_path)

    # Iterate through each page
    for page_num in range(len(pdf_document)):
        # Get the page
        page = pdf_document[page_num]

        # Set custom dimensions if provided
        zoom_x = width / page.rect.width if width else 1
        zoom_y = height / page.rect.height if height else 1
        mat = fitz.Matrix(zoom_x, zoom_y)

        # Convert page to image with custom dimensions
        pix = page.get_pixmap(matrix=mat)

        # Save image
        image_path = os.path.join(output_folder, f"page_{page_num + 1}.png")
        pix.save(image_path)

        # Open the saved image to get its dimensions
        with Image.open(image_path) as img:
            print(f"Page {page_num + 1} dimensions: {img.size[0]}x{img.size[1]} pixels")

    # Close the PDF document
    pdf_document.close()

    print(f"PDF pages converted to images and saved in {output_folder}")

# Example usage

