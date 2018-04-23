"""
    Find blank pages in documents
"""
import os
from glob import glob
from collections import defaultdict
from utils_peter import load_json, save_json, base_name
from bs4 import BeautifulSoup
import re
# from blanks import blank_pages_map


def get_page_summary(summary_path, prefix_len):
    summary = load_json(summary_path)
    page_summaries = summary['page_summaries']
    for i in range(len(page_summaries)):
        page_summaries[i]['text'] = summary['page_texts'][i][:prefix_len].replace('\n', ' ')
    return page_summaries


def get_text(summary_path):
    summary = load_json(summary_path)
    return summary['text']


def get_page_texts(summary_path):
    """Return 'page_texts' field of json dict with path `summary_path`.
        This is a list of one string per page for the pages in the summarized PDF.
    """
    summary = load_json(summary_path)
    return summary['page_texts']


def find_no_text_pages(page_texts):
    """Find the pages in the page text list `page_texts` (created by  make_page_corpus.py) that
        contain no text
        Returns: list of empty page numbers (page numbers start at zero)
    """
    return [i for i, text in enumerate(page_texts) if not text]


RE_PAGE_NUMBER = re.compile(r'^\s*(Page\:?)?\s*\d+\s*$', re.DOTALL)


def is_page_number(text):
    return RE_PAGE_NUMBER.search(text) is not None


if False:
    text = 'Index\nSymbols\n64-bit Python\ninstalling\n10\n<binary_'
    print(is_page_number(text))
    m = RE_PAGE_NUMBER.search(text)
    print(m.group(0))
    print(m.groups())
    assert False


def find_same(index_text, indexes, text):
    """`index_text`[i] for in `indexes` is a list of strings that contain `text` as a substring in
        increasing length
        Returns: Indexes in `indexes` for which `page_texts`[i] are identical to `text`
    """
    indexes_watermark = []
    for i, idx in enumerate(indexes):
        t = index_text[idx]
        if t != text:
            assert len(t) > len(text), (i, idx, len(t), len(text))
            pos = t.find(text)
            assert pos >= 0, '\n%r\n%r' % (t, text)
            if pos > 0 and not is_page_number(t[:pos]):
                continue
            pos1 = pos + len(text)
            if pos1 < len(t) and not is_page_number(t[pos1:]):
                continue
            print('^^', len(text), text[:100], indexes[:i])
            assert len(t) < 200, (len(t), pos, pos1,
                is_page_number(t[:pos]), is_page_number(t[pos1:]),
                t[:pos][:50], t[pos1:][:50])

            indexes_watermark.append(idx)
            assert all(len(index_text[j]) < 200 for j in indexes_watermark)
            return indexes[:i]
    # indexes_watermark = indexes
    # assert all(len(index_text[j]) < 200 for j in indexes_watermark)
    return indexes_watermark


def find_watermark_pages(page_texts, min_len, max_len):
    """Find the pages in the page text list `page_texts` (created by  make_page_corpus.py) that
        contain only a text watermark
        where watermark length is between `min_len` and `max_len` characters inclusive.
        Returns: indexes of watermarked pages, text of watermark
    """
    index_text = {i: text for i, text in enumerate(page_texts)}
    indexes = list(index_text)
    indexes.sort(key=lambda i: (len(index_text[i]), index_text[i]))
    if len(indexes) >= 2:
        for i, idx in enumerate(indexes[:-1]):
            text = index_text[idx]
            if len(text) < min_len:
                continue
            if len(text) >= max_len:
                break
            ok = all(text in index_text[k] for k in indexes[i + 1:])
            # print('^^^', i, ok, [text in index_text[k] for k in indexes[i + 1:]][:10], text)
            if ok:
                indexes_watermark = find_same(index_text, indexes[i + 1:], text)
                assert all(len(page_texts[j]) < 200 for j in indexes_watermark)
                return indexes_watermark, text
    return [], None


def add_lists(a, b):
    return sorted(set(a) | set(b))


# 1800805096 ref 67496696
def lists_equal(a, b):
    if bool(a) != bool(b):
        print('@0', (a, b))
        return False
    if not a and not b:
        return True
    if len(a) != len(b):
        print('@1', (a, b))
        return False
    for x, y in zip(a, b):
        if x != y:
            print('@2', (x, y), (a, b))
            return False
    return True


def find_empty_pages(path, blanks, min_len, max_len):
    """Find the empty pages in the processed PDF file `path` (created by  make_page_corpus.py)
        Returns: number of pages, indexes of empty pages, indexes of watermarked pages, text of watermark
    """
    page_texts = get_page_texts(path)
    indexes_empty = find_no_text_pages(page_texts)
    indexes_watermark, text_watermark = find_watermark_pages(page_texts, min_len, max_len)
    pages_watermark = [page_texts[i] for i in indexes_watermark]
    assert all(len(text) <= max_len for text in pages_watermark), (max_len, [
        len(page_texts[i]) for i in indexes_watermark])

    indexes = add_lists(indexes_empty, indexes_watermark)
    assert lists_equal(indexes, blanks), path
    return len(page_texts), indexes_empty, indexes_watermark, text_watermark, pages_watermark


