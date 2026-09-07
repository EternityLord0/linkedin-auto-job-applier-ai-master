#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from src.data.csv_manager import CSVManager
from src.data.status_manager import status_manager, VALID_STATUSES
from src.data.question_cache import question_cache
from src.utils.logger import logger

app = Flask(__name__)
CORS(app)

# Centralized data manager
csv_manager = CSVManager()


@app.route('/')
def home():
    """Displays the home page of the application (Dashboard)."""
    return render_template('index.html')


@app.route('/applied-jobs', methods=['GET'])
def get_applied_jobs():
    """
    Retrieves a list of applied jobs from the applications history CSV file
    enriched with live CRM status from status_manager.
    """
    try:
        jobs = csv_manager.get_all_applied_jobs_for_ui()
        if not jobs:
            return jsonify([]), 200

        formatted_jobs = []
        for row in jobs:
            formatted_jobs.append({
                'Job_ID': row.get('Job ID', ''),
                'Title': row.get('Title', ''),
                'Company': row.get('Company', ''),
                'Work_Location': row.get('Work Location', 'Unknown'),
                'Work_Style': row.get('Work Style', 'Unknown'),
                'Resume': row.get('Resume', 'Padrão'),
                'Status': row.get('Status', 'Candidatado'),
                'Notes': row.get('Notes', ''),
                'Status_Updated_At': row.get('Status_Updated_At', ''),
                'HR_Name': row.get('HR Name', ''),
                'HR_Link': row.get('HR Link', ''),
                'Job_Link': row.get('Job Link', ''),
                'External_Job_link': row.get('External Job link', ''),
                'Date_Applied': row.get('Date Applied', '')
            })

        return jsonify(formatted_jobs)
    except Exception as e:
        logger.error(f"Error fetching applied jobs for UI: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/applied-jobs/<job_id>/status', methods=['PUT', 'POST'])
def update_applied_job_status(job_id):
    """
    Updates the CRM pipeline status of a specific job application.
    Supports Kanban drag-and-drop and Table dropdown selector.
    """
    try:
        data = request.get_json(force=True) or {}
        new_status = data.get('status')
        notes = data.get('notes')

        if not new_status:
            return jsonify({"error": "Field 'status' is required"}), 400

        if new_status not in VALID_STATUSES:
            return jsonify({"error": f"Invalid status. Choose one of: {VALID_STATUSES}"}), 400

        success = status_manager.set_status(job_id, new_status, notes=notes)
        if success:
            return jsonify({
                "success": True,
                "job_id": job_id,
                "status": new_status,
                "message": f"Job {job_id} updated to '{new_status}' successfully"
            }), 200
        else:
            return jsonify({"error": "Failed to update status"}), 500

    except Exception as e:
        logger.error(f"Error updating job status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/statuses', methods=['GET'])
def get_available_statuses():
    """Returns the list of valid CRM statuses for the UI."""
    return jsonify(VALID_STATUSES)


@app.route('/api/cache-questions', methods=['GET', 'POST'])
def handle_cache_questions():
    """Endpoint to inspect or add custom pre-answered questions to answered_questions.json."""
    if request.method == 'GET':
        return jsonify(question_cache.cache)
    elif request.method == 'POST':
        data = request.get_json(force=True) or {}
        question = data.get('question')
        answer = data.get('answer')
        if not question or not answer:
            return jsonify({"error": "Both 'question' and 'answer' are required"}), 400
        question_cache.save_answer(question, str(answer))
        return jsonify({"success": True, "message": f"Cached: '{question}' -> '{answer}'"})


if __name__ == '__main__':
    logger.info("Starting Web Server Dashboard on http://127.0.0.1:5000")
    app.run(debug=True, port=5000)