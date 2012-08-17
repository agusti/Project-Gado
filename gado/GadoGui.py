import sys
from Tkinter import *
import tkMessageBox
import Image, ImageTk
import ttk
#from gado.ProgressMeter import *
import Pmw
import time
import platform
from gado.Robot import Robot
from gado.functions import *
from gado.gui.ManageSets import ManageSets
from gado.gui.ConfigurationWindow import ConfigurationWindow
import gado.messages as messages
from threading import Thread

class GuiListener(Thread):
    def __init__(self, q, l, gui):
        self.gui = gui
        self.q = q
        self.l = l
        Thread.__init__(self)

    def run(self):
        while True:
            msg = fetch_from_queue(self.q, self.l)
            print 'GuiListener\tFetched message %s' % str(msg)
            if msg[0] == messages.SET_SCANNER_PICTURE:
                self.gui.changeScannedImage(msg[1])
            elif msg[0] == messages.SET_WEBCAM_PICTURE:
                self.gui.changeWebcamImage(msg[1])
            elif msg[0] == messages.SET_STATUS_TEXT:
                self.gui.changeStatusText(msg[1])
            else:
                add_to_queue(self.q, self.l, msg[0], (msg[1] if len(msg) > 1 else None))

class GadoGui(Frame):
    
    #Widgets
    global artifactSetDropDown
    
    #These have to be globals in order to avoid garbage collection bug in TkImage class
    global frontImage
    global backImage
    
    global frontImageLabel
    global backImageLabel
    
    def __init__(self, root, q, l):
        # Create the root frame
        self.root = root
        self.q = q
        self.l = l
        self.t1 = GuiListener(q, l, self)
        
        #Initialize the master frame
        Frame.__init__(self, self.root)
    
    def load(self):
        print 'GadoGui\tfetch_from_queue READY'
        #fetch_from_queue(self.q, self.l, messages.READY)
        print 'GadoGui\tfetch_from_queue DONE'
        
        self.manage_sets = ManageSets(self.root, self.q, self.l)
        self.selected_set = None
        self.config_window = ConfigurationWindow(self.root, self.q, self.l)
        
        #Create all menus for application
        self.createMenus(self.root)
        
        #Pack the widgets and create the GUI
        self.pack()
        self.createWidgets()
        
        self.t1.start()
        
    #################################################################################
    #####                           MENU FUNCTIONS                              #####
    #################################################################################
    
    def createMenus(self, master=None):
        #Create the drop down menu
        self.menubar = Menu(master)
        
        #Create the file menu
        self.fileMenu = self.createFileMenu(self.menubar, master)
        
        #Create the Settings menu
        self.settingsMenu = self.createSettingsMenu(self.menubar, master)
        
        #Add both menus to the menubar
        self.menubar.add_cascade(label="File", menu=self.fileMenu)
        self.menubar.add_cascade(label="Settings", menu=self.settingsMenu)
        
        #Assign menubar
        master.config(menu=self.menubar)
        
    def createFileMenu(self, menubar=None, master=None):
        
        self.fileMenu = Menu(self.menubar, tearoff=0)
        self.fileMenu.add_command(label="Quit", command=master.quit)
        
        return self.fileMenu
    
    def createSettingsMenu(self, menubar=None, master=None):
        
        self.settingsMenu = Menu(self.menubar, tearoff=0)
        self.settingsMenu.add_command(label="Configure Layout", command=self.config_window.show)
        
        return self.settingsMenu
        
    #################################################################################
    #####                           WIDGET FUNCTIONS                            #####
    #################################################################################
    
    def createWidgets(self):
        
        #Create the artifactSet section
        self.createArtifactSetWidgets()
        
        #Create the Control section
        self.createControlWidgets()
        
        #Create the status center
        self.createStatusWidgets()
        
        #Create the image display widgets
        self.createImageDisplayWidgets()
    
    def createArtifactSetWidgets(self):
        #Create label
        artifactSetLabel = Label(self)
        artifactSetLabel["text"] = "Artifact Set: "
        artifactSetLabel.grid(row=0, column=0, sticky=W, padx=10, pady=5, columnspan=2)
        
        #Create dropdown for selecting an artifact set
        set_dropdown = Pmw.ComboBox(self, selectioncommand=self.set_selected_set)
        set_dropdown.grid(row=1, column=0, sticky=N+S+E+W, padx=10, pady=5, columnspan=1)
        self.set_dropdown = set_dropdown
        self._populate_set_dropdown()
        
        # Add the button to create a new artifact set
        new_set_button = Button(self)
        new_set_button["text"] = "New Artifact Set"
        new_set_button["command"] = self.manage_sets.show
        new_set_button.grid(row=1, column=1, sticky=N+S+E+W, padx=10, pady=5, columnspan=1)
    
    def set_selected_set(self, a):
        idx = self.set_dropdown.curselection()[0]
        self.selected_set = self.weighted_sets[int(idx)][0]
        if not self.selected_set:
            tkMessageBox.showerror("Invalid Set Selection", "Please select a valid set, or create a new one.")
        else:
            add_to_queue(self.q, self.l, messages.SET_SELECTED_ARTIFACT_SET, self.selected_set)
            print 'GadoGui\tadded to queue, trying to pull from queue now'
            fetch_from_queue(self.q, self.l, messages.RETURN)
            print 'GadoGui\tfetched return from queue'
    
    def createControlWidgets(self):
        #Create label
        self.controlLabel = Label(self)
        self.controlLabel["text"] = "Control: "
        self.controlLabel.grid(row=0, column=2, sticky=W, padx=10, pady=5)
        
        #Create start/stop/pause/restart buttons
        self.startButton = Button(self)
        self.startButton["text"] = "Start"
        self.startButton["command"] = self.startRobot
        self.startButton.grid(row=1, column=2, sticky=N+S+E+W, padx=10, pady=5)
        
        self.pauseButton = Button(self)
        self.pauseButton["text"] = "Pause"
        self.pauseButton["command"] = self.pauseRobot
        self.pauseButton.grid(row=1, column=3, sticky=N+S+E+W, padx=10, pady=5)
        
        self.stopButton = Button(self)
        self.stopButton["text"] = "Stop"
        self.stopButton["command"] = self.stopRobot
        self.stopButton.grid(row=1, column=4, sticky=N+S+E+W, padx=10, pady=5)
        
        self.resetButton = Button(self)
        self.resetButton["text"] = "Reset"
        self.resetButton["command"] = self.resetRobot
        self.resetButton.grid(row=1, column=5, sticky=N+S+E+W, padx=10, pady=5)
        
    def createStatusWidgets(self):
        #Create label
        self.statusLabel = Label(self)
        self.statusLabel["text"] = "Status: "
        self.statusLabel.grid(row=4, column=0, sticky=W, padx=10, pady=5)
        
        #Actual message box
        self.messageEntry = Entry(self)
        self.messageEntry.grid(row=5, column=0, columnspan=6, sticky=N+S+E+W, padx=10, pady=5)
        
    def createImageDisplayWidgets(self):
        #Scanner label
        self.scannerLabel = Label(self)
        self.scannerLabel["text"] = "Scanner Image:"
        self.scannerLabel.grid(row=2, column=0, sticky=W, padx=10, pady=5)
        
        self.webCamLabel = Label(self)
        self.webCamLabel["text"] = "Webcam Image:"
        self.webCamLabel.grid(row=2, column=2, sticky=W, padx=10, pady=5)
        
        image = Image.open("test.jpg")
        image.thumbnail((500, 500), Image.ANTIALIAS)
        
        image2 = Image.open("test.jpg")
        image2.thumbnail((500,500), Image.ANTIALIAS)
        
        self.frontImage = ImageTk.PhotoImage(image)
        self.backImage = ImageTk.PhotoImage(image2)
        
        self.frontImageLabel = Label(self, image=self.frontImage)
        self.frontImageLabel.photo = self.frontImage
        self.frontImageLabel.grid(row=3, column=0, sticky=N+S+E+W, padx=10, pady=5, columnspan=2)
        
        self.backImageLabel = Label(self, image=self.backImage)
        self.backImageLabel.photo = self.backImage
        self.backImageLabel.grid(row=3, column=2, sticky=N+S+E+W, padx=10, pady=5, columnspan=4)
        
        
    #################################################################################
    #####                           FUNCTION WRAPPERS                           #####
    #################################################################################
    
    def _refresh(self):
        self.set_dropdown.delete(0, 'end')
        self._populate_set_dropdown()
    
    def _populate_set_dropdown(self):
        add_to_queue(self.q, self.l, messages.WEIGHTED_ARTIFACT_SET_LIST)
        msg = fetch_from_queue(self.q, self.l, messages.RETURN)
        self.weighted_sets = msg[1]
        for id, indented_name in self.weighted_sets:
            self.set_dropdown.insert('end', indented_name)
    
    def connectToRobot(self):
        add_to_queue(self.q, self.l, messages.ROBOT_CONNECT)
        msg = fetch_from_queue(self.q, self.l, messages.RETURN, timeout=30)
        success = msg[1]
        if success:
            tkMessageBox.showinfo("Connection Status", "Successfully connected to Gado!")
        else:
            tkMessageBox.showerror("Connection Status", "Could not connect to Gado, please ensure it is on and plugged into the computer")
        return success
    
    def startRobot(self):
        #Function call to start robot's operation
        print "GadoGui\tStarting robot..."
        self.q.put((messages.START, ))
        
    def pauseRobot(self):
        #Function call to pause robot's operation
        print "GadoGui\tPausing robot..."
        self.q.put((messages.LAST_ARTIFACT, ))
    
    def resumeRobot(self):
        self.q.put((messages.START, ))
    
    def stopRobot(self):
        #Function call to stop robot's operation
        print "Stopping robot..."
        self.q.put((messages.STOP, ))
        
    def resetRobot(self):
        #Function call to reset the robot's operations
        print "Restarting robot..."
        self.q.put((messages.RESET, ))
        
    #Image transferring functions
    
    def changeScannedImage(self, imagePath):
        #Open image from passed path and resize it (preserving ratio) to fit in GUI
        try:
            image = Image.open(imagePath)
            image.thumbnail((500, 500), Image.ANTIALIAS)
            
            self.frontImage = ImageTk.PhotoImage(image)
            
            self.frontImageLabel = Label(self, image=self.frontImage)
            self.frontImageLabel.photo = self.frontImage
            self.frontImageLabel.grid(row=3, column=0, sticky=N+S+E+W, padx=10, pady=5, columnspan=2)
            
        except:
            print "Error updating scanner image in gui thread..."
        
    def changeWebcamImage(self, imagePath):
        try:
            image = Image.open(imagePath)
            image.thumbnail((500,500), Image.ANTIALIAS)
            
            self.backImage = ImageTk.PhotoImage(image)
            
            self.backImageLabel = Label(self, image=self.backImage)
            self.backImageLabel.photo = self.backImage
            self.backImageLabel.grid(row=3, column=2, sticky=N+S+E+W, padx=10, pady=5, columnspan=2)
        except:
            print "Error updating webcam image in gui thread..."