RE_BLANK = re.compile(r'blank_pages_\d+')


def assign_blanks(path):
    m = RE_BLANK.search(path)
    if not m:
        return m
    pdf = '%s.pdf' % m.group(0)
    return blank_pages_map[pdf]


def find_empty_pages_corpus(root, max_files):
    """Analyze up to `max_files` of the json files in directory `root` which are created by
        make_page_corpus.py
        Write results to stdout

        Returns: list of (name, n_pages, indexes_empty, indexes_watermark, text_watermark)
    """
    path_list = sorted(glob(os.path.join(root, '*.json')))
    path_blanks = {path: assign_blanks(path) for path in path_list}

    if True:
        path_blanks = {k: v for k, v in path_blanks.items() if v}
        path_list = [k for k in path_list if k in path_blanks]

    print(len(path_list), path_list[:20])
    # for p, b in path_blanks.items():
    #     assert b in blank_pages_map, (p, b)
    # print(path_blank)
    # assert path_list
    # assert False
    # path_list = [os.path.join(root, '2013-12-12_rg_final_report.json.json')]
    if max_files > 0:
        path_list = path_list[:max_files]
    print('%d files' % len(path_list))
    empty_docs = []
    for path in path_list:

        n_pages, indexes_empty, indexes_watermark, text_watermark, pages_watermark = find_empty_pages(
            path, path_blanks[path], min_len=5, max_len=200)
        if indexes_empty or indexes_watermark:
            empty_docs.append((base_name(path), n_pages, indexes_empty, indexes_watermark,
                text_watermark, pages_watermark))
    empty_docs.sort(key=lambda x: (-len(x[2]) - len(x[3]), -len(x[3]), x[1], x[0]))
    print('@' * 100)
    for name, n_pages, indexes_empty, indexes_watermark, text_watermark, pages_watermark in empty_docs:
        # if not indexes_watermark:
        #     continue
        if text_watermark:
            text_watermark = '"%s"' % text_watermark.replace('\n', ' ')
        else:
            text_watermark = ''
        print('%4d %4d %4d %-40s %s' % (n_pages, len(indexes_empty), len(indexes_watermark), name,
            text_watermark))
        if indexes_empty:
            print('\tempty: %s' % indexes_empty[:10])
        if indexes_watermark:
            print('\twatermark: %s' % indexes_watermark[:10])
            for idx, text in zip(indexes_watermark[:10], pages_watermark[:10]):
                print('\t%3d: %4d %r' % (idx, len(text), text[:50]))

    return empty_docs


def summarize_all(root, prefix_len, max_files):
    path_list = list(glob(os.path.join(root, '*.json')))
    if max_files > 0:
        path_list = path_list[:max_files]
    print('%d files' % len(path_list))
    page_summaries = {base_name(path): get_page_summary(path, prefix_len) for path in path_list}
    doc_page = {(name, i): summary
                for name, summaries in page_summaries.items()
                for i, summary in enumerate(summaries)
               }
    page_list = list(doc_page)
    page_list.sort(key=lambda k: (doc_page[k]['n_chars'], doc_page[k]['n_lines'], k))

    def extend_dict(page, info):
        info['_name'] = page[0]
        info['_page'] = page[1]
        return info

    page_info_list = [extend_dict(page, doc_page[page]) for page in page_list]
    save_json('page_info_list.json', page_info_list)

    doc_count = defaultdict(int)
    for i, page in enumerate(page_list):
        doc_count[page[0]] += 1
        if doc_count[page[0]] >= 3:
            continue
        info = doc_page[page]
        print('%6d: %4d l %5d c - %-30s "%s"' % (i, info['n_lines'], info['n_chars'],
            page, info['text']))


RE_TAG = re.compile(r'<.*?>')


def trim(tag):
    i = tag.find(' ')
    if i < 0:
        return tag
    return tag[i]


def find_all_tags(root, do_soup):
    print('=' * 80)
    all_tags = defaultdict(int)
    path_list = list(glob(os.path.join(root, '*.json')))
    for i, path in enumerate(path_list):
        print('%3d: %s %8d' % (i, path, os.path.getsize(path)))
        text = get_text(path)
        if do_soup:
            soup = BeautifulSoup(text, "html5lib")
            for tag in soup.find_all():
                all_tags[tag.name] += 1
        else:
            tags = RE_TAG.findall(text)
            tags = [trim(tag[1:-1]) for tag in tags]
            for tag in tags:
                all_tags[tag] += 1

    print('-' * 80)
    for i, tag in enumerate(sorted(all_tags)):
        print('%3d: %-10s %8d' % (i, tag, all_tags[tag]))


pdf_dir = '~/testdata'
text_dir = '~/testdata.pages0'
pdf_dir = os.path.expanduser(pdf_dir)
text_dir = os.path.expanduser(text_dir)
print('pdf_dir=%s' % pdf_dir)
print('text_dir=%s' % text_dir)


if __name__ == '__main__':
    # summarize_all(text_dir, prefix_len=200, max_files=-1)
    find_empty_pages_corpus(text_dir, max_files=-1)
    # find_all_tags(text_dir, False)
