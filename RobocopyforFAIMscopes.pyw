# -*- coding: utf-8 -*-

import ctypes, datetime, os, sys, shutil, threading, tkMessageBox
import subprocess
from filecmp import dircmp
from time import sleep
from Tkinter import Checkbutton, Button, Entry, Label, Text, Tk, StringVar, Scrollbar, DoubleVar, IntVar, RIDGE, FLAT, X, LEFT, RIGHT, Y


# *************************************************************************************
# FUNCTION: get User full name
#
# *************************************************************************************
def get_display_name():
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3

    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)
    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value

# *************************************************************************************
# FUNCTION: Sends a mail to the user about calculated times
#
# *************************************************************************************
def SendEmail(mailAdresse, mailObject, mailText):
	import smtplib
	from email.mime.text import MIMEText
	try:
		msg = MIMEText(mailText)
		msg['Subject'] = mailObject
		msg['From'] = "Robocopy@fmi.ch"
		msg['To'] = mailAdresse

		s = smtplib.SMTP('cas.fmi.ch')
		s.sendmail("laurent.gelman@fmi.ch", mailAdresse, msg.as_string())
		s.quit()
	except:
		print("Could not send e-mail")


# *************************************************************************************
# FUNCTION: get Directories, done and cancel functions
#
# *************************************************************************************
def chooseSrcDir():
    from tkFileDialog import askdirectory
    global pathSrc
    pathSrc = askdirectory(initialdir=currdir, title="Please select a directory")
    srcTxt.set(pathSrc)

def chooseDst1Dir():
    from tkFileDialog import askdirectory
    global pathDst1
    pathDst1 = askdirectory(initialdir=currdir, title="Please select a directory")
    dst1Txt.set(pathDst1)

def chooseDst2Dir():
    from tkFileDialog import askdirectory
    global pathDst2
    pathDst2 = askdirectory(initialdir=currdir, title="Please select a directory")
    dst2Txt.set(pathDst2)

def organizepath(numdest, pathDst1, pathDst2):
	if (pathDst1 != "") | (pathDst2 != ""):
		numdest = 1
		ThreadTwo = False
	if (pathDst1 != "") & (pathDst2 != ""):
		numdest = 2
		ThreadTwo = True
	if numdest==1:
		if pathDst1 == "":
			pathDst1 = pathDst2
			pathDst2 = ""
	return numdest, pathDst1, pathDst2	

def doCopy():
	if pathSrc == "":
		root2 = Tk()
		root2.withdraw()
		tkMessageBox.showerror(title="Problem", message="You must select a source folder")
		root2.destroy()
	elif (pathDst1 == "") & (pathDst2 == ""):
		root2 = Tk()
		root2.withdraw()
		tkMessageBox.showerror(title="Problem", message="You must select at least one destination fodler")
		root2.destroy()
	else:
		numdest = 0
		numdest, p1, p2 = organizepath(numdest, pathDst1, pathDst2)

		mailAdresse = mail.get()
		summary.set(summary.get() + "\nRobocopy Info...\n\nSource = "+pathSrc+"\nTarget1 = "+pathDst1+"\nTarget2 = "+pathDst2+"\n")

def cancel():
    root.destroy()
    sys.exit()

# *************************************************************************************
# FUNCTION: Workers / Threads
#
# *************************************************************************************

def worker(var1, var2, dummy):
	subprocess.Popen(["robocopy", var1, var2, "/e", "/Z", "/r:0", "/w:30", "/COPY:DT", "/dcopy:T"], creationflags=subprocess.SW_HIDE, shell=True)





"""
****************************************************

MAIN

****************************************************
"""
userName = get_display_name().split(",")
mailAdresse = userName[1][1:]+"."+userName[0]+"@fmi.ch"
pathSrc=""
pathDst1=""
pathDst2=""
global currdir
currdir = os.getcwd()



"""
****************************************************
Design the Dialog window
****************************************************
"""

