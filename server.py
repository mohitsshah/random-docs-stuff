from flask import Flask, redirect, url_for, request, jsonify
import argparse
import os
import json
from modules.pdf import PDFParser
from modules.database import Database
from modules.configs import ModelConfig

app = Flask(__name__)
UPLOAD_FOLDER = './uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.mkdir(UPLOAD_FOLDER)

ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

database = Database()
configs = ModelConfig()


def get_args():
    parser = argparse.ArgumentParser(description='Document Processing API')
    parser.add_argument('-p', '--port', type=str, default="12345",
                        help='Port number', nargs='+')
    args = parser.parse_args()
    port = args.port[0]
    return port


port_code = get_args()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_document():
    try:
        if 'file' not in request.files:
            print('No file part')
        file = request.files['file']
        metadata = json.loads(file.filename)
        id = metadata["id"]
        exists = database.document_exists(id)
        if not exists:
            if 'category' in metadata:
                categories = metadata['category'].split('/')
            else:
                categories = ['unclassified']
            categories.append(metadata["id"])
            parser = PDFParser(metadata["id"], app.config['UPLOAD_FOLDER'], categories, file)
            parser.parse()
            message = "Submitted job for Document ID %s." % id
            response = jsonify({"message": message})
        else:
            message = "Document ID %s already exists." % id
            response = jsonify({"message": message})
            response.status_code = 500
    except Exception as e:
        message = str(e)
        response = jsonify({"message": message})
        response.status_code = 404
    return response


@app.route('/fetch', methods=['GET'])
def fetch_document():
    id = request.args.get('id')
    if id is not None:
        content, status = database.fetch_document(id)
        if content is None:
            message = 'Document ID %s is being processed.' % id
            response = jsonify({"message": message})
            response.status_code = 500
            return response
        else:
            message = content
            json_path = os.path.join(message['processed_path'], message['id'] + '.json')
            with open(json_path, 'r') as fi:
                message['content'] = json.loads(fi.read())
            return jsonify(message)
    else:
        response = jsonify({"message": "id not provided"})
        response.status_code = 404
        return response


@app.route('/tag', methods=['POST'])
def tag_document():
    data = request.get_json(force=True)
    if "id" in data and "categories" in data:
        categories = data["categories"]
        id = data["id"]
        if id is not None:
            content, status = database.fetch_document(id)
            if content is None:
                message = 'Document ID %s does not exist.' % id
                response = jsonify({"message": message})
                response.status_code = 500
                return response
            else:
                database.update_category(id, categories, content, app.config['UPLOAD_FOLDER'])
                message = {"message": "OK"}
                return jsonify(message)
    else:
        response = jsonify({"message": "id/categories not provided"})
        response.status_code = 404
        return response


@app.route('/models', methods=['POST'])
def create_model_config():
    data = request.get_json(force=True)
    if 'name' not in data:
        response = jsonify({"message": "Name is required."})
        response.status_code = 500
        return response
    name = data["name"]

    if 'params' not in data:
        response = jsonify({"message": "Model parameters are required."})
        response.status_code = 500
        return response
    params = data["params"]
    status, message = configs.create(name, params)
    if status:
        return jsonify({"message": "Created config: %s" % name})
    else:
        response = jsonify({"message": message})
        response.status_code = 500
        return response


@app.route('/train', methods=['POST'])
def train_model():
    data = request.get_json(force=True)
    if 'name' not in data:
        response = jsonify({"message": "Name is required."})
        response.status_code = 500
        return response
    name = data["name"]
    status, message = configs.train(name)
    if status:
        return jsonify({"message": "Submitted model %s for training." % name})
    else:
        response = jsonify({"message": message})
        response.status_code = 500
        return response


@app.route('/train_status', methods=['POST'])
def train_status():
    data = request.get_json(force=True)
    if 'name' not in data:
        response = jsonify({"message": "Name is required."})
        response.status_code = 500
        return response
    name = data["name"]
    status, message = configs.check_status(name)
    if status:
        return jsonify({"message": message})
    else:
        response = jsonify({"message": message})
        response.status_code = 500
        return response


@app.route('/predict', methods=['POST'])
def get_prediction():
    data = request.get_json(force=True)
    if 'name' not in data:
        response = jsonify({"message": "Name is required."})
        response.status_code = 500
        return response
    name = data["name"]
    if 'id' not in data:
        response = jsonify({"message": "Document ID is required."})
        response.status_code = 500
        return response
    id = data["id"]
    status, message = configs.predict(id, name)
    if status:
        return jsonify({"message": message})
    else:
        response = jsonify({"message": message})
        response.status_code = 500
        return response

if __name__ == '__main__':
    try:
        app.run(debug=True, port=int(port_code))
    except Exception:
        app.run(debug=True, port=12345)
