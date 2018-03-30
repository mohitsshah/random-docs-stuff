import xml.etree.ElementTree
import os
import json
import argparse
import numpy as np
from fuzzywuzzy import fuzz
import re
from lxml import html
from database import Database


def parse(filename, dir_path):
    def get_attribs(items):
        obj = {}
        for item in items:
            obj[item[0]] = item[1]
        return obj

    def get_text_from_textbox(root, id):
        selector = "./textbox[@id=" + "'" + id + "']"
        e = root.find(selector)
        box = []
        for child in e:
            if child.tag == 'textline':
                line = []
                for c in child:
                    if c.tag == 'text':
                        line.append(c.text)
                line = ''.join(line)
                box.append(line)
        box = ''.join(box)
        return box

    def convert_page(filename, number):
        infile = (filename + '.pdf[%s]') % str(int(number) - 1)
        outfile = (filename + '-%s' + '.png') % str(int(number) - 1)
        if os.path.exists(outfile):
            return outfile
        cmd = 'convert -density 300 -units PixelsPerInch ' + infile + ' ' + outfile
        os.system(cmd)
        return outfile

    def extract_region(filename, image_file, id, attribs, max_y):
        bbox = attribs['bbox']
        bbox = bbox.split(',')
        ymax = int(float(300 * max_y) / 72)
        bbox = [int(300 * float(b) / 72) for b in bbox]
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        crop_params = str(width) + 'x' + str(height) + '+' + str(bbox[0]) + '+' + str(ymax - bbox[3])
        outfile = image_file[0:-4] + '-'
        outfile += crop_params + '.png'
        if os.path.exists(outfile):
            return outfile
        cmd = 'convert -crop ' + crop_params + ' ' + image_file + ' ' + outfile
        os.system(cmd)
        return outfile

    def perform_ocr(infile):
        outfile = infile[0:-4] + '.hocr'
        if os.path.exists(outfile):
            return outfile
        cmd = 'tesseract ' + infile + ' ' + infile[0:-4] + ' hocr'
        os.system(cmd)
        return outfile

    def parse_hocr(infile):
        outfile = infile[0:-5] + '.txt'
        if os.path.exists(outfile):
            return outfile
        cmd = 'hocr-lines ' + infile + ' > ' + outfile
        os.system(cmd)
        return outfile

    def parse_hocr_lines(infile, width, height, attribs):
        lines = []
        bboxs = []
        y_coords = []
        bbox = attribs['bbox']
        bbox = bbox.split(',')
        ymax = int(float(300 * height) / 72)
        bbox = [int(300 * float(b) / 72) for b in bbox]
        w = 72 * float(bbox[2] - bbox[0]) / 300.
        h = 72 * float(bbox[3] - bbox[1]) / 300.
        x = 72 * float(bbox[0]) / 300.
        y = 72 * float(ymax - bbox[3]) / 300.
        doc = html.parse(infile)
        for line in doc.xpath("//*[@class='ocr_line']"):
            bbox = line.attrib['title'].split(';')[0].split(' ')[1:]
            others = line.attrib['title'].split(';')[1:]
            angle = 0.
            for o in others:
                if 'textangle' in o:
                    tmp = o.strip().split(' ')[1]
                    angle = float(tmp)
                    break
            bbox = [72 * float(x) / 300 for x in bbox]
            bbox[0] = (bbox[0] + x) / width
            bbox[1] = (bbox[1] + y) / height
            bbox[2] = (bbox[2] + x) / width
            bbox[3] = (bbox[3] + y) / height
            tmp = float(bbox[3])
            bbox[3] = float(bbox[1])
            bbox[1] = tmp
            tmp0 = float(bbox[0])
            tmp1 = float(bbox[1])
            tmp2 = float(bbox[2])
            tmp3 = float(bbox[3])
            if angle == 90:
                bbox[0] = tmp3
                bbox[1] = tmp2
                bbox[2] = tmp1
                bbox[3] = tmp0
            elif angle == 180:
                bbox[0] = tmp2
                bbox[1] = tmp3
                bbox[2] = tmp0
                bbox[3] = tmp1

            text = re.sub(r'\s+', '\x20', line.text_content()).strip()
            if len(text) > 0:
                bboxs.append(bbox)
                y_coords.append(bbox[3])
                lines.append(text)
        return bboxs, lines, y_coords

    def parse_text_lines(root, width, height):
        line_selector = "./page[@id=" + "'" + id + "']/textbox/textline"
        l_e = root.findall(line_selector)
        lines = []
        bboxs = []
        y_coords = []
        for child in l_e:
            line = []
            fonts = []
            for c in child:
                if c.tag == 'text':
                    line.append(c.text)
                    if c.attrib:
                        if 'size' in c.attrib:
                            fonts.append(c.attrib['size'])

            bbox = child.attrib['bbox']
            bbox = bbox.split(',')
            bbox = [float(x) for x in bbox]
            bbox[1] = height - bbox[1]
            bbox[3] = height - bbox[3]
            bbox[0] /= width
            bbox[1] /= height
            bbox[2] /= width
            bbox[3] /= height
            line = ''.join(line).rstrip().lstrip()
            if len(line) > 0:
                bboxs.append(bbox)
                y_coords.append(bbox[3])
                lines.append(line)
        return bboxs, lines, y_coords

    def get_page_children(filename, root, id):
        selector = "./page[@id=" + "'" + id + "']"
        e = root.find(selector)
        bbox = e.attrib['bbox']
        bbox = bbox.split(',')
        bbox = [float(x) for x in bbox]
        width = bbox[2]
        height = bbox[3]
        page_attribs = get_attribs(e.items())
        bbox = page_attribs['bbox']
        bbox = bbox.split(',')
        bbox = [int(float(b)) for b in bbox]
        max_y = bbox[-1]
        boxes = []
        lines = []
        y_coords = []
        t_boxs, t_lines, t_y = parse_text_lines(root, width, height)
        boxes.extend(t_boxs)
        lines.extend(t_lines)
        y_coords.extend(t_y)
        for child in e:
            tag = child.tag
            if tag == 'figure':
                if id not in pages_converted:
                    pages_converted[id] = convert_page(filename, id)
                image_file = pages_converted[id]
                attribs = get_attribs(child.items())
                cropped_file = extract_region(filename, image_file, id, attribs, max_y)
                hocr_file = perform_ocr(cropped_file)
                h_boxs, h_lines, h_y = parse_hocr_lines(hocr_file, width, height, attribs)
                boxes.extend(h_boxs)
                lines.extend(h_lines)
                y_coords.extend(h_y)

        if len(lines) == 0:
            if id not in pages_converted:
                pages_converted[id] = convert_page(filename, id)
            image_file = pages_converted[id]
            attribs = get_attribs(e.items())
            cropped_file = extract_region(filename, image_file, id, attribs, max_y)
            hocr_file = perform_ocr(cropped_file)
            h_boxs, h_lines, h_y = parse_hocr_lines(hocr_file, width, height, attribs)
            boxes.extend(h_boxs)
            lines.extend(h_lines)
            y_coords.extend(h_y)

        idx = np.argsort(y_coords)
        new_lines = []
        new_bboxs = []
        for dx in list(idx):
            new_lines.append(lines[dx])
            new_bboxs.append(boxes[dx])
        obj = {'bbox': new_bboxs, 'text': new_lines, 'width': width, 'height': height}
        return obj

    def get_headers_footers(pages):
        window_size = 5
        top_n = 5
        num_pages = len(pages)
        h_scores = np.zeros((num_pages, top_n))
        f_scores = np.zeros((num_pages, top_n))
        h_weights = [1.0, 1.0, 0.5, 0.5, 0.5]
        f_weights = [1.0, 1.0, 0.5, 0.5, 0.5]
        num = np.zeros(num_pages)
        for i in range(num_pages):
            box = pages[str(i + 1)]['bbox']
            lns = pages[str(i + 1)]['text']
            for j in range(0, window_size):
                if (i - j - 1) >= 0:
                    cbox = pages[str(i - j)]['bbox']
                    clns = pages[str(i - j)]['text']
                    for n in range(top_n):
                        try:
                            b1 = np.array(box[n])
                            b2 = np.array(cbox[n])
                            d = np.sum((b1 - b2) * (b1 - b2))
                            l1 = lns[n]
                            l1 = re.sub(r'\d', '@', l1)
                            l2 = clns[n]
                            l2 = re.sub(r'\d', '@', l2)
                            s = float(fuzz.ratio(l1, l2)) / 100
                            s *= np.exp(-d)
                            s *= h_weights[n]
                            h_scores[i, n] += s
                        except Exception as e:
                            pass
                    for n in range(top_n):
                        try:
                            b1 = np.array(box[len(box) - n - 1])
                            b2 = np.array(cbox[len(cbox) - n - 1])
                            d = np.sum((b1 - b2) * (b1 - b2))
                            l1 = lns[len(lns) - n - 1]
                            l1 = re.sub(r'\d', '@', l1)
                            l2 = clns[len(clns) - n - 1]
                            l2 = re.sub(r'\d', '@', l2)
                            s = float(fuzz.ratio(l1, l2)) / 100
                            s *= np.exp(-d)
                            s *= f_weights[n]
                            f_scores[i, n] += s
                        except Exception as e:
                            pass
                    num[i] += 1
                if (i + j + 1) < num_pages:
                    cbox = pages[str(i + j + 2)]['bbox']
                    clns = pages[str(i + j + 2)]['text']
                    for n in range(top_n):
                        try:
                            b1 = np.array(box[n])
                            b2 = np.array(cbox[n])
                            d = np.sum((b1 - b2) * (b1 - b2))
                            l1 = lns[n]
                            l1 = re.sub(r'\d', '@', l1)
                            l2 = clns[n]
                            l2 = re.sub(r'\d', '@', l2)
                            s = float(fuzz.ratio(l1, l2)) / 100
                            s *= np.exp(-d)
                            s *= h_weights[n]
                            h_scores[i, n] += s
                        except Exception as e:
                            pass
                    for n in range(top_n):
                        try:
                            b1 = np.array(box[len(box) - n - 1])
                            b2 = np.array(cbox[len(cbox) - n - 1])
                            d = np.sum((b1 - b2) * (b1 - b2))
                            l1 = lns[len(lns) - n - 1]
                            l1 = re.sub(r'\d', '@', l1)
                            l2 = clns[len(clns) - n - 1]
                            l2 = re.sub(r'\d', '@', l2)
                            s = float(fuzz.ratio(l1, l2)) / 100
                            s *= np.exp(-d)
                            s *= f_weights[n]
                            f_scores[i, n] += s
                        except Exception as e:
                            pass
                    num[i] += 1

        threshold = 0.5
        h_scores = h_scores / num.reshape(-1, 1)
        headers = {}
        for i in range(num_pages):
            headers[str(i + 1)] = []
            s = h_scores[i, :]
            for n, j in enumerate(s):
                if j > threshold:
                    headers[str(i + 1)].append((n, j))

        f_scores = f_scores / num.reshape(-1, 1)
        footers = {}
        for i in range(num_pages):
            footers[str(i + 1)] = []
            s = f_scores[i, :]
            for n, j in enumerate(s):
                if j > threshold:
                    L = len(pages[str(i + 1)]['text'])
                    footers[str(i + 1)].append((L - n - 1, j))
        return headers, footers

    def make_document(pages, headers, footers):
        document = {'numPages': len(pages), 'pages': []}
        for i in range(len(pages)):
            content = pages[str(i + 1)]
            header = headers[str(i + 1)]
            footer = footers[str(i + 1)]
            boxes = content['bbox']
            lines = content['text']
            page = {"width": content["width"], "height": content["height"], "lines": []}
            for box, line in zip(boxes, lines):
                coords = [{"x": box[0], "y": box[3]}, {"x": box[2], "y": box[3]}, {"x": box[0], "y": box[1]},
                          {"x": box[2], "y": box[1]}]
                page["lines"].append({"box": coords, "text": line})
            for h in header:
                index = h[0]
                score = h[1]
                page["lines"][index]["header"] = score
            for f in footer:
                index = f[0]
                score = f[1]
                page["lines"][index]["footer"] = score
            document["pages"].append(page)
        return document

    def convert_to_xml(filename):
        infile = filename + '.pdf'
        outfile = filename + '.xml'
        if os.path.exists(outfile):
            return
        cmd = 'python ./modules/pdf2txt.py -o ' + outfile + ' ' + infile
        os.system(cmd)

    pages_converted = {}
    if filename.endswith('.pdf'):
        filename = filename[0:-4]
    doc_id = str(filename)
    filename = os.path.join(dir_path, filename)
    convert_to_xml(filename)
    tree = xml.etree.ElementTree.parse(filename + '.xml')
    root = tree.getroot()
    pages = {}
    for child in root:
        tag = child.tag
        if tag == 'page':
            obj = get_attribs(child.items())
            id = obj['id']
            content = get_page_children(filename, root, id)
            pages[id] = content
    print('Number of Pages: ', len(pages))
    headers, footers = get_headers_footers(pages)
    document = make_document(pages, headers, footers)
    with open(filename + '.json', 'w') as fi:
        fi.write(json.dumps(document))
    database = Database()
    database.update_status(doc_id, 'COMPLETE')


if __name__ == '__main__':
    p = argparse.ArgumentParser('PDF Parser Script')
    p.add_argument('-filename', type=str, required=True)
    p.add_argument('-path', type=str, required=True)
    flags = p.parse_args()
    parse(flags.filename, flags.path)
