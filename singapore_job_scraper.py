from flask import Flask, render_template, request, jsonify, send_file
from singapore_job_scraper import SingaporeJobScraper
import os
import pandas as pd
import threading
import uuid
import json
from datetime import datetime

app = Flask(__name__)

# Directory to store job scraping results
RESULTS_DIR = "job_results"
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

# Store scraping tasks
tasks = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    try:
        data = request.json
        keywords = data.get('keywords', [])
        search_term = data.get('search_term', '')
        
        if not keywords:
            return jsonify({'error': 'Keywords are required'}), 400
        
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        
        # Create a task object
        task = {
            'id': task_id,
            'status': 'running',
            'keywords': keywords,
            'search_term': search_term,
            'start_time': datetime.now().isoformat(),
            'results_file': None,
            'job_count': 0
        }
        
        tasks[task_id] = task
        
        # Start scraping in a background thread
        thread = threading.Thread(target=run_scraper, args=(task_id, keywords, search_term))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'message': 'Scraping started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_scraper(task_id, keywords, search_term):
    try:
        # Create and run the scraper
        scraper = SingaporeJobScraper(keywords, output_dir=RESULTS_DIR)
        output_file = scraper.run(search_term=search_term, export_format='json')
        
        # Update task status
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['results_file'] = output_file
        tasks[task_id]['job_count'] = len(scraper.results)
        tasks[task_id]['end_time'] = datetime.now().isoformat()
        
    except Exception as e:
        # Update task with error
        tasks[task_id]['status'] = 'failed'
        tasks[task_id]['error'] = str(e)
        tasks[task_id]['end_time'] = datetime.now().isoformat()

@app.route('/task_status/<task_id>')
def task_status(task_id):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
        
    return jsonify(tasks[task_id])

@app.route('/results/<task_id>')
def get_results(task_id):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
        
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed yet'}), 400
        
    if not task['results_file'] or not os.path.exists(task['results_file']):
        return jsonify({'error': 'Results file not found'}), 404
        
    # Read results
    with open(task['results_file'], 'r') as f:
        results = json.load(f)
        
    return jsonify(results)

@app.route('/download/<task_id>')
def download_results(task_id):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
        
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed yet'}), 400
        
    if not task['results_file'] or not os.path.exists(task['results_file']):
        return jsonify({'error': 'Results file not found'}), 404
        
    # Get requested format
    format_type = request.args.get('format', 'csv')
    
    # Read the JSON results
    with open(task['results_file'], 'r') as f:
        results = json.load(f)
    
    # Create a dataframe
    df = pd.DataFrame(results)
    
    # Create a temporary file for download
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format_type == 'excel':
        temp_file = f"{RESULTS_DIR}/export_{task_id}_{timestamp}.xlsx"
        df.to_excel(temp_file, index=False)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
    elif format_type == 'json':
        temp_file = f"{RESULTS_DIR}/export_{task_id}_{timestamp}.json"
        df.to_json(temp_file, orient='records', indent=4)
        mimetype = 'application/json'
        
    else:  # default to CSV
        temp_file = f"{RESULTS_DIR}/export_{task_id}_{timestamp}.csv"
        df.to_csv(temp_file, index=False)
        mimetype = 'text/csv'
    
    return send_file(
        temp_file,
        mimetype=mimetype,
        as_attachment=True,
        download_name=os.path.basename(temp_file)
    )

@app.route('/tasks')
def list_tasks():
    return jsonify(list(tasks.values()))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)