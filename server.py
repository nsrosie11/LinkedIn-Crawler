from flask import Flask, request, send_from_directory, jsonify, Response
from sales_navigator_scraper import SalesNavigatorScraper
from uuid import uuid4
import threading
import queue
import json
import time
import os

app = Flask(__name__)
active_crawlers = {}
progress_queues = {}

# --- Helper: pastikan folder db dan file templates.json ada ---
def ensure_db():
    db_dir = 'db'
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    json_path = os.path.join(db_dir, 'templates.json')
    if not os.path.exists(json_path):
        with open(json_path, 'w') as f:
            json.dump({}, f)
    return json_path

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# ==============================
# CRAWLER ENDPOINTS
# ==============================

@app.route('/start-crawler', methods=['POST'])
def start_crawler():
    data = request.json
    queue_id = str(threading.get_ident())
    progress_queues[queue_id] = queue.Queue()
    
    def run_crawler():
        scraper = SalesNavigatorScraper(
            email=data['email'],
            password=data['password'],
            connect_note=data['connectNote'],
            progress_queue=progress_queues[queue_id],
            template_name=data['templateName']
        )
        active_crawlers[queue_id] = scraper
        scraper.direct_access_and_connect(data['searchUrl'])
        progress_queues[queue_id].put({
            'message': 'Crawler completed',
            'status': 'completed',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        })
        active_crawlers.pop(queue_id, None)
    
    thread = threading.Thread(target=run_crawler)
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Crawler started', 'queue_id': queue_id})

@app.route('/stop-crawler', methods=['POST'])
def stop_crawler():
    try:
        for queue_id, crawler in active_crawlers.items():
            crawler.stop()
            if queue_id in progress_queues:
                progress_queues[queue_id].put({
                    'message': 'Crawler stopped by user',
                    'status': 'stopped',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        active_crawlers.clear()
        return jsonify({'status': 'success', 'message': 'Crawler stopped'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error stopping crawler: {str(e)}'}), 500

@app.route('/stream/<queue_id>')
def stream_progress(queue_id):
    def generate():
        q = progress_queues.get(queue_id)
        if not q:
            return
            
        while True:
            try:
                progress = q.get(timeout=1)
                if progress is None:
                    break
                yield f"data: {json.dumps(progress)}\n\n"
            except queue.Empty:
                if queue_id not in active_crawlers:
                    break
                continue
            
        progress_queues.pop(queue_id, None)
    
    return Response(generate(), mimetype='text/event-stream')

# ==============================
# TEMPLATE DATA ENDPOINTS
# ==============================

@app.route('/get_template_data')
def get_template_data():
    template = request.args.get('template')
    if not template:
        return jsonify([]), 400

    ensure_db()
    data_files = [f for f in os.listdir('db') if f.endswith('.json') and template in f]
    all_data = []

    for file in data_files:
        try:
            date = "-".join(file.split('-')[:3])
            with open(os.path.join('db', file), 'r') as f:
                data = json.load(f)
                all_data.append({
                    'date': date,
                    'profiles': data.get('profiles', []),
                    'connected': len(data.get('connected', []))
                })
        except Exception:
            continue

    return jsonify(all_data)

@app.route('/get_template_history')
def get_template_history():
    template = request.args.get('template')
    if not template:
        return jsonify([]), 400
        
    ensure_db()
    history = []
    
    for filename in os.listdir('db'):
        if filename.endswith('.json') and template in filename:
            file_path = os.path.join('db', filename)
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    date = "-".join(filename.split('-', 3)[:3])
                    history.append({
                        'date': date,
                        'leads': data
                    })
            except Exception as e:
                print(f'Error reading {filename}: {str(e)}')
    
    return jsonify(history)

# ==============================
# TEMPLATE MANAGEMENT (CRUD)
# ==============================

@app.route('/api/templates', methods=['GET'])
def get_templates():
    json_path = ensure_db()
    with open(json_path, 'r') as f:
        return jsonify(json.load(f))

@app.route('/api/templates', methods=['POST'])
def create_template():
    template_data = request.json
    template_id = str(uuid4())

    json_path = ensure_db()
    with open(json_path, 'r') as f:
        templates = json.load(f)
    
    templates[template_id] = template_data
    
    with open(json_path, 'w') as f:
        json.dump(templates, f, indent=2)
    
    return jsonify({'id': template_id})

@app.route('/api/templates/<template_id>', methods=['PUT'])
def update_template(template_id):
    template_data = request.json
    json_path = ensure_db()

    with open(json_path, 'r') as f:
        templates = json.load(f)
    
    if template_id not in templates:
        return jsonify({'error': 'Template not found'}), 404
    
    templates[template_id] = template_data
    
    with open(json_path, 'w') as f:
        json.dump(templates, f, indent=2)
    
    return jsonify({'success': True})

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    json_path = ensure_db()

    with open(json_path, 'r') as f:
        templates = json.load(f)
    
    if template_id not in templates:
        return jsonify({'error': 'Template not found'}), 404
    
    del templates[template_id]
    
    with open(json_path, 'w') as f:
        json.dump(templates, f, indent=2)
    
    return jsonify({'success': True})

@app.route('/save-template', methods=['POST'])
def save_template():
    try:
        template_data = request.json
        # Here you would normally insert into Supabase
        # For now, just return success
        return jsonify({'message': 'Template saved successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==============================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
