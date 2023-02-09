import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image
import os

from ImageProcessor import *

MAX_DIMENSION = 500
treatments = ["BW", "Gaussian", "Laplacian Adj", "Laplacian All"]


# Resizes the image and puts it in the right format for Tkinter. dwabtit
def formatImage(image):
    width, height = image.size
    if width > height:
        image = image.resize((MAX_DIMENSION, int(height / (width / MAX_DIMENSION))))
    else:
        image = image.resize((int(width / (height / MAX_DIMENSION)), MAX_DIMENSION))
    image = ImageTk.PhotoImage(image)
    return image


def updateInputImage(imageName):
    inputImage = Image.open(f"Images/{imageName}")
    inputImage = formatImage(inputImage)
    inputImageLabel.config(image=inputImage)
    inputImageLabel.image = inputImage


def submit():
    treatment = treatmentSelection.get()
    image = f"Images/{imageSelection.get()}"

    imageProcessor = ImageProcessor(image)

    if treatment == treatments[0]:
        # imageProcessor.greyscale()
        imageProcessor.delPix()
        # imageProcessor.roundGrey()
    elif treatment == treatments[1]:
        imageProcessor.gaussianBlur()
    elif treatment == treatments[2]:
        imageProcessor.greyscale()
        imageProcessor.gaussianBlur()
        # imageProcessor.gaussianBlur()
        imageProcessor.round(3)
        imageProcessor.lapAdj()
        imageProcessor.delPix()
    elif treatment == treatments[3]:
        imageProcessor.greyscale()
        imageProcessor.gaussianBlur()
        imageProcessor.gaussianBlur()
        imageProcessor.round(3)
        imageProcessor.lapAdj()
        imageProcessor.delPix()
        imageProcessor.toGCode()

    # temp
    imageProcessor.image.save("Output/tempoutput.png")

    outputImage = formatImage(imageProcessor.image)
    outputImageLabel.config(image=outputImage)
    outputImageLabel.image = outputImage


window = tk.Tk()
window.title("HWA Image Processing GUI")

window.tk.call("source", "azure.tcl")
window.tk.call("set_theme", "light")

inputText = ttk.Label(window, text="Input Image")
inputText.grid(column=0, row=0, columnspan=2, padx=5, pady=5)

outputText = ttk.Label(window, text="Output Image")
outputText.grid(column=2, row=0, columnspan=2, padx=5, pady=5)

inputImageLabel = ttk.Label(window, image=None)
inputImageLabel.grid(column=0, row=1, columnspan=2, padx=5, pady=5)

outputImageLabel = ttk.Label(window, image=None)
outputImageLabel.grid(column=2, row=1, columnspan=2, padx=5, pady=5)

imageSelection = tk.StringVar()
imageMenu = ttk.OptionMenu(
    window,
    imageSelection,
    "Select image",
    *os.listdir(r"Images"),
    style="Accent.TOptionMenu",
    command=updateInputImage,
)
imageMenu.grid(column=0, row=2, padx=5, pady=5)

treatmentSelection = tk.StringVar()
treatmentMenu = ttk.OptionMenu(
    window,
    treatmentSelection,
    "Select treatment",
    *treatments,
    style="Accent.TOptionMenu",
)
treatmentMenu.grid(column=1, row=2, padx=5, pady=5)

submitButton = ttk.Button(window, style="Accent.TButton", text="Submit", command=submit)
submitButton.grid(column=3, row=2, padx=5, pady=5)

window.mainloop()
