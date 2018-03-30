class Page(object):
    def __init__(self, page):
        self.page = page

    def get_size(self):
        return {"width": self.page["width"], "height": self.page["height"]}

    def get_headers(self):
        lines = self.page["lines"]
        headers = [(lines[i]['text'], lines[i]['header']) for i, _ in enumerate(lines) if 'header' in lines[i]]
        return headers

    def get_footers(self):
        lines = self.page["lines"]
        footers = [(lines[i]['text'], lines[i]['footer']) for i, _ in enumerate(lines) if 'footer' in lines[i]]
        return footers

    def get(self):
        return self.page["lines"]

    def get_lines(self):
        return '\n'.join([l["text"] for l in self.page["lines"]])


class Document(object):
    def __init__(self, doc):
        self.doc = doc
        self.pages = [Page(p) for p in self.doc["content"]["pages"]]

    def num_pages(self):
        return self.doc["content"]["numPages"]

    def get_page(self, num):
        page = None
        try:
            return self.pages[num]
        except Exception as e:
            print(str(e))
        return page

    def get_text(self):
        text = '\n'.join([p.get_lines() for p in self.pages])
        return text

    def get_tags(self):
        return self.doc["categories"]

    def set_tags(self, tag):
        from .api import API
        service = API('localhost', '12345')
        status, data = service.tag(self.doc["id"], tag)
        if status == 200:
            return True
        else:
            print("Tagging error: %s" % data["message"])
            return False
