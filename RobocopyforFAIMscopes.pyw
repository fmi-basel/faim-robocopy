# -*- coding: utf-8 -*-

import ctypes, datetime, getpass, os, psutil, re, subprocess, sys, shutil, threading, tkMessageBox
from filecmp import dircmp
import filecmp
from time import sleep
from Tkinter import Checkbutton, Button, Entry, Label, Tk, StringVar, DoubleVar, IntVar, RIDGE, X, LEFT

# ******************	
def mainProg(root, pathSrc, pathDst1, pathDst2, multiThread, timeInterval, silentThread, deleteSource, mailAdresse, waitExit):
	print (pathSrc+"; "+pathDst1+"; "+pathDst2+"; "+str(multiThread)+"; "+str(timeInterval)+"; "+str(silentThread)+"; "+str(deleteSource)+"; "+mailAdresse)
	# test number of destination entered				
	numdest = 0
	if (pathDst1 != "") | (pathDst2 != ""):
		numdest = 1
		#ThreadTwo = False
	if (pathDst1 != "") & (pathDst2 != ""):
		numdest = 2
		#ThreadTwo = True
	# If only one destination enterd, attribute it to pathDst1
	if numdest==1:
		if pathDst1 == "":
			pathDst1 = pathDst2
			pathDst2 = ""
	# Initialize the summary report
	globalSummary.set("Robocopy Folders:\n\nSource = "+pathSrc+"\n<p>Target1 = "+pathDst1+"\n<p>Target2 = "+pathDst2+"\n<p>")

	# Starts the copy with Robocopy
	editSummary("\n<p>%H:%M:%S: Process started")
	
	# initialise Threads
	global Thread1
	Thread1 = threading.Thread()
	global Thread2
	Thread2 = threading.Thread()
	
	# Starts while loop which will stop when no change after given time, then condition will be True
	condition = False
	checkTime = datetime.datetime.now()
	
	try:
		while condition == False:
			# ****Start Thread1********
			# Checks first that Thread1 is not running, otherwise skip the step.
			sameContent = compsubfolders(pathSrc, pathDst1)
			if sameContent == False:
				checkTime = datetime.datetime.now()
				if Thread1.isAlive() == False | sameContent == False:
					checkTime = datetime.datetime.now()
					try:
						Thread1 = threading.Thread(target=worker, args=(pathSrc, pathDst1, silentThread))
						Thread1.start()
						editSummary("\n<p>%H:%M:%S: Copying to destination 1")
					except:
						editSummary("\n<p>%H:%M:%S: Problem with thread 1")
						SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
				else:
					pass
					
			# Start second thread if pathDst2 exists
			if pathDst2 != "":
				if multiThread == 0:
					# wait for Thread1 to be finished before starting Thread2
					conditionWait = False
					while conditionWait == False:
						if not Thread1.isAlive():
							conditionWait = True
						else:
							sleep(10)	
					# Start Thread2 now that Thread1 is done
					sameContent = compsubfolders(pathSrc, pathDst2)
					if sameContent == False:
						checkTime = datetime.datetime.now()
						if Thread2.isAlive() == False:
							try:
								Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2, silentThread))
								Thread2.start()
								editSummary("\n<p>%H:%M:%S: Copying to destination 2")
							except:
								editSummary("\n<p>%H:%M:%S: Problem with thread 1")
								SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
						else:
							pass
						
				else:
					# Start Thread2 in parallel to Thread1
					sameContent = compsubfolders(pathSrc, pathDst2)
					if sameContent == False:
						checkTime = datetime.datetime.now()
						if Thread2.isAlive() == False:
							try:
								Thread2 = threading.Thread(target=worker, args=(pathSrc, pathDst2, silentThread))
								Thread2.start()
								editSummary("\n<p>%H:%M:%S: Copying to destination2")
							except:
								editSummary("\n<p>%H:%M:%S: Problem with thread 2")
								SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
						else:
							pass
			
			# Wait next time-point before comparing folders
			editSummary("\n<p>%H:%M:%S: Waiting for "+str(timeInterval)+" min before next Robocopy")
			sleep(int(timeInterval*60))
			
			# Delete files in source folder
			if deleteSource:
				try:
					for root, directories, files in os.walk(pathSrc):
						for myFile in files:
							pathS = os.path.join(root, myFile)
							path1 = re.sub(pathSrc, pathDst1, pathS)
							path2 = re.sub(pathSrc, pathDst2, pathS)
							if os.path.isfile(path1) & filecmp.cmp(pathS, path1)==True:
								if pathDst2 != "":
									if os.path.isfile(path2) & filecmp.cmp(pathS, path2)==True:
										os.remove(pathS)
									else:
										pass
								else:
									os.remove(pathS)
							else:
								pass
				except:
					editSummary("\n<p>%H:%M:%S: Problem with deleting files\n")
					SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
				
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
					editSummary("\n<p>%H:%M:%S: Problem with deleting folders\n")
					

			# Compare source and destination folders to determine whether process should be stopped (i.e. no new file created in Source folder)
			# If no new file or folder was created since the beginning of the robocopy, then the condition is true and loop is terminated (= exit)
			exitTime = datetime.datetime.now()
			timeDiff = exitTime - checkTime
			if int(timeDiff.total_seconds()) >= int(waitExit*60):
				checkTime = exitTime
				editSummary("\n<p>%H:%M:%S: Checking whether all folders are the same\n")
				# Starts by checking if dst1 still connected and then compare content of folders
				if os.path.exists(pathDst1):
					sameContent = compsubfolders(pathSrc, pathDst1)
					if sameContent==True:
						editSummary("\n<p>%H:%M:%S: All files in source were found in destination 1")
						# Continues with dst2 if it exists
						if pathDst2 != "":
							if os.path.exists(pathDst2):
								sameContent = compsubfolders(pathSrc, pathDst1)
								if sameContent==True:
									editSummary("\n<p>%H:%M:%S: All files in source were found in destination 2")
									# Everything went fine both for dst1 and dst2 and there was no change during time lapse indicated
									condition = True
							else:
								editSummary("\n<p>%H:%M:%S: Problem with comparing files in dst2\nCould not find dst2 folder")
								SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
								# Everything went fine for dst1, dst2 seems not available anymore
								condition = True
						else :
							# Everything went fine for dst1 (no dst2 had been entered by user) and there was no change during time lapse indicated
							condition = True
				elif pathDst2 != "":
					editSummary("\n<p>%H:%M:%S: Problem with comparing files in dst1\nCould not find dst1 folder\nChecking now dst2\n")
					SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
					if os.path.exists(pathDst2):
						sameContent = compsubfolders(pathSrc, pathDst1)
						if sameContent==True:
							editSummary("\n<p>%H:%M:%S: All files in source were found in destination 2")
							# dst1 could not be found anymore, but there is a copy on dst2 and no change during time lapse indicated
							condition = True
					else :
						editSummary("\n<p>%H:%M:%S: Problem with comparing files in dst2\nCould not find dst2 either\n")
						SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
						# Both destinations are not available anymore
						condition = True
				else:
					editSummary("\n<p>%H:%M:%S: Problem with comparing files in dst1\nCould not find dst1 folder.\nRobocopy process aborted")
					SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
					# dst1 is not available anymore, no dst2 had been entered
					condition = True
	
	# Something went wrong at some unidentified step		
	except:
		editSummary("\n<p>%H:%M:%S: An error occured.\n")
		SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")

	# count number of files in each folder
	countFileNumber(pathSrc)
	countFileNumber(pathDst1)
	if pathDst2 != "":
		countFileNumber(pathDst2)
	
	# Send E-mail at the end with the summary
	globalSummary.set(re.sub("<p>", "", globalSummary.get()))
	dialogSummary.set("Process finished")
	SendEmail(mailAdresse, "Robocopy Info", globalSummary.get())
	
	# In case e-mail could not be sent, summary is printed in Spyder console
	print globalSummary.get()
	root.destroy()
	sys.exit()

