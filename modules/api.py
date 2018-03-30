import requests
import json
import os


class API(object):
    def __init__(self, host, port):
        self.host = host
        self.port = str(port)
        self.base_url = 'http://' + host + ':' + port + '/'

    def upload(self, file_path, id, category=None):
        url = self.base_url + 'upload'
        print ("Making request to: ", url)
        payload = {"id": id}
        if category:
            payload["category"] = category
        files = {"file": (json.dumps(payload), open(file_path, 'rb'), 'application/octet-stream')}
        req = requests.post(url, files=files)
        return req.status_code, json.loads(req.content)

    def fetch(self, id):
        url = self.base_url + 'fetch'
        print ("Making request to: ", url)
        req = requests.get(url, params={"id": id})
        return req.status_code, json.loads(req.content)

    def tag(self, id, categories):
        url = self.base_url + 'tag'
        print("Making request to: ", url)
        payload = {"id": id, "categories": categories}
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        return req.status_code, json.loads(req.content)

    def create_model(self, name, params):
        url = self.base_url + 'models'
        print("Making request to: ", url)
        payload = {"name": name, "params": params}
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        return req.status_code, json.loads(req.content)

    def train_model(self, name):
        url = self.base_url + 'train'
        print("Making request to: ", url)
        payload = {"name": name}
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        return req.status_code, json.loads(req.content)

    def train_status(self, name):
        url = self.base_url + 'train_status'
        print("Making request to: ", url)
        payload = {"name": name}
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        return req.status_code, json.loads(req.content)

    def get_prediction(self, id, name):
        url = self.base_url + 'predict'
        print("Making request to: ", url)
        payload = {"name": name, "id": id}
        req = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload))
        return req.status_code, json.loads(req.content)
