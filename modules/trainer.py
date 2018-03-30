import os
import json
import re
import numpy as np
import argparse
import pickle
from database import Database
from document import Document
from sklearn.cross_validation import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, confusion_matrix
import utils


class Trainer(object):
    def __init__(self, name):
        self.name = name

    @staticmethod
    def get_configs(name):
        path = os.path.join('./models', name, "configs.json")
        with open(path, 'r') as fi:
            return json.loads(fi.read())

    @staticmethod
    def make_dataset(params):
        strings = re.compile('[^a-zA-Z]')
        data_dir = os.path.join('./processed', params["directory"])
        tags = os.listdir(data_dir)
        if params["tags"] is not None:
            tags = params["tags"].split(";")
        db = Database()
        texts = []
        labels = []
        for i, tag in enumerate(tags):
            class_dir = os.path.join(data_dir, tag)
            ids = os.listdir(class_dir)
            for id in ids:
                data, status = db.fetch_document(id)
                if data:
                    json_path = os.path.join(data['processed_path'], data['id'] + '.json')
                    with open(json_path, 'r') as fi:
                        data['content'] = json.loads(fi.read())
                    doc = Document(data)
                    text = doc.get_text()
                    text = utils.preprocess_text(text)
                    texts.append(text)
                    labels.append(i)

        train_x, test_x, train_y, test_y = train_test_split(texts, labels, test_size=params["split"])
        return train_x, test_x, train_y, test_y, tags

    @staticmethod
    def make_input(params):
        v = None
        if params["method"] == "tfidf":
            v = TfidfVectorizer(ngram_range=(params["min_n"], params["max_n"]), max_features=params["vocab_size"],
                                stop_words='english')
        return v

    @staticmethod
    def make_classifier(params):
        v = None
        method = params["method"]
        if method == "naive_bayes":
            v = MultinomialNB()
        elif method == "knn":
            v = KNeighborsClassifier()
        elif method == "svm":
            v = SVC(kernel="linear", probability=True)
        elif method == "decision_trees":
            v = DecisionTreeClassifier()
        elif method == "random_forest":
            v = RandomForestClassifier()
        elif method == "mlp":
            v = MLPClassifier()
        elif method == "adaboost":
            v = AdaBoostClassifier(base_estimator=SVC(kernel="linear", probability=True))
        return v

    @staticmethod
    def make_pipeline(inputs, classifier):
        p = Pipeline([("inputs", inputs), ("clf", classifier)])
        return p

    @staticmethod
    def get_confusion_matrix(true, pred, tags):
        cm = np.zeros((len(tags), len(tags)))
        for t, p in zip(true, pred):
            cm[t, p] += 1
        return cm

    def write_confusion_matrix(self, true, pred, tags, label='test'):
        confusion = self.get_confusion_matrix(true, pred, tags)
        with open(os.path.join('./models', self.name, label + '_confusion.txt'), 'w') as fi:
            headers = ['']
            headers.extend(tags)
            fi.write('\t'.join(headers))
            fi.write('\n')
            for i in range(len(confusion)):
                tmp = [tags[i]]
                vals = [str(v) for v in confusion[i, :]]
                tmp.extend(vals)
                fi.write('\t'.join(tmp))
                fi.write('\n')

    def train(self):
        try:
            configs = self.get_configs(self.name)
            train_x, test_x, train_y, test_y, tags = self.make_dataset(configs["dataset"])
            input_rep = self.make_input(configs["input"])
            clf = self.make_classifier(configs["classifier"])
            if input_rep and clf:
                input_rep.fit(train_x)
                train_feats = input_rep.transform(train_x)
                test_feats = input_rep.transform(test_x)
                clf.fit(train_feats, train_y)
                train_preds = clf.predict(train_feats)
                test_preds = clf.predict(test_feats)
                train_report = classification_report(train_y, train_preds, target_names=tags)
                test_report = classification_report(test_y, test_preds, target_names=tags)
                self.write_confusion_matrix(train_y, train_preds, tags, label='train')
                self.write_confusion_matrix(test_y, test_preds, tags, label='test')
                with open(os.path.join('./models', self.name, 'train_report.txt'), 'w') as fi:
                    fi.write(train_report)
                with open(os.path.join('./models', self.name, 'test_report.txt'), 'w') as fi:
                    fi.write(test_report)
                model = {
                    "inputs": input_rep,
                    "classifier": clf,
                    "tags": tags
                }
                with open(os.path.join('./models', self.name, 'model.pkl'), 'wb') as fi:
                    pickle.dump(model, fi)
                db = Database()
                db.update_training_status(self.name, 'COMPLETE')

        except Exception as e:
            print(str(e))
            db = Database()
            db.update_training_status(self.name, str(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser("Document Classification Trainer")
    parser.add_argument("-name", type=str, required=True, help="Model Name")
    flags = parser.parse_args()
    T = Trainer(flags.name)
    T.train()