# ******************	
# FUNCTION: count number of files in each folder
def countFileNumber(folder):
	try:
		nbFiles = sum([len(files) for r, d, files in os.walk(folder)])
		editSummary("\n<p>%H:%M:%S: Number of files in "+folder+" = "+str(nbFiles))
	except:
		editSummary("\n<p>%H:%M:%S: Number of files in "+folder+" could not be checked")

# ******************	
# FUNCTION: get User full name
def get_display_name():
    GetUserNameEx = ctypes.windll.secur32.GetUserNameExW
    NameDisplay = 3

    size = ctypes.pointer(ctypes.c_ulong(0))
    GetUserNameEx(NameDisplay, None, size)
    nameBuffer = ctypes.create_unicode_buffer(size.contents.value)
    GetUserNameEx(NameDisplay, nameBuffer, size)
    return nameBuffer.value

# ******************	
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
		print("Could not send e-mail")

# ******************	
# FUNCTIONs from dialog box
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

# ******************
# FUNCTIOn Do Copy!
def doCopy():
	# Checks that a source folder has been selected
	if srcTxt.get() == "":
	    root2 = Tk()
	    root2.withdraw()
	    tkMessageBox.showerror(title="Problem", message="You must select a source folder")
	    root2.destroy()
	# Checks that at least one destination folder has been selected				
	elif (dst1Txt.get() == "") & (dst2Txt.get() == ""):
		root2 = Tk()
		root2.withdraw()
		tkMessageBox.showerror(title="Problem", message="You must select at least one destination folder")
		root2.destroy()
	else:
		#root.destroy()
		mainThread = threading.Thread(target = mainProg, args = (root, srcTxt.get(), dst1Txt.get(), dst2Txt.get(), multiThr.get(), timeInt.get(), silentThr.get(), deleteSrc.get(), mail.get(), timeExit.get()))
		mainThread.start()

