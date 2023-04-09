# this is main, run this

import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image
import os
import turtle

from ImageProcessor import *

MAX_DIMENSION = 500
treatments = [
    "BW",
    "Gaussian",
    "Laplacian Adj",
    "Laplacian All",
    "Lap Adj to GCode",
    "Lap Adj to GCode plus purge",
]


# Resizes the image and puts it in the right format for Tkinter. dwabtit
def formatImage(image):
    width, height = image.size
    if width > height:
        image = image.resize((MAX_DIMENSION, int(height / (width / MAX_DIMENSION))))
    else:
        image = image.resize((int(width / (height / MAX_DIMENSION)), MAX_DIMENSION))
    image = ImageTk.PhotoImage(image)
    return image


# Updates image when a new one is selected, called by dropdown listener
def updateInputImage(imageName):
    inputImage = Image.open(f"Images/{imageName}")
    inputImage = formatImage(inputImage)
    inputImageLabel.config(image=inputImage)
    inputImageLabel.image = inputImage


def runTurtle():
    t = turtle.Turtle()
    t.speed(0)
    t.ht()
    t.up()
    turtle.delay(0)
    turtle.screensize(1024, 1024)

    t.clear()
    with open("Output/turtle.txt") as txt:
        a = txt.readlines()
        # delay = False
        for i in a:
            i = i.strip()
            if i == "stop" or i == "end":
                t.up()
            else:
                x, y = map(int, i.split(","))
                t.goto(x - 512, -(y - 512))
                t.down()
    input()


# Runs whatever is selected and displays the output
def submit():
    treatment = treatmentSelection.get()
    image = f"Images/{imageSelection.get()}"

    imageProcessor = ImageProcessor(image)

    roundness = int(textbox.get("1.0", tk.END))
    blurTimes = 2
    minChainLength = 12

    # all the different sorts of treatments
    def BW():
        imageProcessor.greyscale()
    def Gaussian():
        BW()
        for i in range(blurTimes):
            imageProcessor.gaussianBlur()
    def Laplacian_Adj():
        Gaussian()
        imageProcessor.roundColors(roundness)
        imageProcessor.lapAdj()
        imageProcessor.delPix()
    def Laplacian_All():
        Gaussian()
        imageProcessor.roundColors(roundness)
        imageProcessor.lapAll()
        imageProcessor.delPix()
    def Lap_Adj_to_GCode():
        Laplacian_Adj()
        imageProcessor.toGCode()
    def Lap_Adj_to_GCode_plus_purge():
        Lap_Adj_to_GCode()
        imageProcessor.purge(minChainLength)

    if treatment == treatments[0]:
        BW()
    elif treatment == treatments[1]:
        Gaussian()
    elif treatment == treatments[2]:
        Laplacian_Adj()
    elif treatment == treatments[3]:
        Laplacian_All()
    elif treatment == treatments[4]:
        Lap_Adj_to_GCode()
    elif treatment == treatments[5]:
        Lap_Adj_to_GCode_plus_purge()


    # temp
    imageProcessor.image.save("Output/tempoutput.png")

    outputImage = formatImage(imageProcessor.image)
    outputImageLabel.config(image=outputImage)
    outputImageLabel.image = outputImage

    if (treatment == treatments[4]) or (treatment == treatments[5]):
        runTurtle()


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

textbox = tk.Text(window, height=1, width=15)
textbox.grid(column=2, row=2, padx=5, pady=5)
textbox.insert(tk.END, "4")

submitButton = ttk.Button(window, style="Accent.TButton", text="Submit", command=submit)
submitButton.grid(column=3, row=2, padx=5, pady=5)

window.mainloop()
