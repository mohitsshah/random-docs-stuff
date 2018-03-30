import sqlite3
import os
import shutil


class Database(object):
    def __init__(self):
        db_dir = 'database'
        if not os.path.exists(db_dir):
            os.mkdir(db_dir)
        self.doc_db, self.doc_cols = self.maybe_create_docs_db(db_dir)
        self.model_db, self.model_cols = self.maybe_create_models_db(db_dir)

    def maybe_create_docs_db(self, db_dir):
        doc_db = os.path.join(db_dir, 'documents.sqlite')
        if not os.path.exists(doc_db):
            conn = sqlite3.connect(doc_db)
            c = conn.cursor()
            c.execute(
                'CREATE TABLE documents (id TEXT UNIQUE, categories TEXT, upload_path TEXT, processed_path TEXT, status TEXT, timestamp TEXT)')
            conn.commit()
            conn.close()
        doc_cols = ["id", "categories", "upload_path", "processed_path", "status", "timestamp"]
        return doc_db, doc_cols

    def maybe_create_models_db(self, db_dir):
        doc_db = os.path.join(db_dir, 'models.sqlite')
        if not os.path.exists(doc_db):
            conn = sqlite3.connect(doc_db)
            c = conn.cursor()
            c.execute(
                'CREATE TABLE documents (name TEXT UNIQUE, path TEXT, status TEXT, timestamp TEXT)')
            conn.commit()
            conn.close()
        doc_cols = ["name", "path", "status", "timestamp"]
        return doc_db, doc_cols

    def document_exists(self, id):
        conn = sqlite3.connect(self.doc_db)
        c = conn.cursor()
        t = (id,)
        c.execute('SELECT * FROM documents WHERE id=?', t)
        data = c.fetchone()
        conn.close()
        return data

    def fetch_document(self, id):
        conn = sqlite3.connect(self.doc_db)
        c = conn.cursor()
        t = (id,)
        c.execute('SELECT * FROM documents WHERE id=?', t)
        data = c.fetchone()
        conn.close()
        if data is None:
            return data, None
        else:
            obj = {}
            for i, col in enumerate(self.doc_cols):
                obj[col] = data[i]
            if obj['status'] != 'COMPLETE':
                return None, obj['status']
            else:
                return obj, obj['status']

    def insert_document(self, id, categories, upload_path, processed_path):
        conn = sqlite3.connect(self.doc_db)
        c = conn.cursor()
        c.execute(
            "INSERT INTO documents (id, categories, upload_path, processed_path, status, timestamp) VALUES (?, ?, ?, ?, 'INCOMPLETE', DATETIME('now'))",
            (id, '/'.join(categories), upload_path, processed_path))
        conn.commit()
        conn.close()

    def update_status(self, id, status):
        conn = sqlite3.connect(self.doc_db)
        conn.execute("UPDATE documents SET status=? WHERE id=?", (status, id))
        conn.commit()
        conn.close()

    def update_category(self, id, categories, obj, upload_folder):
        print(id)
        new_path = os.path.join(upload_folder, categories)
        os.makedirs(new_path, exist_ok=True)
        new_file_path = os.path.join(new_path, id + '.pdf')
        old_path = obj['upload_path']
        shutil.move(old_path, new_file_path)
        processed_path = obj['processed_path']
        new_processed_path = os.path.join('./processed', categories, id)
        shutil.move(processed_path, new_processed_path)
        conn = sqlite3.connect(self.doc_db)
        conn.execute("UPDATE documents SET categories=?,upload_path=?,processed_path=? WHERE id=?",
                     (categories, new_file_path, new_processed_path, id))
        conn.commit()
        conn.close()

    def insert_model(self, name, path):
        conn = sqlite3.connect(self.model_db)
        c = conn.cursor()
        c.execute(
            "INSERT INTO documents (name, path, status, timestamp) VALUES (?, ?, 'NONE', DATETIME('now'))",
            (name, path))
        conn.commit()
        conn.close()

    def fetch_model(self, name):
        conn = sqlite3.connect(self.model_db)
        c = conn.cursor()
        t = (name,)
        c.execute('SELECT * FROM documents WHERE name=?', t)
        data = c.fetchone()
        conn.close()
        if data is None:
            return data
        else:
            obj = {}
            for i, col in enumerate(self.model_cols):
                obj[col] = data[i]
            return obj

    def update_training_status(self, name, status):
        conn = sqlite3.connect(self.model_db)
        conn.execute("UPDATE documents SET status=? WHERE name=?", (status, name))
        conn.commit()
        conn.close()
