# -*- coding: utf-8 -*-

import ctypes, datetime, getpass, os, re, sys, shutil, threading, tkMessageBox
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


# FUNCTION: Sends a mail to the user about calculated times
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
		editSummary(logfileName, "\n<p>%H:%M:%S: Could not send e-mail")


# FUNCTIONs: get Directories, done and cancel functions
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


# FUNCTION: Workers / Threads
def worker(var1, var2, silent, dummy):
	if silent==0:
		subprocess.Popen(["robocopy", var1, var2, "/e", "/Z", "/r:0", "/w:30", "/COPY:DT", "/dcopy:T"], creationflags=subprocess.SW_HIDE, shell=True)
	else:
		subprocess.call(["robocopy", var1, var2, "/e", "/Z", "/r:0", "/w:30", "/COPY:DT", "/dcopy:T"])

# FUNCTION compare subdirectories
def compsubfolders(source, destination):
	condition = True
	for root, directories, files in os.walk(source):
		for myDir in directories:
			path1 = os.path.join(root, myDir)
			path2 = re.sub(source, destination, path1)
			if os.path.exists(path2):
				myComp = dircmp(path1, path2)
				if len(myComp.left_only)!=0:
					condition = False
			else:
				condition = False
	return condition
				
# FUNCTION TO DO: update summary and write logfile
# NB: Logfile name should be logfile path = user desktop
def writeLogFile(logfileName, text):
	logfile = open(logfileName, 'w')
	logfile.write(text)
	logfile.close()

# FUNCTION Edit summary
def editSummary(logfileName, text):
	global summary
	myTime = datetime.datetime.now()
	summary += myTime.strftime(text)
	writeLogFile(logfileName, summary)
	
	
# ****************************************************************************************************
# MAIN
# ****************************************************************************************************

# Initialize parameters:

# Generates mail adresse
try:
	userName = get_display_name().split(",")
	mailAdresse = userName[1][1:]+"."+userName[0]+"@fmi.ch"
except:
	mailAdresse = "FirstName.LastName@fmi.ch"

# Set paths to empty
pathSrc=""
pathDst1=""
pathDst2=""
global currdir
currdir = os.getcwd()

