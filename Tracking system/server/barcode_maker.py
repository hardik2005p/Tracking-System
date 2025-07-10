import barcode
from barcode.writer import ImageWriter
from PIL import Image

def create_custom_barcode(barcode_data, barcode_type='code128', output_file='barcode.png'):
    """
    Create a custom barcode and save it as an image file.

    :param barcode_data: The data to encode in the barcode
    :param barcode_type: The type of barcode to generate (default is 'code128')
    :param output_file: The output file name (default is 'barcode.png')
    """
    # Get the barcode class based on the type
    barcode_class = barcode.get_barcode_class(barcode_type)
    
    # Create a barcode object
    barcode_obj = barcode_class(barcode_data, writer=ImageWriter())
    
    # Save the barcode as an image file
    barcode_obj.save(output_file)
    
    # Open the generated image and display it (optional)
    img = Image.open(output_file)
    img.show()

# Example usage
barcode_data = 'tray003'
barcode_type = 'code128'  # You can change this to 'ean13', 'ean8', 'upca', etc.
output_file = 'custom_barcode3.png'

create_custom_barcode(barcode_data, barcode_type, output_file)
