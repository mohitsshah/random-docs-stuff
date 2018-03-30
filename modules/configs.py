import os
import json
import subprocess
from .database import Database

configs_dir = './models'


class ModelConfig(object):
    def create(self, name, params):
        if "dataset" not in params:
            return False, "Dataset not specified."
        if "directory" not in params["dataset"]:
            params["dataset"]["directory"] = "."
        if "tags" not in params["dataset"]:
            params["dataset"]["tags"] = None
        if "split" not in params["dataset"]:
            params["dataset"]["split"] = 0.2
        if "input" not in params:
            return False, "Input representation not specified."
        if "method" not in params["input"]:
            params["input"]["method"] = "tfidf"
        if "vocab_size" not in params["input"]:
            params["input"]["vocab_size"] = 1000
        if "min_n" not in params["input"]:
            params["input"]["min_n"] = 1
        if "max_n" not in params["input"]:
            params["input"]["max_n"] = 1
        if "classifier" not in params:
            return False, "Classifier not specified."
        if "method" not in params["classifier"]:
            params["classifier"]["method"] = "mlp"
        model_dir = os.path.join(configs_dir, name)
        os.makedirs(model_dir, exist_ok=True)
        config_file = os.path.join(model_dir, 'configs.json')
        with open(config_file, 'w') as fi:
            fi.write(json.dumps(params))
        db = Database()
        try:
            db.insert_model(name, model_dir)
        except Exception as e:
            return False, str(e)
        return True, True

    def train(self, name):
        db = Database()
        obj = db.fetch_model(name)
        status = obj["status"]
        if status != "INCOMPLETE":
            db = Database()
            db.update_training_status(name, "INCOMPLETE")
            process = subprocess.Popen(['python', './modules/trainer.py', '-name', obj["name"]])
            return True, True
        else:
            return False, "Training is already in progress."

    def check_status(self, name):
        db = Database()
        obj = db.fetch_model(name)
        status = obj["status"]
        if status == "NONE":
            return False, "Model %s not trained." % name
        elif status == "INCOMPLETE":
            return False, "Training %s is already in progress." % name
        elif status == "COMPLETE":
            return True, "Training %s complete." % name
        else:
            return False, "Error: %s" % status
