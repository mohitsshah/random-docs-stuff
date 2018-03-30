import os
import numpy as np
import pickle
import modules.utils as utils


class Classifier(object):
    @staticmethod
    def load_model(name):
        model_file = os.path.join('./models', name, "model.pkl")
        if not os.path.exists(model_file):
            return None
        with open(model_file, 'rb') as fi:
            model = pickle.load(fi)
            return model

    def run(self, text, name):
        try:
            model = self.load_model(name)
            if model is None:
                return False, "Error loading model %s" % name
            input_rep = model["inputs"]
            text = utils.preprocess_text(text)
            text_feats = input_rep.transform([text])
            clf = model["classifier"]
            probs = clf.predict_proba(text_feats)
            tags = model["tags"]
            probs = probs[0]
            indices = np.argsort(probs)[::-1]
            scores = []
            for i in indices:
                scores.append([tags[i], np.round(probs[i], 2)])
            return True, scores
        except Exception as e:
            print (str(e))
            return None, str(e)