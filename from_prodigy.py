"""

"""
from os.path import join
from collections import defaultdict
import re
from utils_peter import pdf_dir, save_json, load_jsonl


def load_pages():
    if True:
        root = 'blank.model'
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


RE_URL = re.compile(r'^http://localhost:8000/(.+?)#page=(\d+)(?:&view=Fit)?$')


def collect_pages(ppt_list):
    path_pages = defaultdict(set)
    all_answers = defaultdict(int)
    for path, page, text, answer in ppt_list:
        if answer == 'accept':
            path_pages[path].add(page)
        all_answers[answer] += 1
    print('answers:', sorted(all_answers.items()))
    # assert False
    return {path: sorted(pages) for path, pages in path_pages.items()}


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
    assert 'answer' in json_dict, json_dict
    answer = json_dict['answer']
    m = RE_URL.search(url)
    name = m.group(1)
    page = int(m.group(2))
    path = join(pdf_dir, name)

    return path, page, text, answer


if __name__ == '__main__':
    load_pages()