root = Tk()
root.title("Robocopy FAIM")
srcTxt = StringVar()
srcTxt.set("")
dst1Txt = StringVar()
dst1Txt.set("")
dst2Txt = StringVar()
dst2Txt.set("")
multiThread = IntVar()
multiThread.set(0)
timeInt = DoubleVar()
timeInt.set(0.1)
mail = StringVar()
mail.set(mailAdresse)
deleteSource = IntVar()
deleteSource.set(0)
global summary
summary = StringVar()
summary.set("")

srcButton = Button(root, text = 'Source directory', overrelief=RIDGE, font = "arial 10", command=chooseSrcDir)
srcButton.config(bg = "light steel blue", fg="blue")
srcButton.pack(padx = 10, pady=5, fill=X)
srcTxtLabel = Label(root, textvariable = srcTxt, font = "arial 10")
srcTxtLabel.config(bg = "light steel blue", fg="black")
srcTxtLabel.pack(padx = 10, anchor = "w")

dst1Button = Button(root, text = 'Destination 1 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst1Dir)
dst1Button.config(bg = "light steel blue", fg="blue")
dst1Button.pack(padx = 10, pady=5, fill=X)
dst1TxtLabel = Label(root, textvariable = dst1Txt, font = "arial 10")
dst1TxtLabel.config(bg = "light steel blue", fg="black")
dst1TxtLabel.pack(padx = 10, anchor = "w")

dst2Button = Button(root, text = 'Destination 2 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst2Dir)
dst2Button.config(bg = "light steel blue", fg="blue")
dst2Button.pack(padx = 10, pady=5, fill=X)
dst2TxtLabel = Label(root, textvariable = dst2Txt, font = "arial 10")
dst2TxtLabel.config(bg = "light steel blue", fg="black")
dst2TxtLabel.pack(padx = 10, anchor = "w")

multiCheckBox = Checkbutton(root, text="Copy both destinations in parallel", wraplength=200, variable=multiThread)
multiCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
multiCheckBox.pack(padx = 10, pady=5, anchor="w")

delCheckBox = Checkbutton(root, text="Delete files in source folder after copy", wraplength=200, variable=deleteSource)
delCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
delCheckBox.pack(padx = 10, pady=5, anchor="w")

tiLabel = Label(root, text="Time interval (min):", font = "arial 10")
tiLabel.config(bg = "light steel blue", fg="blue")
tiLabel.pack(padx = 10, anchor="w")
tiText = Entry(root, width=6, justify=LEFT, textvariable = timeInt, relief = FLAT)
tiText.config(bg = "light steel blue", fg="black")
tiText.pack(padx = 20, anchor="w")

sendLabel = Label(root, text="Send Info to:", font = "arial 10")
sendLabel.config(bg = "light steel blue", fg="blue")
sendLabel.pack(padx = 10, anchor="w")
adresseText = Entry(root, justify=LEFT, width = 25, textvariable = mail, relief = FLAT)
adresseText.config(bg = "light steel blue", fg="black")
adresseText.pack(padx = 20, anchor="w")

summaryLabel = Label(root, text="Summary:", font = "arial 10")
summaryLabel.config(bg = "light steel blue", fg="blue")
summaryLabel.pack(padx = 10, pady = 5, anchor="w")
summaryText = Label(root, textvariable=summary, height = 10, font = ("arial", 10), justify = LEFT)
summaryText.config(bg = "light steel blue", fg="black")
summaryText.pack(padx = 10, pady = 5, anchor="w")
"""
spaceLabel = Label(root, text=" ", font = "arial 10")
spaceLabel.config(bg = "light steel blue", fg="black")
spaceLabel.pack(padx = 15, fill="x")
"""
doCopyButton = Button(root, text = 'Do Copy !', width = 8, overrelief=RIDGE, font = "arial 10", command = doCopy)
doCopyButton.config(bg = "lime green", fg="black")
doCopyButton.pack(side = "left", padx = 10, pady=5)

cancelButton = Button(root, text = 'Cancel', width = 8, overrelief=RIDGE, font = "arial 10", command = cancel)
cancelButton.config(bg = "orange", fg="black")
cancelButton.pack(side = "right", padx = 10, pady=5)



root.config(bg="light steel blue")
root.mainloop()



"""
****************************************************
Check for missing information about source and destination folders
****************************************************
"""
# exit program if no Source folder was entered

sys.exit()

# test number of destination entered				


