import tkinter as tk
from tkinter import ttk, messagebox
import os
import numpy as np
import os
from datetime import datetime
from alerts.EmailNotify import send_email  # Import the send_email function
from alerts.SMSNotify import send_sms

# Functionality to start/stop detection
detection_running = False
cap = None
last_popup_time = 0  # Track the last popup time
popup_interval = 10  # Interval in seconds to show repeated alerts

import os
import importlib.util

# Define detection_running as a global variable
detection_running = False  # Initially, detection is not running

def start_detection():
    global detection_running  # Declare the global variable

    if detection_running:
        # If detection is already running, show a message
        messagebox.showinfo("Info", "Detection is already running!")
        return
    
    if os.path.isfile("detection/human_detections.py"):
        # Dynamically load the module
        spec = importlib.util.spec_from_file_location("human_detections", "detection/human_detections.py")
        human_detections = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(human_detections)  # Blocking: runs the full detection loop to completion
            detection_running = True  # Set detection_running to True when detection starts
            status_label.config(text="Status: Running", foreground="green")
            return True
        except Exception as e:
            print(f"Error executing functions from human_detections.py: {e}")
            return False
    else:
        print("File 'detection/human_detections.py' not found.")
        return False

# This will allow you to check if detection is running in other parts of the program
def stop_detection():
    global detection_running
    detection_running = False  # Set the flag to False to stop the detection
    status_label.config(text="Status: Stopped", foreground="red")
    print("Detection stopped.")
    return
    

def open_report(report_type):
    file_name = "static/detection_report.html" if report_type == "HTML" else "static/detection_report.txt"
    if os.path.exists(file_name):
        os.startfile(file_name)
    else:
        messagebox.showerror("Error", f"{file_name} does not exist. Please generate a report first.")


# GUI Setup
root = tk.Tk()
root.title("Human Presence Detection System")
root.geometry("900x600")
root.configure(bg="#2c3e50")

# Adding styles
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", font=("Helvetica", 14, "bold"), padding=10)
style.map("TButton", foreground=[("active", "#ffffff")], background=[("active", "red")])

# Gradient background
canvas = tk.Canvas(root, width=900, height=600)
canvas.pack(fill="both", expand=True)
canvas.create_rectangle(0, 0, 900, 600, fill="#4CAF50", outline="")

# Title Label
title_label = tk.Label(root, text="Human Presence Detection System",
                       font=("Helvetica", 26, "bold"), bg="#4CAF50", fg="black")
title_label.place(x=150, y=40, width=600)

# Status Label
status_label = tk.Label(root, text="Click to function", font=("Helvetica", 16), bg="#4CAF50", fg="red")
status_label.place(x=370, y=120)

# Control Buttons
start_button = ttk.Button(root, text="Detect Now", command=start_detection)
start_button.place(x=335, y=200, width=220, height=60)

# Report Buttons
text_report_button = ttk.Button(root, text="View Text Report", command=lambda: open_report("Text"))
text_report_button.place(x=335, y=280, width=220, height=60)

html_report_button = ttk.Button(root, text="View HTML Report", command=lambda: open_report("HTML"))
html_report_button.place(x=335, y=360, width=220, height=60)

# Footer
footer_label = tk.Label(root, text="Developed by Team Trio", font=("Helvetica", 12, "italic"),
                        bg="#34495e", fg="#ecf0f1")
footer_label.place(x=350, y=450, width=200)

# Run the Tkinter app
root.mainloop()