# ******************	
# FUNCTION Abort		
def abort():
	print ("Dialog Canceled")
	root.destroy()
	try:
		Thread1.run = False
		Thread2.run = False
	except:
		pass
	# Delete all windows consoles
	for proc in psutil.process_iter():
		if proc.name() == "conhost.exe":
			try:
				 process = psutil.Process(proc.pid)
				 process.terminate()
			except:
				 pass
	# Stops all Robocopy scripts		
	for proc in psutil.process_iter():
		if proc.name() == "Robocopy.exe":
			process = psutil.Process(proc.pid)
			process.terminate()
			
	# Send e-mail to user about status at aborting
	SendEmail(mail.get(), "Robocopy aborted by user", globalSummary.get())
	
	# Kill current running process
	process = psutil.Process()
	process.terminate()
	sys.exit()
	
# ******************	
# FUNCTION: Workers / Threads
def worker(var1, var2, silent):
	print ("worker started !!!")
	if silent==0:
		FNULL = open(os.devnull, 'w')
		subprocess.call(["robocopy", var1, var2, "/e", "/Z", "/r:0", "/w:30", "/COPY:DT", "/dcopy:T"], stdout=FNULL, stderr=subprocess.STDOUT)
	else:
		subprocess.call(["robocopy", var1, var2, "/e", "/Z", "/r:0", "/w:30", "/COPY:DT", "/dcopy:T"])

# ******************	
# FUNCTION compare subdirectories
def compsubfolders(source, destination):
	condition = True
	myComp = dircmp(source, destination)
	if len(myComp.left_only)!=0:
		condition = False
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


# ******************	
# FUNCTION Edit summary
def editSummary(text):
	
	# Edit globalSummary
	myTime = datetime.datetime.now()
	globalSummary.set(globalSummary.get() + myTime.strftime(text))
	try:
		logfile = open(logfileName, 'w')
		logfile.write(globalSummary.get())
		logfile.close()
	except:
		print ("Problem with logfile: " +logfileName)
		
	# Edit the summary for dialog window
	textTmp = globalSummary.get()
	for j in range (10):
		j = textTmp.rfind("<p>")
		if j>=0:
			textTmp = textTmp[:j]
		else:
			j=0
			break
	textTmp = re.sub("<p>", "", globalSummary.get()[j:])
	dialogSummary.set(textTmp)
	
	
# *******************************
# DIALOG WINDOW
# *******************************
if sys.executable.endswith("pythonw.exe"):
  sys.stdout = open(os.devnull, "w");
  sys.stderr = open(os.path.join(os.getenv("TEMP"), "stderr-"+os.path.basename(sys.argv[0])), "w")

# Define the path for saving the Log file
userName = getpass.getuser()
if userName == "CVUser":
	logFilepath = r"C:\\Users\\CVUser\\Desktop\\Robocopy FAIM Logfiles"
