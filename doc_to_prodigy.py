"""
    Convert bitbucket.org/papercutsoftware/document-analysis results to Prodigy format

    {"Name":"blank.pdf",
    "Success":true,"
    "SizeMB":0.002,
    "Duration":0.0006,
    "NumPages":1,
    "Width":215.9,
    "Height":279.4,
    "BlankPages":[1],
    "Error":"",
    "InPath":"/Users/pcadmin/testdata/blank.pdf"
    }

"""
from os.path import join, relpath, expanduser
from utils_peter import pdf_dir, save_jsonl, load_json


def save_pages(details_path):
    """
        details_path: A json file saved by $GOPATH/bin/blanks_explore
    """
    summary_list = load_json(details_path)
    print('summary_list=%d' % len(summary_list))
    print(summary_list[0])
    entry_list = []
    for summary in summary_list:
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
       {
       "Name":"fonts_in_form_xobject.pdf",
       "Success":true,
       "SizeMB":0.006,
       "Duration":0.004,
       "NumPages":1,
       "Width":215.9,
       "Height":279.4,
       "TextMarkedPages":[1],
       "GraphMarkedPages":[1],
       "Error":"",
       "InPath":"/Users/pcadmin/testdata/fonts_in_form_xobject.pdf",
       "Texts":["GO!\n\nGO!"],
       }
    """
    print('-' * 80)
    name = summary['InPath']
    page_texts = none2empty(summary['Texts'])
    marked_text = none2empty(summary['TextMarkedPages'])
    marked_graph = none2empty(summary['GraphMarkedPages'])
    print('marked_text=%d %s' % (len(marked_text), marked_text[:10]))
    print('marked_graph=%d %s' % (len(marked_graph), marked_graph[:10]))
    print('page_texts=%d' % len(page_texts))
    pages = sorted(set(marked_text) - set(marked_graph))
    page2text = {i + 1: p for i, p in enumerate(page_texts)}
    print('pages=%d %s' % (len(pages), pages[:10]))
    entries = [(name, p, page2text[p]) for p in pages if p in page2text]
    return entries


def none2empty(a):
    if a is None:
        return []
    return a


def to_prodigy(path, page, text):
    """
        {"text":"Uber\u2019s Lesson: Silicon Valley\u2019s Start-Up Machine Needs Fixing",
        "meta":{"source":"The New York Times"},
                "url":"https://github.com/rdbc-io/rdbc/issues/86
               },
        }
    """
    name = relpath(path, pdf_dir)
    url = 'http://localhost:8000/%s#page=%d&view=Fit' % (name, page)

    return {
        'text': text,
        'meta': {
            # 'source': '%s : page %d' % (name, page),
            'url': url,
        }
    }


if __name__ == '__main__':
    analysis_dir = expanduser('~/go-work/src/bitbucket.org/papercutsoftware/document-analysis')
    corpus_dir = join(analysis_dir, 'corpus_tests/blanks_details')
    details = join(corpus_dir, 'details_text.json')
    save_pages(details)