# Dialog window
root = Tk()
root.title("Robocopy FAIM")
# Source folder selection
srcTxt = StringVar()
srcTxt.set("")
srcButton = Button(root, text = 'Source directory', overrelief=RIDGE, font = "arial 10",  command=chooseSrcDir)
srcButton.config(bg = "light steel blue", fg="black")
srcButton.pack(padx = 10, pady=5, fill=X)
srcTxtLabel = Label(root, textvariable = srcTxt, font = "arial 10")
srcTxtLabel.config(bg = "light steel blue")
srcTxtLabel.pack(padx = 10, anchor = "w")
# Destination 1 folder selection
dst1Txt = StringVar()
dst1Txt.set("")
dst1Button = Button(root, text = 'Destination 1 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst1Dir)
dst1Button.config(bg = "light steel blue", fg="black")
dst1Button.pack(padx = 10, pady=5, fill=X)
dst1TxtLabel = Label(root, textvariable = dst1Txt, font = "arial 10")
dst1TxtLabel.config(bg = "light steel blue")
dst1TxtLabel.pack(padx = 10, anchor = "w")
# Destination 2 folder selection
dst2Txt = StringVar()
dst2Txt.set("")
dst2Button = Button(root, text = 'Destination 2 directory', overrelief=RIDGE, font = "arial 10", command=chooseDst2Dir)
dst2Button.config(bg = "light steel blue")
dst2Button.pack(padx = 10, pady=5, fill=X)
dst2TxtLabel = Label(root, textvariable = dst2Txt, font = "arial 10")
dst2TxtLabel.config(bg = "light steel blue")
dst2TxtLabel.pack(padx = 10, anchor = "w")
# Options checkboxes
multiThread = IntVar()
multiThread.set(0)
multiCheckBox = Checkbutton(root, text="Copy both destinations in parallel", wraplength=200, variable=multiThread)
multiCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
multiCheckBox.pack(padx = 10, pady=5, anchor="w")
silentThread = IntVar()
silentThread.set(0)
silentCheckBox = Checkbutton(root, text="Show Robocopy console", wraplength=200, variable=silentThread)
silentCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
silentCheckBox.pack(padx = 10, pady=5, anchor="w")
deleteSource = IntVar()
deleteSource.set(0)
delCheckBox = Checkbutton(root, text="Delete files in source folder after copy", wraplength=200, variable=deleteSource)
delCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
delCheckBox.pack(padx = 10, pady=5, anchor="w")
# Time-lapse information
timeInt = DoubleVar()
timeInt.set(0.1)
tiLabel = Label(root, text="Time interval (min):", font = "arial 10")
tiLabel.config(bg = "light steel blue", fg="black")
tiLabel.pack(padx = 10, anchor="w")
tiText = Entry(root, width=6, justify=LEFT, textvariable = timeInt)
tiText.config(bg = "light steel blue", fg="black")
tiText.pack(padx = 10, anchor="w")
# E-mail information
mail = StringVar()
mail.set(mailAdresse)
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
summary = "Robocopy completed...\n\nSource = "+pathSrc+"\n<p>Target1 = "+pathDst1+"\n<p>Target2 = "+pathDst2+"\n<p>"
logfileName = r"\\argon\\" + getpass.getuser() + r"\\Desktop\\Robocopy Logfile_Started at " + datetime.datetime.now().strftime("%H-%M-%S") + ".html"
editSummary(logfileName, "\n<p>%H:%M:%S: Process started") 

# Starts the copy with Robocopy
try:
	logfile = open(logfileName, 'w')
	logfile.write(summary)
	logfile.close()
	condition = False
	while condition == False:
		# Start Thread1
		try:
			Thread1 = threading.Thread(target=worker, args=(pathSrc, pathDst1, silentThread.get(), 0))
			Thread1.start()
			editSummary(logfileName, "\n<p>%H:%M:%S: Starting copying to destination 1")
			editSummary(logfileName, "\n<p>%H:%M:%S: \tThread 1 running...")
			
		except:
			editSummary(logfileName, "\n<p>%H:%M:%S: Problem with thread 1")
			SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
				
		# Start second thread if pathDst2 exists
		if pathDst2 != "":
			if multiThread.get() == 0:
				# wait for Thread1 to be finished before starting Thread2
				conditionWait = False
				while conditionWait == False:
					if not Thread1.isAlive():
						conditionWait = True
					else:
						editSummary(logfileName, "\n<p>%H:%M:%S: \tWaiting for Robocopy to finish dst1 before starting dst2...")
						sleep(10)	
				# Start Thread2 now that Thread1 is done
				try:
					Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2, silentThread.get(),0))
					Thread2.start()
					editSummary(logfileName, "\n<p>%H:%M:%S: Starting copying to destination 2")
					editSummary(logfileName, "\n<p>%H:%M:%S: \tThread 2 running...")
				except:
					editSummary(logfileName, "\n<p>%H:%M:%S: Problem with thread 1")
					SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
					
			else:
				# Start Thread2 in parallel to Thread1	
				try:
					Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2, silentThread.get(),0))
					Thread2.start()
					editSummary(logfileName, "\n<p>%H:%M:%S: Starting copying to destination2")
					editSummary(logfileName, "\n<p>%H:%M:%S: \tThread 2 running")
				except:
					editSummary(logfileName, "\n<p>%H:%M:%S: Problem with thread 2")
					SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
			
		# Wait for all threads to be finished before comparing folders
		conditionWait = False
		while conditionWait == False:
			editSummary(logfileName, "\n<p>%H:%M:%S: Waiting for "+str(timeInt.get())+" min before comparing folders again")
			sleep(int(timeInt.get()*60))
			if not Thread1.isAlive():
				if ThreadTwo == True:
					if not Thread2.isAlive():
						conditionWait = True
					else:
						editSummary(logfileName, "\n<p>%H:%M:%S: Robocopy still active")
				else:	
					conditionWait = True
			else:
				editSummary(logfileName, "\n<p>%H:%M:%S: Robocopy still active...")
		
		# Delete files in source folder
		if deleteSource.get():
			# NB: If pathDst1 is not connected, no deletion accurs.
			# The script deletes first each file one by one and then goes once more through folders
			try:
				for root, directories, files in os.walk(pathSrc):
					for myFile in files:
						path1 = os.path.join(root, myFile)
						path2 = re.sub(pathSrc, pathDst1, path1)
						if os.path.isfile(path2):
							os.remove(path1)
			except:
				editSummary(logfileName, "\n<p>%H:%M:%S: Problem with deleting files\n")
				SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
			# 	
			# Now empty folders are deleted...	
			emptyFolders = []
			try:
				for root, directories, files in os.walk(pathSrc):
					emptyFolders.append(root)
				emptyFolders.sort(reverse = True)
				for emptyFolder in emptyFolders[:-1]:
					if os.listdir(emptyFolder) == []:
						shutil.rmtree(emptyFolder)
			except:
				editSummary(logfileName, "\n<p>%H:%M:%S: Problem with deleting folders\n")				
				

		# Compare source and destination folders to determine whether process should be stopped (i.e. no new file created in Source folder)
		# If no new file or folder was created since the beginning of the robocopy, then the condition is true and loop is terminated (= exit)
		#
		# Starts by checking if dst1 still connected and then compare content of folders
		if os.path.exists(pathDst1):
			sameContent = compsubfolders(pathSrc, pathDst1)
			if sameContent==True:
				editSummary(logfileName, "%H:%M:%S: All files in source were found in destination 1")
				# Continues with dst2 if it exists
				if pathDst2 != "":
					if os.path.exists(pathDst2):
						sameContent = compsubfolders(pathSrc, pathDst1)
						if sameContent==True:
							editSummary(logfileName, "%H:%M:%S: All files in source were found in destination 2")
							# Everything went fine both for dst1 and dst2 and there was no change during time lapse indicated
							condition = True
					else:
						editSummary(logfileName, "\n<p>%H:%M:%S: Problem with comparing files in dst2\nCould not find dst2 folder")
						SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
						# Everything went fine for dst1, dst2 seems not available anymore
						condition = True
				else :
					# Everything went fine for dst1 (no dst2 had been entered by user) and there was no change during time lapse indicated
					condition = True
		elif pathDst2 != "":
			editSummary(logfileName, "\n<p>%H:%M:%S: Problem with comparing files in dst1\nCould not find dst1 folder\nChecking now dst2\n")
			SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
			if os.path.exists(pathDst2):
				sameContent = compsubfolders(pathSrc, pathDst1)
				if sameContent==True:
					editSummary(logfileName, "\n<p>%H:%M:%S: All files in source were found in destination 2")
					# dst1 could not be found anymore, but there is a copy on dst2 and no change during time lapse indicated
					condition = True
			else :
				editSummary(logfileName, "\n<p>%H:%M:%S: Problem with comparing files in dst2\nCould not find dst2 either\n")
				SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
				# Both destinations are not available anymore
				condition = True
		else:
			editSummary(logfileName, "\n<p>%H:%M:%S: Problem with comparing files in dst1\nCould not find dst1 folder.\nRobocopy process aborted")
			SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
			# dst1 is not available anymore, no dst2 had been entered
			condition = True