else:
	logFilepath = os.path.join(os.environ['HOMESHARE'], 'Desktop')
	if os.path.exists(logFilepath) == False:
		logFilepath = os.path.join(os.environ['USERPROFILE'], 'Desktop')
logfileName = logFilepath + r"\\Robocopy_Logfile_" + datetime.datetime.now().strftime("%H-%M-%S") + ".html"

# Dialog window
root = Tk()
root.title("Robocopy FAIM")
currdir = os.getcwd()
try:
	userName = get_display_name().split(",")
	mailAdresse = userName[1][1:]+"."+userName[0]+"@fmi.ch"
except:
	mailAdresse = "FirstName.LastName@fmi.ch"
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
multiThr = IntVar()
multiThr.set(0)
multiCheckBox = Checkbutton(root, text="Copy both destinations in parallel", wraplength=200, variable=multiThr)
multiCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
multiCheckBox.pack(padx = 10, pady=5, anchor="w")
silentThr = IntVar()
silentThr.set(0)
silentCheckBox = Checkbutton(root, text="Show Robocopy console", wraplength=200, variable=silentThr)
silentCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
silentCheckBox.pack(padx = 10, pady=5, anchor="w")
deleteSrc = IntVar()
deleteSrc.set(0)
delCheckBox = Checkbutton(root, text="Delete files in source folder after copy", wraplength=200, variable=deleteSrc)
delCheckBox.config(bg = "light steel blue", fg="black", justify = LEFT)
delCheckBox.pack(padx = 10, pady=5, anchor="w")
# Time-lapse information
timeInt = DoubleVar()
timeInt.set(0.5)
tiLabel = Label(root, text="Time interval between Robocopy processes (min):", font = "arial 10")
tiLabel.config(bg = "light steel blue", fg="black")
tiLabel.pack(padx = 10, anchor="w")
tiText = Entry(root, width=6, justify=LEFT, textvariable = timeInt)
tiText.config(bg = "light steel blue", fg="black")
tiText.pack(padx = 10, anchor="w")
# Time-Exit information
timeExit = DoubleVar()
timeExit.set(5)
tiexLabel = Label(root, text="Time for exiting if no change in folders (min):", font = "arial 10")
tiexLabel.config(bg = "light steel blue", fg="black")
tiexLabel.pack(padx = 10, anchor="w")
tiexText = Entry(root, width=6, justify=LEFT, textvariable = timeExit)
tiexText.config(bg = "light steel blue", fg="black")
tiexText.pack(padx = 10, anchor="w")
# E-mail information
mail = StringVar()
mail.set(mailAdresse)
sendLabel = Label(root, text="Send Summary to:", font = "arial 10")
sendLabel.config(bg = "light steel blue", fg="black")
sendLabel.pack(padx = 10, pady= 5, anchor="w")
adresseText = Entry(root, justify=LEFT, width = 25, textvariable = mail)
adresseText.config(bg = "light steel blue", fg="black")
adresseText.pack(padx = 10, anchor="w")
# Summary
dialogSummary = StringVar()
globalSummary = StringVar()
dialogSummary.set("*** Summary window *****")
globalSummary.set("")
sumLabel = Label(root, textvariable=dialogSummary, font = "arial 10")
sumLabel.config(bg = "light steel blue", fg="navy", justify = LEFT, height = 12)
sumLabel.pack(padx = 10, pady= 10, anchor="w")
# Space
spaceLabel = Label(root, text=" ", font = "arial 10")
spaceLabel.config(bg = "light steel blue", fg="black")
spaceLabel.pack(padx = 15, anchor="w")
# Do Copy and Cancel buttons
doCopyButton = Button(root, text = 'Do Copy !', width = 8, overrelief=RIDGE, font = "arial 10", command = doCopy)
doCopyButton.config(bg = "lime green", fg="black")
doCopyButton.pack(side = "left", padx = 10, pady=5)
cancelButton = Button(root, text = 'Abort', width = 8, overrelief=RIDGE, font = "arial 10", command = abort)
cancelButton.config(bg = "red", fg="black")
cancelButton.pack(side = "right", padx = 10, pady=5)
root.config(bg="light steel blue")
# Show Dialog Window
root.mainloop()
