from flask import Flask, request, render_template_string, redirect, url_for, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder="static")

DB_NAME = 'detection_reports.db'

# Route to delete a frame
@app.route('/delete_frame/<filename>', methods=['POST'])
def delete_frame(filename):
    file_path = os.path.join("static", "frames", filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for('view_report'))  # Redirect to the report
    return "File not found", 404

# Route to serve the report
@app.route('/view_report')
def view_report():
    # Serve the HTML report dynamically
    report_path = "static/detection_report.html"
    if os.path.exists(report_path):
        return send_from_directory(directory="static", path="detection_report.html")
    return "No report found. Please run the detection process first."

# Function to fetch records from the database
def fetch_records():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Function to delete a record by ID
def delete_record(record_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reports WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()

@app.route('/')
def index():
    records = fetch_records()
    # Render the HTML with the records
    return render_template_string(generate_html(records))

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete(record_id):
    delete_record(record_id)
    return redirect(url_for('index'))

# Generate HTML dynamically
def generate_html(records):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Detection Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f7f7f7; color: #333; }
            h2 { text-align: center; color: #4CAF50; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #fff; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); }
            table, th, td { border: 1px solid #ddd; padding: 10px; text-align:center; }
            th { background-color: #4CAF50; color: white; text-align: center; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            tr:hover { background-color: #f1f1f1; }
            .delete-btn { 
                color: white; 
                background-color: #4CAF50; 
                text-decoration: none; 
                padding: 10px 20px;  /* Adjust padding for balanced spacing */
                display: inline-block;  /* To keep button size fixed */
                border: none;
                cursor: pointer;
                font-size: 16px;
                text-align: center;
                margin: 0 auto;  /* Centers the button in the table cell */
                width: auto;  /* Button width is dynamic */
            }
            .delete-btn:hover {
                background-color: red;
            }

            /* Modal Styles */
            .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
            .modal-content { background-color: white; padding: 20px; text-align: center; border-radius: 5px; width: 300px; }
            .btn { padding: 10px 20px; margin: 10px; cursor: pointer; }
            .btn-danger { background-color:#4CAF50 ; color: white; border: none; }
            .btn-secondary { background-color: gray; color: white; border: none; }
            .btn-danger:hover { background-color:red ;}
            .btn-secondary:hover { background-color:black ;}
        </style>
        <script>
            function confirmDelete(event, recordId) {
                event.preventDefault();  // Prevent form submission until confirmation
                document.getElementById("deleteModal").style.display = "flex";  // Show the modal
                document.getElementById("confirmDeleteBtn").onclick = function() {
                    // Now submit the form for deletion
                    document.getElementById("deleteForm").action = "/delete/" + recordId;  // Dynamically set the form action
                    document.getElementById("deleteForm").submit();  // Submit the form
                };
            }

            function closeModal() {
                document.getElementById("deleteModal").style.display = "none";  // Close the modal if cancelled
            }
        </script>
    </head>
    <body>
        <h2>Recent Detection Events</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Timestamp</th>
                <th>Status</th>
                <th>Frame Path</th>
                <th>Action</th>
            </tr>
    """
    for row in records:
        html += f"""
            <tr>
                <td>{row[0]}</td>
                <td>{row[1]}</td>
                <td>{row[2]}</td>
                <td><a href="{row[3]}" target="_blank">View Frame</a></td>
                <td>
                    <!-- Form for deleting a record -->
                    <form id="deleteForm" method="POST" style="display:inline;" onsubmit="confirmDelete(event, {row[0]})">
                        <button type="submit" class="delete-btn">Delete</button>
                    </form>
                </td>
            </tr>
        """
    html += """
        </table>

        <!-- Modal for Delete Confirmation -->
        <div id="deleteModal" class="modal">
            <div class="modal-content">
                <h3>Are you sure you want to delete this frame?</h3>
                <button class="btn btn-danger" id="confirmDeleteBtn">Yes, Delete</button>
                <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
            </div>
        </div>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    app.run(debug=True)
