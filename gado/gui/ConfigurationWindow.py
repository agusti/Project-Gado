import sys, ttk, Pmw, time, tkMessageBox
from Tkinter import *
from gado.functions import *
import gado.messages as messages

INPUT_TRAY_LOCATION = 'arm_in_value'
OUTPUT_TRAY_LOCATION = 'arm_out_value'
SCANNER_LOCATION = 'arm_home_value'
SCANNER_HEIGHT = 'actuator_home_value'

class ConfigurationWindow():
    def __init__(self, root, q, l):
        self.q = q
        self.l = l
        
        window = Toplevel(root)
        window.title("Manage Artifact Sets")
        self.window = window
        
        window.title("Configure Your Setup")
        
        mylabel = Label(window)
        mylabel["text"] = "Set the locations for your current setup"
        mylabel.grid(row=0, column=0, sticky=N+S+E+W, padx=10, pady=5)
        
        button_input = Button(window)
        button_input["text"] = "Input Tray Location"
        button_input["command"] = lambda: self._launch_dialog(INPUT_TRAY_LOCATION)#dialog.deiconify
        button_input.grid(row=1, column=0, sticky=N+S+E+W, padx=10, pady=5)
        
        button_scanner = Button(window)
        button_scanner["text"] = "Scanner Location"
        button_scanner["command"] = lambda: self._launch_dialog(SCANNER_LOCATION)#dialog.deiconify
        button_scanner.grid(row=2, column=0, sticky=N+S+E+W, padx=10, pady=5)
        
        button_output = Button(window)
        button_output["text"] = "Output Tray Location"
        button_output["command"] = lambda: self._launch_dialog(OUTPUT_TRAY_LOCATION)#dialog.deiconify
        button_output.grid(row=3, column=0, sticky=N+S+E+W, padx=10, pady=5)
        
        button_height = Button(window)
        button_height["text"] = "Scanner Height"
        button_height["command"] = lambda: self._launch_dialog(SCANNER_HEIGHT)#dialog.deiconify
        button_height.grid(row=4, column=0, sticky=N+S+E+W, padx=10, pady=5)
        
        window.protocol("WM_DELETE_WINDOW", self.window.withdraw)
        window.withdraw()
        
        self._create_dialog(root)
        self.new_actuator_position = None
        self.new_arm_position = None
    
    def show(self):
        self.window.deiconify()
    
    def _create_dialog(self, root):
        dialog = Toplevel(root)
        self.dialog = dialog
        dialog.title("Instructions")
        
        dialog.bind("<Key>", self._keyboard_callback)
        
        #Label to tell user what's up
        configLabel = Label(dialog)
        configLabel["text"] = "Using the arrow keys, move the arm of the robot to the desired location\n\nWhen finished hit Done"
        configLabel.grid(row=0, column=0, sticky=N+S+E+W, padx=10, pady=10)
        
        #Done button
        doneButton = Button(dialog)
        doneButton["text"] = "Done"
        doneButton["command"] = self._save_config #  DOESN'T EXIST YET
        doneButton.grid(row=1, column=0, sticky=N+S+E+W, padx=10, pady=5)
    
        dialog.protocol("WM_DELETE_WINDOW", dialog.withdraw)
        dialog.withdraw()
    
    def _launch_dialog(self, parameter):
        #Expose the configDialog window
        self._lastTime = time.time()
        self.active_conf_param = parameter
        self.dialog.deiconify()
    
    def _save_config(self):
        acp = self.active_conf_param
        args = dict()
        if acp.find('arm') >= 0 and self.new_arm_position:
            args[acp] = self.new_arm_position
            export_settings(**args)
        elif acp.find('actuator') >= 0 and self.new_actuator_position:
            args[acp] = self.new_actuator_position
            export_settings(**args)
        
        add_to_queue(self.q, self.l, messages.RELOAD_SETTINGS)
        fetch_from_queue(self.q, self.l, messages.RETURN)
        self.dialog.withdraw()
    
    def _configuring_arm(self):
        return self.active_conf_param.find('arm') >= 0
    
    def _keyboard_callback(self, event):

        # Delay between robot commands for consistent behavior
        t = time.time()
        l = self.l
        q = self.q
        if t - self._lastTime > 0.1:
            key = event.keycode
            if self._configuring_arm():
                if key == 37:
                    #Left arrow press
                    add_to_queue(q, l, messages.MOVE_LEFT)
                    msg = fetch_from_queue(q, l, messages.RETURN)
                    self.new_arm_position = msg[1]
                elif key == 39:
                    #Right arrow press
                    add_to_queue(q, l, messages.MOVE_RIGHT)
                    msg = fetch_from_queue(q, l, messages.RETURN)
                    self.new_arm_position = msg[1]
            else:
                if key == 38:
                    #Up arrow press
                    add_to_queue(q, l, messages.MOVE_DOWN)
                    msg = fetch_from_queue(q, l, messages.RETURN)
                    self.new_actuator_position = msg[1]
                elif key == 40:
                    #Down arrow press
                    add_to_queue(q, l, messages.MOVE_UP)
                    msg = fetch_from_queue(q, l, messages.RETURN)
                    self.new_actuator_position = msg[1]
            
            self._lastTime = t