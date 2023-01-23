from PIL import Image, ImageFilter

# Image inputs
astro = "DALLE_Astronaut.jpg"

# Kernels
gaussianK = (1/16, 2/16, 1/16, 2/16, 4/16, 2/16, 1/16, 2/16, 1/16)
lapAdjK = (0, 1, 0, 1, -4, 1, 0, 1, 0)
lapAllK = (-1, -1, -1, -1, 8, -1, -1, -1, -1)

class ImageProcessor:
    def __init__(self, imageIn):
        self.image = Image.open(imageIn)

    def greyscale(self): 
        self.image = self.image.convert("L")

    def gaussianBlur(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), gaussianK, 1, 0))

    def lapAdj(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAdjK, 0.5, 0))

    def lapAll(self):
        self.image = self.image.filter(ImageFilter.Kernel((3, 3), lapAllK, 1, 0))

