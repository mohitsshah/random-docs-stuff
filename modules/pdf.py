import os
import shutil
import subprocess
from .database import Database


class PDFParser(object):
    def __init__(self, id, upload_dir, categories, file):
        d = upload_dir
        for c in categories[0:-1]:
            d = os.path.join(d, c)
            if not os.path.exists(d):
                os.mkdir(d)
        upload_path = os.path.join(d, id + '.pdf')
        file.save(upload_path)

        base_dir = './processed'
        if not os.path.exists(base_dir):
            os.mkdir(base_dir)
        d = base_dir
        for c in categories:
            d = os.path.join(d, c)
            if not os.path.exists(d):
                os.mkdir(d)
        self.dir_path = d
        path = os.path.join(d, id + '.pdf')
        shutil.copy(upload_path, path)
        self.filename = id

        database = Database()
        self.err = None
        try:
            database.insert_document(id, categories[0:-1], upload_path, self.dir_path)
        except Exception as e:
            self.err = str(e)

    def parse(self):
        if self.err is None:
            process = subprocess.Popen(
                ['python', './modules/pdf_parse.py', '-filename', self.filename, '-path', self.dir_path])
