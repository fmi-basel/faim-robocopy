# -*- coding: utf-8 -*-

import datetime
import getpass
import os
import psutil
import re
import subprocess
import sys
import shutil
import threading

from time import sleep
from tkinter import LabelFrame, Frame, Checkbutton, Button, Entry, Label, Tk, StringVar, DoubleVar, IntVar, RIDGE, RAISED, SUNKEN, W, LEFT, messagebox
from tkinter.filedialog import askdirectory


# ******************
def mainProg(root, pathSrc, pathDst1, pathDst2, multiThread, timeInterval,
             silentThread, deleteSource, mailAdresse, waitExit, secureM,
             omitFile):
    # test number of destination entered
    numdest = 0
    if (pathDst1 != "") | (pathDst2 != ""):
        numdest = 1
        #ThreadTwo = False
    if (pathDst1 != "") & (pathDst2 != ""):
        numdest = 2
        #ThreadTwo = True
    # If only one destination enterd, attribute it to pathDst1
    if numdest == 1:
        if pathDst1 == "":
            pathDst1 = pathDst2
            pathDst2 = ""
    # Initialize the summary report
    globalSummary.set("Robocopy Folders:\n\nSource = " + pathSrc +
                      "\n<p>Target1 = " + pathDst1 + "\n<p>Target2 = " +
                      pathDst2 + "\n<p>")
    # write source and destination folders in txt file for next use
    target = open(paramFile, 'w')
    target.write(pathSrc + ";" + pathDst1 + ";" + pathDst2)
    target.close()

    # Starts the copy with Robocopy
    editSummary("\n<p>%H:%M:%S: Process started")

    # initialise Threads
    global Thread1
    Thread1 = threading.Thread()
    global Thread2
    Thread2 = threading.Thread()

    # Starts while loop which will stop when no change after given
    # time, then condition will be True
    condition = False
    checkTime = datetime.datetime.now()

    try:
        while condition == False:
            # ****Start Thread1********
            # Checks first that Thread1 is not running, otherwise skip the step.
            sameContent = compsubfolders(pathSrc, pathDst1, omitFile)
            if sameContent == False:
                editSummary(
                    "\n<p>%H:%M:%S: Source and destination(s) are different")
                checkTime = datetime.datetime.now()
                if Thread1.isAlive() == False | sameContent == False:
                    checkTime = datetime.datetime.now()
                    try:
                        Thread1 = threading.Thread(
                            target=worker,
                            args=(pathSrc, pathDst1, silentThread, secureM,
                                  omitFile))
                        Thread1.start()
                        editSummary("\n<p>%H:%M:%S: Copying to destination 1")
                    except:
                        editSummary("\n<p>%H:%M:%S: Problem with thread 1")
                        SendEmail(mailAdresse, "Robocopy Info: ERROR",
                                  "Please check Summary")
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
                            editSummary(
                                "\n<p>%H:%M:%S: Waiting for Thread1 to finish")
                            sleep(10)
                    # Start Thread2 now that Thread1 is done
                    sameContent = compsubfolders(pathSrc, pathDst2, omitFile)
                    if sameContent == False:
                        checkTime = datetime.datetime.now()
                        if Thread2.isAlive() == False:
                            try:
                                Thread2 = threading.Thread(
                                    target=worker,
                                    args=(pathSrc, pathDst2, silentThread,
                                          secureM, omitFile))
                                Thread2.start()
                                editSummary(
                                    "\n<p>%H:%M:%S: Copying to destination 2")
                            except:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with thread 2")
                                SendEmail(mailAdresse, "Robocopy Info: ERROR",
                                          "Please check Summary")
                        else:
                            pass

                else:
                    # Start Thread2 in parallel to Thread1
                    sameContent = compsubfolders(pathSrc, pathDst2, omitFile)
                    if sameContent == False:
                        checkTime = datetime.datetime.now()
                        if Thread2.isAlive() == False:
                            try:
                                Thread2 = threading.Thread(
                                    target=worker,
                                    args=(pathSrc, pathDst2, silentThread,
                                          secureM, omitFile))
                                Thread2.start()
                                editSummary(
                                    "\n<p>%H:%M:%S: Copying to destination2")
                            except:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with thread 2")
                                SendEmail(mailAdresse, "Robocopy Info: ERROR",
                                          "Please check Summary")
                        else:
                            pass

            # Wait next time-point before comparing folders
            editSummary("\n<p>%H:%M:%S: Waiting for " + str(timeInterval) +
                        " min before next Robocopy")
            sleep(int(timeInterval * 60))

            # Delete files in source folder
            if deleteSource:
                editSummary(
                    "\n<p>%H:%M:%S: Deleting source files that have been fully copied"
                )
                try:
                    for racine, directories, files in os.walk(pathSrc):
                        for myFile in files:
                            pathS = os.path.join(racine, myFile)
                            path1 = re.sub(pathSrc, pathDst1, pathS)
                            path2 = re.sub(pathSrc, pathDst2, pathS)
                            try:
                                if os.path.isfile(path1) & filecmp.cmp(
                                        pathS, path1) == True:
                                    if pathDst2 != "":
                                        if os.path.isfile(path2) & filecmp.cmp(
                                                pathS, path2) == True:
                                            try:
                                                os.remove(pathS)
                                            except:
                                                editSummary(
                                                    "\n<p>%H:%M:%S: " +
                                                    myFile +
                                                    " could not be deleted yet"
                                                )
                                        else:
                                            pass
                                    else:
                                        try:
                                            os.remove(pathS)
                                        except:
                                            editSummary(
                                                "\n<p>%H:%M:%S: " + myFile +
                                                " could not be deleted yet")
                                else:
                                    pass
                            except OSError as err:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with deleting files: OS error: {0}".
                                    format(err))
                            except ValueError:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with deleting files: could not convert data to an integer."
                                )
                            except:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with deleting files: Unexpected error:",
                                    sys.exc_info()[0])
                except:
                    pass

                # Now empty folders are deleted...
                emptyFolders = []
                try:
                    for racine, directories, files in os.walk(pathSrc):
                        emptyFolders.append(racine)
                    emptyFolders.sort(reverse=True)
                    for emptyFolder in emptyFolders[:-1]:
                        if os.listdir(emptyFolder) == []:
                            shutil.rmtree(emptyFolder)
                except:
                    editSummary(
                        "\n<p>%H:%M:%S: Problem with deleting folders\n")

            # Compare source and destination folders to determine
            # whether process should be stopped (i.e. no new file
            # created in Source folder) If no new file or folder was
            # created since the beginning of the robocopy, then the
            # condition is true and loop is terminated (= exit)
            exitTime = datetime.datetime.now()
            timeDiff = exitTime - checkTime
            if int(timeDiff.total_seconds()) >= int(waitExit * 60):
                checkTime = exitTime
                editSummary(
                    "\n\n<p>%H:%M:%S: Checking whether all folders are the same\n"
                )
                # Starts by checking if dst1 still connected and then compare content of folders
                if os.path.exists(pathDst1):
                    sameContent = compsubfolders(pathSrc, pathDst1, omitFile)
                    if sameContent == True:
                        editSummary(
                            "\n<p>%H:%M:%S: There is no file in source not found in destination 1"
                        )
                        # Continues with dst2 if it exists
                        if pathDst2 != "":
                            if os.path.exists(pathDst2):
                                sameContent = compsubfolders(
                                    pathSrc, pathDst2, omitFile)
                                if sameContent == True:
                                    editSummary(
                                        "\n<p>%H:%M:%S: There is no file in source not found in destination 2"
                                    )
                                    # Everything went fine both for dst1 and dst2 and there was no change during time lapse indicated
                                    condition = True
                            else:
                                editSummary(
                                    "\n<p>%H:%M:%S: Problem with comparing files in dst2\nCould not find dst2 folder"
                                )
                                SendEmail(mailAdresse, "Robocopy Info: ERROR",
                                          "Please check Summary")
                                # Everything went fine for dst1, dst2 seems not available anymore
                                #condition = True
                        else:
                            # Everything went fine for dst1 (no dst2
                            # had been entered by user) and there was
                            # no change during time lapse indicated
                            condition = True
                else:
                    editSummary(
                        "\n<p>%H:%M:%S: Problem with comparing files in dst1\nCould not find dst1 folder."
                    )
                    SendEmail(mailAdresse, "Robocopy Info: ERROR",
                              "Please check Summary")
                    # dst1 is not available anymore, no dst2 had been entered
                    #condition = True
    # Something went wrong at some unidentified step
    except OSError as err:
        editSummary("\n<p>%H:%M:%S: Problem: OS error: {0}".format(err))
        SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
    except ValueError:
        editSummary(
            "\n<p>%H:%M:%S: Problem: could not convert data to an integer.")
        SendEmail(mailAdresse, "Robocopy Info: ERROR", "Please check Summary")
    except:
        editSummary("\n<p>%H:%M:%S: Problem: Unexpected error: ",
                    sys.exc_info()[0])
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

    root.destroy()
    sys.exit()


