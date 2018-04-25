import json
import jsonlines
import os


pdf_dir = '~/testdata'
summary_dir = '~/testdata.pages1'
pdf_dir = os.path.expanduser(pdf_dir)
summary_dir = os.path.expanduser(summary_dir)
print('pdf_dir=%s' % pdf_dir)
print('summary_dir=%s' % summary_dir)


def load_json(path):
    with open(path, 'r') as f:
        obj = json.load(f)
    return obj


def save_json(path, obj):
    with open(path, 'w') as f:
        json.dump(obj, f, indent=4, sort_keys=True)


def save_jsonl(path, obj):
    with jsonlines.open(path, mode='w') as w:
        w.write_all(obj)


def base_name(path):
    base = os.path.basename(path)
    return os.path.splitext(base)[0]
