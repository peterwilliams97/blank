"""
   {"text": "Uber\u2019s Lesson: Silicon Valley\u2019s Start-Up Machine Needs Fixing",
    "meta": {"source":"The New York Times"},
            "url":"https://github.com/rdbc-io/rdbc/issues/86
           },
    }
"""
from glob import glob
from os.path import join, relpath
from utils_peter import pdf_dir, summary_dir, save_jsonl, load_json


def save_pages(summary_dir):
    path_list = list(glob(join(summary_dir, '*.json')))
    print('path_list=%d' % len(path_list))
    summary_list = [load_json(path) for path in path_list]
    print('summary_list=%d' % len(summary_list))
    summary_list = [summary for summary in summary_list if 'path' in summary]
    print('summary_list=%d' % len(summary_list))
    entry_list = []
    for summary in summary_list:
        # if 'path' not in summary:
        #     continue
        assert 'path' in summary, sorted(summary)
        entry_list.extend(summary_to_entries(summary))
    print('entry_list=%d' % len(entry_list))
    entry_list = [entry for entry in entry_list if len(entry[2]) <= 100]
    print('entry_list=%d' % len(entry_list))
    entry_list.sort(key=entry_key)
    prodigy_list = [to_prodigy(*entry) for entry in entry_list]
    print('prodigy_list=%d' % len(prodigy_list))
    save_jsonl('all.pages.jsonl', prodigy_list)


def entry_key(entry):
    name, page, text = entry
    blank = 'blank' in text.lower()
    return not blank, len(text), page, name


def summary_to_entries(summary):
    """
        "Height": 140,
        "Width": 59.3,
        "marked_graph": [1],
        "marked_text": [1],
        "n_chars": 2936,
        "n_pages": 1,
        "name": "-patente-de-invencion-1445369-1.pdf",
        "page_texts"
    """
    name = summary['path']
    page_texts = summary['page_texts']
    marked_text = summary['marked_text']
    marked_graph = summary['marked_graph']
    pages = sorted(set(marked_text) - set(marked_graph))
    entries = [(name, p, page_texts[p - 1]) for p in pages]
    return entries


def to_prodigy(path, page, text):
    """
        {"text":"Uber\u2019s Lesson: Silicon Valley\u2019s Start-Up Machine Needs Fixing",
        "meta":{"source":"The New York Times"},
                "url":"https://github.com/rdbc-io/rdbc/issues/86
               },
        }
    """
    # 'file:///Users/pcadmin/testdata/AF+handout+scanned.pdf'
    # path = join(pdf_dir, name)
    # assert exists(path), (path, [pdf_dir, name])
    # url = 'file://%s#page=%d' % (path, page)
    # http://localhost:8000/-patente-de-invencion-1445369-1.pdf
    name = relpath(path, pdf_dir)
    # assert False, name
    url = 'http://localhost:8000/%s#page=%d' % (name, page)

    return {
        'text': text,
        'meta': {
            # 'source': '%s : page %d' % (name, page),
            'url': url,
        }
    }


save_pages(summary_dir)