# ******************
# FUNCTIONs from dialog box
def chooseSrcDir():
    global pathSrc
    pathSrc = askdirectory(
        initialdir=params[0], title="Please select a directory")
    srcTxt.set(pathSrc)
    params[0] = pathSrc


def chooseDst1Dir():
    global pathDst1
    pathDst1 = askdirectory(
        initialdir=params[1], title="Please select a directory")
    dst1Txt.set(pathDst1)
    params[1] = pathDst1


def chooseDst2Dir():
    global pathDst2
    pathDst2 = askdirectory(
        initialdir=params[2], title="Please select a directory")
    dst2Txt.set(pathDst2)
    params[2] = pathDst2


# ******************
# FUNCTIOn Do Copy!
def doCopy():
    # Checks that a source folder has been selected
    if srcTxt.get() == "":
        root2 = Tk()
        root2.withdraw()
        messagebox.showerror(
            title="Problem", message="You must select a source folder")
        root2.destroy()
    # Checks that at least one destination folder has been selected
    elif (dst1Txt.get() == "") & (dst2Txt.get() == ""):
        root2 = Tk()
        root2.withdraw()
        messagebox.showerror(
            title="Problem",
            message="You must select at least one destination folder")
        root2.destroy()
    else:
        filecmp._filter = _filter
        mainThread = threading.Thread(
            target=mainProg,
            args=(root, srcTxt.get(), dst1Txt.get(), dst2Txt.get(),
                  multiThr.get(), timeInt.get(), silentThr.get(),
                  deleteSrc.get(), mail.get(), timeExit.get(),
                  secureMode.get(), omitF.get()))
        mainThread.start()


