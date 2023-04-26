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
        allCommands = txt.readlines()
        # delay = False
        for command in allCommands:
            command = command.strip()
            if command == "stop" or command == "end":
                t.up()
            else:
                x, y = map(int, command.split(","))
                t.goto(x - 512, -(y - 512))
                t.down()
    input()


# Runs whatever is selected and displays the output
def submit():
    treatment = treatmentSelection.get()
    image = f"Images/{imageSelection.get()}"

    imageProcessor = ImageProcessor(image)

    roundness = int(roundnessInput.get("1.0", tk.END))
    blurTimes = int(blurTimesInput.get("1.0", tk.END))
    minChainLength = int(minChainLengthInput.get("1.0", tk.END))

    # all the different sorts of treatments
    def BW():
        imageProcessor.greyscale()
    def Gaussian():
        BW()
        for i in range(blurTimes):
            imageProcessor.gaussianBlur()
    def Laplacian_Adj():
        Gaussian()

        #note: you can use either rounding function
        #imageProcessor.balancedRoundColors(roundness)
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
        imageProcessor.turtlePurge(minChainLength)
        imageProcessor.gcodePurge(minChainLength)
        # note: -1 is just a placeholder value
        # note: LINEJOINER FUNCTION MUST BE USED AFTER PURGE FUNCTION, DO NOT USE BEFORE PURGE FUNCTION
        imageProcessor.lineJoiner(-1)
        imageProcessor.duplicateEraser()

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

# note: change these constants to change the defualt values in the boxes
ROUNDNESS_DEFUALT = "4"
roundnessInputText = ttk.Label(window, text="roundness:")
roundnessInputText.grid(column=0, row=3, columnspan=2, padx=5, pady=5)
roundnessInput = tk.Text(window, height=1, width=15)
roundnessInput.grid(column=2, row=3, padx=5, pady=5)
roundnessInput.insert(tk.END, ROUNDNESS_DEFUALT)

BLUR_TIMES_DEFUALT = "2"
blurTimesInputText = ttk.Label(window, text="blur times:")
blurTimesInputText.grid(column=0, row=4, columnspan=2, padx=5, pady=5)
blurTimesInput = tk.Text(window, height=1, width=15)
blurTimesInput.grid(column=2, row=4, padx=5, pady=5)
blurTimesInput.insert(tk.END, BLUR_TIMES_DEFUALT)

MIN_CHAIN_LENGTH_DEFUALT = "20"
minChainLengthInputText = ttk.Label(window, text="minimum chain length:")
minChainLengthInputText.grid(column=0, row=5, columnspan=2, padx=5, pady=5)
minChainLengthInput = tk.Text(window, height=1, width=15)
minChainLengthInput.grid(column=2, row=5, padx=5, pady=5)
minChainLengthInput.insert(tk.END, MIN_CHAIN_LENGTH_DEFUALT)

submitButton = ttk.Button(window, style="Accent.TButton", text="Submit", command=submit)
submitButton.grid(column=5, row=2, padx=5, pady=5)

window.mainloop()
