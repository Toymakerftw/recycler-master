# app.py
from flask import Flask, render_template, jsonify, request
import os
import mimetypes

app = Flask(__name__)

def get_file_type(path):
    mime_type, _ = mimetypes.guess_type(path)
    if mime_type:
        if mime_type.startswith('text/'):
            return 'text'
        elif mime_type.startswith('image/'):
            return 'image'
    return 'other'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/browse')
def browse():
    path = request.args.get('path', os.path.expanduser('~'))
    try:
        items = []
        with os.scandir(path) as entries:
            for entry in entries:
                try:
                    item = {
                        'name': entry.name,
                        'path': os.path.join(path, entry.name),
                        'is_dir': entry.is_dir(),
                        'size': os.path.getsize(entry.path) if not entry.is_dir() else 0,
                        'type': 'directory' if entry.is_dir() else get_file_type(entry.name),
                        'extension': os.path.splitext(entry.name)[1][1:].lower() if not entry.is_dir() else ''
                    }
                    items.append(item)
                except (PermissionError, FileNotFoundError):
                    continue
        
        return jsonify({
            'current_path': path,
            'parent_path': os.path.dirname(path),
            'items': sorted(items, key=lambda x: (not x['is_dir'], x['name'].lower()))
        })
    except PermissionError:
        return jsonify({'error': 'Permission denied'}), 403
    except FileNotFoundError:
        return jsonify({'error': 'Path not found'}), 404

@app.route('/file')
def get_file():
    path = request.args.get('path')
    try:
        if os.path.isfile(path):
            with open(path, 'r') as f:
                content = f.read()
            return jsonify({
                'content': content,
                'extension': os.path.splitext(path)[1][1:].lower()
            })
    except UnicodeDecodeError:
        return jsonify({'error': 'Not a text file'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
