import cv2
import numpy as np
import time
import sqlite3
import os
import sys
from datetime import datetime

# Allow `alerts` (a sibling package at the project root) to be imported
# regardless of whether this file is run directly, via `-m`, or exec'd
# in-process by gui.py.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alerts.EmailNotify import send_email  # Import the send_email function
from alerts.SMSNotify import send_sms  # Import the send_sms function

# Database setup (Create a connection and table if it doesn't exist)
db_name = 'detection_reports.db'

def setup_database():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            detection_status TEXT,
            frame_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_detection_to_db(status, frame_path):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("INSERT INTO reports (timestamp, detection_status, frame_path) VALUES (?, ?, ?)", 
                   (timestamp, status, frame_path))
    conn.commit()
    conn.close()

def generate_text_report():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10")  # Fetch last 10 events
    rows = cursor.fetchall()
    
    with open("static/detection_report.txt", "w") as report:
        report.write("Recent Detection Events:\n")
        report.write("-" * 30 + "\n")
        for row in rows:
            report.write(f"ID: {row[0]}, Timestamp: {row[1]}, Status: {row[2]}, Frame Path: {row[3]}\n")
        report.write("-" * 30 + "\n")
    conn.close()

def generate_html_report():
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10")  # Fetch last 10 events
    rows = cursor.fetchall()

    # Create HTML report
    with open("static/detection_report.html", "w") as html_report:
        html_report.write("<html><head><title>Detection Report</title>")
        html_report.write("<style>")
        html_report.write("body { font-family: Arial,sans-serif;margin:0;padding:20px;background-color: #f7f7f7;color: #333; }")
        html_report.write("h2 { color: #4CAF50;text-align: center;}")
        html_report.write("table { width: 100%;border-collapse: collapse;margin: 20px 0;background-color: #fff;box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);}")
        html_report.write("table, th, td { border: 1px solid #ddd; padding: 10px; }")
        html_report.write("th { background-color: #4CAF50; color: white;text-align: left; }")
        html_report.write("tr:nth-child(even) { background-color: #f9f9f9; }")
        html_report.write("tr:hover{background-color: #f1f1f1;}")
        html_report.write("td a { color: #4CAF50;text-decoration: none;}")
        html_report.write(" td a:hover {text-decoration: underline;}")
        html_report.write("</style>")
        html_report.write("</head><body>")
        html_report.write("<h2>Recent Detection Events</h2>")
        html_report.write("<table>")
        html_report.write("<tr><th>ID</th><th>Timestamp</th><th>Status</th><th>Frame Path</th></tr>")

        for row in rows:
            html_report.write("<tr>")
            html_report.write(f"<td>{row[0]}</td>")
            html_report.write(f"<td>{row[1]}</td>")
            html_report.write(f"<td>{row[2]}</td>")
            html_report.write(f"<td><a target='_blank' href='{row[3]}' >View Frame</a></td>")
            html_report.write("</tr>")

        html_report.write("</table>")
        html_report.write("</body></html>")
    conn.close()

# Set up the database and table
setup_database()

# Load YOLO
net = cv2.dnn.readNet("yolov3.weights", "detection/yolov3.cfg")
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]

# Load COCO class labels
with open("detection/coco.names", "r") as f:
    classes = [line.strip() for line in f.readlines()]

# Initialize video capture
cap = cv2.VideoCapture(0)

# Add a start-up delay to allow the camera to stabilize (e.g., 2 seconds)
time.sleep(2)

# Add a global flag to manage detection state
detection_running = True  # Initially, detection is running

"""
def stop_detection():
    global detection_running
    detection_running = False  # Set flag to False to stop detection
    cap.release()
    cv2.destroyAllWindows()
"""
# Initialize notification cooldowns and detection consistency checks
last_email_time = 0
last_sms_time = 0
email_cooldown = 120  # seconds
sms_interval = 120  # seconds
detection_start_time = None  # To track consistent detection
consistent_detection_duration = 3  # Minimum time in seconds for consistent detection

output_folder = "static/frames"
os.makedirs(output_folder, exist_ok=True)  # Ensure output folder exists

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture video")
        break

    height, width, channels = frame.shape

    # Preprocess the image for YOLO
    blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)

    # Store detection information
    class_ids = []
    confidences = []
    boxes = []
    human_detected = False  # Reset human detection for each frame

    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]

            # Detect 'person' with confidence above 0.3
            if confidence > 0.3 and classes[class_id] == "Human":
                human_detected = True  # Mark human presence as detected

                # Get bounding box coordinates
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)

                # Save detections
                boxes.append([x, y, w, h])
                confidences.append(float(confidence))
                class_ids.append(class_id)

    # Non-max suppression to eliminate redundant overlapping boxes
    indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

    # Draw bounding boxes for detected humans
    for i in range(len(boxes)):
        if i in indexes:
            x, y, w, h = boxes[i]
            label = str(classes[class_ids[i]])
            confidence = confidences[i]
            color = (0, 255, 0)  # Green for human detection
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, f"{label} {round(confidence, 2)}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    # Display the output frame
    cv2.imshow("Human Detection", frame)

    # Check if human was detected and maintain consistent detection for a specific duration
    if human_detected:
        if detection_start_time is None:
            detection_start_time = time.time()  # Set the detection start time

        # Check if the human has been detected consistently for the required duration
        if time.time() - detection_start_time >= consistent_detection_duration:
            current_time = time.time()

            # Save frame for logging
            frame_path = os.path.join(output_folder, f"frame_{int(current_time)}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Frame saved as {frame_path}")

            # Log the detection to the database
            log_detection_to_db("Human Detected", frame_path)

            # Flask app will handle the HTML rendering
            print("Detection logged and Flask server can display the report.")

            # Generate reports after logging
            generate_text_report()
            generate_html_report()  # Generate the HTML report

            # Send email if the cooldown period has passed
            if current_time - last_email_time > email_cooldown:
                subject = "Human Detected⚠️"
                body = "WARNING⚠️ \nHuman presence has been detected in the CCTV!"
                recipients = os.environ["EMAIL_RECIPIENTS"].split(",")
                send_email(subject, body, recipients)
                last_email_time = current_time  # Update the last email time

            # Send SMS if the interval has passed
            if current_time - last_sms_time > sms_interval:
                send_sms()  # Call the send_sms function
                last_sms_time = current_time  # Update the last SMS time

            # Reset the detection start time to avoid repeated notifications
            detection_start_time = None
    else:
        # Reset detection start time if human is not detected
        detection_start_time = None

    # Break the loop with the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video capture and close all windows
cap.release()
cv2.destroyAllWindows()