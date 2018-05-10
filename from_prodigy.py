"""

"""
from os.path import join
from collections import defaultdict
import re
from utils_peter import pdf_dir, save_json, load_jsonl


def load_pages():
    if True:
        root = 'model1'
        prodigy_list = []
        for name in ['evaluation.jsonl', 'training.jsonl']:
            path = join(root, name)
            pl = load_jsonl(path)
            print('%s: %d' % (path, len(pl)))
            prodigy_list.extend(pl)
    else:
        prodigy_list = load_jsonl('all.pages.jsonl')
    ppt_list = [from_prodigy(d) for d in prodigy_list]
    path_pages = collect_pages(ppt_list)
    save_json('path-pages.json', path_pages)
    pages = sum(len(p) for p in path_pages.values())
    print('saved to path-pages.json : %d paths %d pages' % (
        len(path_pages), pages))


RE_URL = re.compile(r'^http://localhost:8000/(.+?)#page=(\d+)$')


def collect_pages(ppt_list):
    path_pages = defaultdict(list)
    for path, page, text in ppt_list:
        path_pages[path].append(page)
    return path_pages


def from_prodigy(json_dict):
    """
        {"text":"Uber\u2019s Lesson: Silicon Valley\u2019s Start-Up Machine Needs Fixing",
        "meta":{"source":"The New York Times"},
                "url":"https://github.com/rdbc-io/rdbc/issues/86
               },
        }
    """
    text = json_dict['text']
    meta = json_dict['meta']
    url = meta['url']
    m = RE_URL.search(url)
    name = m.group(1)
    page = int(m.group(2))
    path = join(pdf_dir, name)

    return path, page, text


if __name__ == '__main__':
    load_pages()