# ******************
# FUNCTION Abort
def abort():
    print("Dialog Canceled")
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
    globalSummary.set(re.sub("<p>", "", globalSummary.get()))
    SendEmail(mail.get(), "Robocopy aborted by user", globalSummary.get())

    # Kill current running process
    process = psutil.Process()
    process.terminate()
    sys.exit()


# ******************
# FUNCTION: Workers / Threads
def worker(var1, var2, silent, secureM, omitFile):
    var3 = "*." + omitFile
    paramRobocopy = ["robocopy", var1, var2, "/XF", var3, "/e", "/COPY:DT"]
    #    paramRobocopy.append("/XF Oocyte.tif")
    if secureM == 1:
        paramRobocopy.append("/r:0")
        paramRobocopy.append("/w:30")
        paramRobocopy.append("/dcopy:T")
        paramRobocopy.append("/Z")

    if silent == 0:
        FNULL = open(os.devnull, 'w')
        subprocess.call(paramRobocopy, stdout=FNULL, stderr=subprocess.STDOUT)
    else:
        subprocess.call(paramRobocopy)


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
        print("Problem with logfile: " + logfileName)

    # Edit the summary for dialog window
    textTmp = globalSummary.get()
    for j in range(23):
        j = textTmp.rfind("<p>")
        if j >= 0:
            textTmp = textTmp[:j]
        else:
            j = 0
            break
    textTmp = re.sub("<p>", "", globalSummary.get()[j:])
    dialogSummary.set(textTmp)


# Define the path for saving the Log file
userName = getpass.getuser()
homeShare = os.environ.get('HOMESHARE')
userDirectory = os.path.expanduser('~')
logFilepath = os.path.join(userDirectory, 'Desktop')
if homeShare and os.path.exists(os.path.join(homeShare, 'Desktop')):
    logFilepath = os.path.join(homeShare, 'Desktop')

"""
# *******************************
# DIALOG WINDOW
# *******************************
"""
root = Tk()
root.title("Robocopy FAIM")
try:
    userName = get_display_name().split(",")
    mailAdresse = userName[1][1:] + "." + userName[0] + "@fmi.ch"
