# -*- coding: utf-8 -*-

import ctypes, datetime, os, sys, shutil, threading, tkMessageBox
import subprocess
from filecmp import dircmp
from time import sleep
from Tkinter import Checkbutton, Button, Entry, Label, Tk, StringVar, DoubleVar, IntVar, RIDGE, X, LEFT


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

def doCopy():
	# Checks that a source folder has been selected
	if pathSrc == "":
	    root2 = Tk()
	    root2.withdraw()
	    tkMessageBox.showerror(title="Problem", message="You must select a source folder")
	    root2.destroy()
	# Checks that at least one destination folder has been selected				
	elif (pathDst1 == "") & (pathDst2 == ""):
		root2 = Tk()
		root2.withdraw()
		tkMessageBox.showerror(title="Problem", message="You must select at least one destination folder")
		root2.destroy()
	else:
	    root.destroy()

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

# Initialize parameters
userName = get_display_name().split(",")
mailAdresse = userName[1][1:]+"."+userName[0]+"@fmi.ch"
pathSrc=""
pathDst1=""
pathDst2=""
global currdir
currdir = os.getcwd()

# ****************************************************
# Dialog window
# ****************************************************

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
# Source folder selection
srcButton = Button(root, text = 'Source directory', overrelief=RIDGE, font = "arial 10",  command=chooseSrcDir)
srcButton.config(bg = "light steel blue", fg="black")
srcButton.pack(padx = 10, pady=5, fill=X)
srcTxtLabel = Label(root, textvariable = srcTxt, font = "arial 10")
srcTxtLabel.config(bg = "light steel blue")
srcTxtLabel.pack(padx = 10, anchor = "w")
# Destination 1 folder selection
dst1Button = Button(root, text = 'Destination 1 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst1Dir)
dst1Button.config(bg = "light steel blue", fg="black")
dst1Button.pack(padx = 10, pady=5, fill=X)
dst1TxtLabel = Label(root, textvariable = dst1Txt, font = "arial 10")
dst1TxtLabel.config(bg = "light steel blue")
dst1TxtLabel.pack(padx = 10, anchor = "w")
# Destination 2 folder selection
dst2Button = Button(root, text = 'Destination 2 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst2Dir)
dst2Button.config(bg = "light steel blue")
dst2Button.pack(padx = 10, pady=5, fill=X)
dst2TxtLabel = Label(root, textvariable = dst2Txt, font = "arial 10")
dst2TxtLabel.config(bg = "light steel blue")
dst2TxtLabel.pack(padx = 10, anchor = "w")
# Options checkboxes
multiCheckBox = Checkbutton(root, text="Copy both destinations in parallel", wraplength=200, variable=multiThread)
multiCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
multiCheckBox.pack(padx = 10, pady=5, anchor="w")
delCheckBox = Checkbutton(root, text="Delete files in source folder after copy", wraplength=200, variable=deleteSource)
delCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
delCheckBox.pack(padx = 10, pady=5, anchor="w")
# Time-lapse information
tiLabel = Label(root, text="Time interval (min):", font = "arial 10")
tiLabel.config(bg = "light steel blue", fg="black")
tiLabel.pack(padx = 10, anchor="w")
tiText = Entry(root, width=6, justify=LEFT, textvariable = timeInt)
tiText.config(bg = "light steel blue", fg="black")
tiText.pack(padx = 10, anchor="w")
# E-mail information
sendLabel = Label(root, text="Send Info to:", font = "arial 10")
sendLabel.config(bg = "light steel blue", fg="black")
sendLabel.pack(padx = 10, pady= 5, anchor="w")
adresseText = Entry(root, justify=LEFT, width = 25, textvariable = mail)
adresseText.config(bg = "light steel blue", fg="black")
adresseText.pack(padx = 10, anchor="w")
# Do Copy and Cancel buttons
spaceLabel = Label(root, text=" ", font = "arial 10")
spaceLabel.config(bg = "light steel blue", fg="black")
spaceLabel.pack(padx = 15, anchor="w")
doCopyButton = Button(root, text = 'Do Copy !', width = 8, overrelief=RIDGE, font = "arial 10", command = doCopy)
doCopyButton.config(bg = "lime green", fg="black")
doCopyButton.pack(side = "left", padx = 10, pady=5)
cancelButton = Button(root, text = 'Cancel', width = 8, overrelief=RIDGE, font = "arial 10", command = cancel)
cancelButton.config(bg = "orange", fg="black")
cancelButton.pack(side = "right", padx = 10, pady=5)
root.config(bg="light steel blue")
root.mainloop()


# Retireive e-mail adresse
mailAdresse = mail.get()

# test number of destination entered				
numdest = 0
if (pathDst1 != "") | (pathDst2 != ""):
	numdest = 1
	ThreadTwo = False
if (pathDst1 != "") & (pathDst2 != ""):
	numdest = 2
	ThreadTwo = True

# If only one destination enterd, attribute it to pathDst1
if numdest==1:
	if pathDst1 == "":
		pathDst1 = pathDst2
		pathDst2 = ""

# Initialize the summary report
summary = "Robocopy completed...\n\nSource = "+pathSrc+"\nTarget1 = "+pathDst1+"\nTarget2 = "+pathDst2+"\n"
myTime = datetime.datetime.now()
summary += myTime.strftime("Process started at %H:%M:%S")

# Starts the copy with Robocopy
try:
	condition = False
	while condition == False:
		# Start Thread1
		try:
			Thread1 = threading.Thread(target=worker, args=(pathSrc, pathDst1,0))
			Thread1.start()
			print ("Starting copying to destination1")
		except:
			myTime = datetime.datetime.now()
			summary += myTime.strftime("\nProblem with thread1 occured at %H:%M:%S")
				
		# Start second thread if pathDst2 exists
		if pathDst2 != "":
			if multiThread.get() == 0:
				# wait for Thread1 to be finished before starting Thread2
				conditionWait = False
				while conditionWait == False:
					if not Thread1.isAlive():
						conditionWait = True
					else:
						print("Waiting for Robocopy to finish dst1 before starting dst2...")
						sleep(10)	
				# Start Thread2 now that Thread1 is done
				try:
					Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2,0))
					Thread2.start()
					print ("Starting copying to destination2")
				except:
					myTime = datetime.datetime.now()
					summary += myTime.strftime("\nProblem with thread1 occured at %H:%M:%S")
					
			else:
				# Start Thread2 in parallel to Thread1	
				try:
					Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2,0))
					Thread2.start()
					print ("Starting copying to destination2")
				except:
					myTime = datetime.datetime.now()
					summary += myTime.strftime("\nProblem with thread2 occured at %H:%M:%S")
			
		# Wait for all threads to be finished before comparing folders
		conditionWait = False
		while conditionWait == False:
			print ("Waiting for "+str(timeInt.get())+" min before comparing folders again")
			sleep(int(timeInt.get()*60))
			if not Thread1.isAlive():
				if ThreadTwo == True:
					if not Thread2.isAlive():
						conditionWait = True
					else:
						print("Robocopy still active")
				else:	
					conditionWait = True
			else:
				print("Robocopy still active...")
		
		# Delete files in source folder
		if deleteSource.get():
			# TODO: add a check if path exists and then subloop with try
			try:
				myComp = dircmp(pathSrc, pathDst1)
				for toDelete in myComp.common:
					path = os.path.join(pathSrc, toDelete)
					if os.path.isfile(path):
						os.remove(path)
					else:
						shutil.rmtree(path, ignore_errors=True)
			except:
				myTime = datetime.datetime.now()
				summary += myTime.strftime("\nProblem with deleting files occured at %H:%M:%S\n")	

		# Compare source and destination folders
		# Starts by checking if dst1 still connected and then compare content of folders
		if os.path.exists(pathDst1):
			myComp = dircmp(pathSrc, pathDst1)
			if len(myComp.left_only)==0:
				print("All files in source were found in destination1")
				# Continues with dst2 if it exists
				if pathDst2 != "":
					if os.path.exists(pathDst2):
						myComp = dircmp(pathSrc, pathDst2)
						if len(myComp.left_only)==0:
							print("All files in source were found in destination2")
							# Everything went fine both for dst1 and dst2 and there was no change during time lapse indicated
							condition = True
					else:
						myTime = datetime.datetime.now()
						message = myTime.strftime("\nProblem with comparing files in dst2 occured at %H:%M:%S\nCould not find dst2 folder")
						summary += message
						# Everything went fine for dst1, dst2 seems not available anymore
						condition = True
				else :
					# Everything went fine dst1 (no dst2 had been entered by user) and there was no change during time lapse indicated
					condition = True
		elif pathDst2 != "":
			myTime = datetime.datetime.now()
			message = myTime.strftime("\nProblem with comparing files in dst1 occured at %H:%M:%S\nCould not find dst1 folder\nChecking now dst2\n")
			summary += message
			SendEmail(mailAdresse, "Robocopy Info: ERROR", message)
			if os.path.exists(pathDst2):
				myComp = dircmp(pathSrc, pathDst2)
				if len(myComp.left_only)==0:
					print("All files in source were found in destination2")
					# dst1 could not be found anymore, but there is a copy on dst2 and no change during time lapse indicated
					condition = True
			else :
				myTime = datetime.datetime.now()
				summary += myTime.strftime("\nProblem with comparing files in dst2 occured at %H:%M:%S\nCould not find dst2 either\n")
				SendEmail(mailAdresse, "Robocopy Info: ERROR", summary)
				# Both destinations are not available anymore
				condition = True
		else:
			summary += myTime.strftime("\nProblem with comparing files in dst1 occured at %H:%M:%S\nCould not find dst1 folder")
			# dst1 is not available anymore, no dst2 had been entered
			condition = True

		
except:
	summary += "\nAn error occured.\n"
	
	

"""
****************************************************
Send E-mail at END
****************************************************
"""
myTime = datetime.datetime.now()
summary += myTime.strftime("\nProcess finished at %H:%M:%S\n")
SendEmail(mailAdresse, "Robocopy Info", summary)