# Something went wrong at some unidentified step		
except:
	editSummary(logfileName, "\n<p>%H:%M:%S: An error occured.\n")

# Copying dst1 to dst2, as dst1 should be local and less error prone and dst2 might miss some files.
editSummary(logfileName, "\n<p>%H:%M:%S: Copying from source to destination(s) finished, now copying from destination 1 to destination 2")
sameContent = compsubfolders(pathDst1, pathDst2)
if sameContent==False:
	try:
		Thread3 = threading.Thread(target=worker, args=(pathDst1, pathDst2, silentThread.get(), 0))
		Thread3.start()
		editSummary(logfileName, "\n<p>%H:%M:%S: Starting copying from destination 1 to destination 2")
	except:
		editSummary(logfileName, "\n<p>%H:%M:%S: Problem with thread3 (dst1 to dst2)")

# count number of files in each folder
try:
	nbFiles = sum([len(files) for r, d, files in os.walk(pathSrc)])
	editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in source = "+str(nbFiles))
except:
	editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in source could not be checked")
	
try:
	nbFiles = sum([len(files) for r, d, files in os.walk(pathDst1)])
	editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in source = "+str(nbFiles))
except:
	editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in Destination 1 could not be checked")
	
if pathDst2 != "":
	try:
		nbFiles = sum([len(files) for r, d, files in os.walk(pathDst2)])
		editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in source = "+str(nbFiles))
	except:
		editSummary(logfileName, "\n<p>%H:%M:%S: Number of files in Destination 2 could not be checked")


editSummary(logfileName, "\n<p>%H:%M:%S: Process finished.")

logfile = open(logfileName, 'w')
logfile.write(summary)
logfile.close()

# Send E-mail at the end with the summary
summary = re.sub("<p>", "", summary)
SendEmail(mailAdresse, "Robocopy Info", summary)

# In case e-mail could not be sent, summary is printed in Spyder console
print summary