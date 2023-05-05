# this is main, run this

import tkinter as tk
import tkinter.ttk as ttk
from PIL import ImageTk, Image
import os
import turtle

from ImageProcessor import *

MAX_DIMENSION = 450
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
    xOffset = int(xOffsetInput.get("1.0", tk.END))
    yOffset = int(yOffsetInput.get("1.0", tk.END))
    paperWidth = int(paperWidthInput.get("1.0", tk.END))
    paperHeight = int(paperHeightInput.get("1.0", tk.END))

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
        imageProcessor.toGCode(minChainLength, xOffset, yOffset, paperWidth, paperHeight)
    def Lap_Adj_to_GCode_plus_purge():
        Lap_Adj_to_GCode()
        # note: LINEJOINER FUNCTION MUST BE USED AFTER PURGING, DO NOT USE BEFORE PURGING IN toGCode()
        #imageProcessor.lineJoiner()
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

processingHeader = ttk.Label(window, text="Processing Options", font="Helvetica 18 bold")
processingHeader.grid(column=0, row=2, columnspan=2, padx=5, pady=10)

imageSelection = tk.StringVar()
imageMenu = ttk.OptionMenu(
    window,
    imageSelection,
    "Select image",
    *os.listdir(r"Images"),
    style="Accent.TOptionMenu",
    command=updateInputImage,
)
imageMenu.grid(column=0, row=3, padx=5, pady=5)

treatmentSelection = tk.StringVar()
treatmentMenu = ttk.OptionMenu(
    window,
    treatmentSelection,
    "Select treatment",
    *treatments,
    style="Accent.TOptionMenu",
)
treatmentMenu.grid(column=1, row=3, padx=5, pady=5)

# note: change these constants to change the defualt values in the boxes
ROUNDNESS_DEFAULT = "4"
roundnessInputText = ttk.Label(window, text="Roundness:")
roundnessInputText.grid(column=0, row=4, columnspan=1, padx=5, pady=5)
roundnessInput = tk.Text(window, height=1, width=15)
roundnessInput.grid(column=1, row=4, padx=5, pady=5)
roundnessInput.insert(tk.END, ROUNDNESS_DEFAULT)

BLUR_TIMES_DEFAULT = "0"
blurTimesInputText = ttk.Label(window, text="Blur times:")
blurTimesInputText.grid(column=0, row=5, columnspan=1, padx=5, pady=5)
blurTimesInput = tk.Text(window, height=1, width=15)
blurTimesInput.grid(column=1, row=5, padx=5, pady=5)
blurTimesInput.insert(tk.END, BLUR_TIMES_DEFAULT)

MIN_CHAIN_LENGTH_DEFAULT = "5"
minChainLengthInputText = ttk.Label(window, text="Minimum line length:\n(set to -1 to disable)")
minChainLengthInputText.grid(column=0, row=6, columnspan=1, padx=5, pady=5)
minChainLengthInput = tk.Text(window, height=1, width=15)
minChainLengthInput.grid(column=1, row=6, padx=5, pady=5)
minChainLengthInput.insert(tk.END, MIN_CHAIN_LENGTH_DEFAULT)

processingHeader = ttk.Label(window, text="Printer Options", font="Helvetica 18 bold")
processingHeader.grid(column=2, row=2, columnspan=2, padx=5, pady=10)

X_OFFSET_DEFAULT = 10 
xOffsetInputText = ttk.Label(window, text="X offset")
xOffsetInputText.grid(column=2, row=3, columnspan=1, padx=5, pady=5)
xOffsetInput = tk.Text(window, height=1, width=15)
xOffsetInput.grid(column=3, row=3, padx=5, pady=5)
xOffsetInput.insert(tk.END, X_OFFSET_DEFAULT)

Y_OFFSET_DEFAULT = 25 
yOffsetInputText = ttk.Label(window, text="Y offset")
yOffsetInputText.grid(column=2, row=4, columnspan=1, padx=5, pady=5)
yOffsetInput = tk.Text(window, height=1, width=15)
yOffsetInput.grid(column=3, row=4, padx=5, pady=5)
yOffsetInput.insert(tk.END, Y_OFFSET_DEFAULT)

PAPER_WIDTH_DEFAULT = 200
paperWidthInputText = ttk.Label(window, text="Paper width")
paperWidthInputText.grid(column=2, row=5, columnspan=1, padx=5, pady=5)
paperWidthInput = tk.Text(window, height=1, width=15)
paperWidthInput.grid(column=3, row=5, padx=5, pady=5)
paperWidthInput.insert(tk.END, PAPER_WIDTH_DEFAULT)

PAPER_HEIGHT_DEFAULT = 200
paperHeightInputText = ttk.Label(window, text="Paper height")
paperHeightInputText.grid(column=2, row=6, columnspan=1, padx=5, pady=5)
paperHeightInput = tk.Text(window, height=1, width=15)
paperHeightInput.grid(column=3, row=6, padx=5, pady=5)
paperHeightInput.insert(tk.END, PAPER_HEIGHT_DEFAULT)

# how to run multiple times
submitButton = ttk.Button(window, style="Accent.TButton", text="Submit", command=submit)
submitButton.grid(column=0, row=7, columnspan=4, padx=5, pady=5)

window.mainloop()