except:
    mailAdresse = "FirstName.LastName@fmi.ch"

"""
Frame for Option selection
"""
frameOptions = LabelFrame(
    frame1,
    width=380,
    height=235,
    text="Option Selection",
    borderwidth=2,
    relief=RAISED)
frameOptions.pack()
frameOptions.place(x=5, y=245)

# Options checkboxes

secureMode = IntVar()
secureMode.set(1)
secureMCheckBox = Checkbutton(
    frameOptions,
    text="Secure Mode (slower)",
    wraplength=200,
    variable=secureMode,
    anchor=W)
secureMCheckBox.pack()
secureMCheckBox.place(x=5, y=5)

multiThr = IntVar()
multiThr.set(0)
multiCheckBox = Checkbutton(
    frameOptions,
    text="Copy both destinations in parallel",
    wraplength=200,
    variable=multiThr,
    anchor=W)
multiCheckBox.pack()
multiCheckBox.place(x=5, y=30)

silentThr = IntVar()
silentThr.set(0)
silentCheckBox = Checkbutton(
    frameOptions,
    text="Show Robocopy console",
    wraplength=200,
    variable=silentThr,
    anchor=W)
silentCheckBox.pack()
silentCheckBox.place(x=5, y=55)

deleteSrc = IntVar()
deleteSrc.set(0)
delCheckBox = Checkbutton(
    frameOptions,
    text="Delete files in source folder after copy",
    wraplength=200,
    variable=deleteSrc,
    anchor=W)
delCheckBox.pack()
delCheckBox.place(x=5, y=80)

omitF = StringVar()
omitF.set("")
omitFLabel = Label(frameOptions, text="Omit files with extension:", anchor=W)
omitFLabel.pack()
omitFLabel.place(x=5, y=105)
omitFCheckBox = Entry(frameOptions, width=3, textvariable=omitF)
omitFCheckBox.pack()
omitFCheckBox.place(x=280, y=105)

# Time-lapse information
timeInt = DoubleVar()
timeInt.set(0.5)
tiLabel = Label(
    frameOptions,
    text="Time interval between Robocopy processes (min):",
    anchor=W)
tiLabel.pack()
tiLabel.place(x=5, y=130)
tiText = Entry(frameOptions, width=6, textvariable=timeInt)
tiText.pack()
tiText.place(x=280, y=132)

# Time-Exit information
timeExit = DoubleVar()
timeExit.set(5)
tiexLabel = Label(
    frameOptions,
    text="Time for exiting if no change in folders (min):",
    anchor=W)
tiexLabel.pack()
tiexLabel.place(x=5, y=155)

tiexText = Entry(frameOptions, width=6, textvariable=timeExit)
tiexText.pack()
tiexText.place(x=280, y=157)

# E-mail information
mail = StringVar()
mail.set(mailAdresse)
sendLabel = Label(frameOptions, text="Send Summary to:", anchor=W)
sendLabel.pack()
sendLabel.place(x=5, y=180)
adresseText = Entry(frameOptions, justify=LEFT, width=25, textvariable=mail)
adresseText.pack()
adresseText.place(x=115, y=182)
"""
Frame for Summary
"""
frameSummary = LabelFrame(
    frame1,
    width=380,
    height=475,
    text="Summary",
    borderwidth=2,
    relief=RAISED)
frameSummary.pack()
frameSummary.place(x=395, y=5)

# Summary
dialogSummary = StringVar()
globalSummary = StringVar()
dialogSummary.set("*** Summary window *****")
globalSummary.set("")
sumLabel = Label(
    frameSummary, textvariable=dialogSummary, justify=LEFT, anchor=W, width=50)
sumLabel.pack()
sumLabel.place(x=5, y=5)

# Do Copy and Cancel buttons
doCopyButton = Button(
    frame1,
    text='Do Copy !',
    width=8,
    overrelief=RIDGE,
    font="arial 10",
    command=doCopy)
doCopyButton.config(bg="yellow green", fg="black")
doCopyButton.pack()
doCopyButton.place(x=10, y=495)
cancelButton = Button(
    frame1,
    text='Abort',
    width=8,
    overrelief=RIDGE,
    font="arial 10",
    command=abort)
cancelButton.config(bg="tomato", fg="black")
cancelButton.pack()
cancelButton.place(x=100, y=495)

# Show Dialog Window
root.mainloop()
