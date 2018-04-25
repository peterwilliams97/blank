"""
    PDF to text conversion
"""
import os
from glob import glob
from collections import defaultdict, OrderedDict
import hashlib
from subprocess import CalledProcessError, Popen, PIPE
import re
from utils_peter import pdf_dir, summary_dir, save_json
from html_to_text import update_summary
import json


KBYTE = 1024
MBYTE = 1024 * 1024

# Settings
min_size = 1 * KBYTE
max_size = 10000 * MBYTE


permission_errors = [
    'You do not have permission to extract text',
    'Permission Error'
]


PDF_BOX = './pdfbox-app-2.0.7.jar'
PDF_SUMMARIZE = './pdf_page_summaries'
for path in [PDF_BOX, PDF_SUMMARIZE]:
    assert os.path.exists(path), path


def run_command(cmd, raise_on_error=True):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()

    if p.returncode != 0:
        so = ''
        se = ''
        if stdout:
            print('~' * 80)
            so = stdout.decode("utf-8")
            print(so)
        if stderr:
            print('^' * 80)
            se = stderr.decode("utf-8")
            print(se)

        if not any(pe in s for s in (so, se) for pe in permission_errors):
            print('-' * 80)
            print('run_command real error')
            print(' '.join(cmd))
            if raise_on_error:
                raise CalledProcessError(p.returncode, cmd)

    return p.returncode, stdout, stderr


def pdf_summarize(pdf_path):
    cmd = [PDF_SUMMARIZE, pdf_path]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        print('FAILURE: retcode=%d stderr=<%s>' % (retcode, stderr))
        return ok, None
    text = stdout.decode('utf-8')
    summary = json.loads(text)
    return ok, summary


def pdf_to_pages(pdf_path):
    """Extract pages from PDF file `pdf_path` using PdfBox
        Returns: ok, text, pages
            ok: Analysis succeeded. PDF is valid
            text: Text of PDF in html format
            pages: Pages of PDF in html format
    """
    cmd = ['java', '-jar', PDF_BOX, 'ExtractText',
           '-html', '-console', pdf_path]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        print('FAILURE: retcode=%d stderr=<%s>' % (retcode, stderr))
        return ok, '', []
    text = stdout.decode('utf-8')
    sep = '<div style="page-break-before:always; page-break-after:always">'
    return ok, text, text.split(sep)[1:]


# Num Pages: 1
RE_NUMPAGES = re.compile(b'Num Pages:\s+(\d+)')


def pdf_num_pages(pdf_path):
    """Use Unidoc to count pages in PDF file `pdf_path`"""
    cmd = ['./pdf_info', pdf_path]
    retcode, stdout, stderr = run_command(cmd, raise_on_error=False)
    ok = retcode == 0
    if not ok:
        return ok, 0
    m = RE_NUMPAGES.search(stdout)
    return ok, int(m.group(1))


xlation = {
    "GraphMarkedPages": 'marked_graph',
    "TextMarkedPages": 'marked_text',
    }


def save_pdf_summary(pdf_path, summary_path):
    """Extract text from `pdf`, break it into pages and write the summary to 'summary_path
    """
    ok, text, pages_html = pdf_to_pages(pdf_path)
    if not ok:
        return
    print('save_pdf_summary: %s->%s' % (pdf_path, summary_path))

    summary = {
        'path': pdf_path,
        'name': os.path.basename(pdf_path),
        'n_pages': len(pages_html),
        'n_chars': sum(len(page) for page in pages_html),
        'pages': pages_html,
        'text': text,
    }

    ok, pages_summary = pdf_summarize(pdf_path)
    if not ok:
        return
    assert pages_summary['NumPages'] == summary['n_pages'], (pdf_path, pages_summary['NumPages'],
                                                             summary['n_pages'])
    for k, v in pages_summary.items():
        if k == 'NumPages':
            continue
        elif k in xlation:
            summary[xlation[k]] = v
        else:
            summary[k] = v

    # NumPages         int
    # Width            float64
    # Height           float64
    # TextMarkedPages  []int
    # GraphMarkedPages []int

    update_summary(summary)

    if not summary_path.endswith('.json'):
        summary_path = '%s.json' % summary_path
    outpath = os.path.abspath(summary_path)
    save_json(outpath, summary)


def sha1_digest(path):
    sha1 = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            data = f.read(50000)
            if not data:
                break
            sha1.update(data)
    return sha1.hexdigest()


def extract_name(path, root, whole=False):
    # print(path)
    # assert False

    name = os.path.relpath(path, root)
    while True:
        head, tail = os.path.split(name)
        if not (head and tail):
            break
        name = '_'.join((head, tail))

    # if root is None:
    #     name = os.path.basename(path)
    # else:
    #     name = os.path.relpath(path, start=root)

    # direct = os.path.dirname(path)
    # for special in ['blank_pages', 'spool', 'MOB-810', 'xarc']:
    #     if special in direct and special not in name:
    #         name = '%s_%s' % (special, name)

    if whole:
        return name
    return os.path.splitext(name)[0]


def flatten_path(path, root):
    path = os.path.relpath(path, root)
    while True:
        head, tail = os.path.split(path)
        if not (head and tail):
            break
        path = '_'.join((head, tail))
    path = os.path.join(root, path)
    assert os.path.isfile(path), path
    return path


def ascii_count(s, limit):
    return len([c for c in s if ord(c) > limit])


def punc_count(s):
    return len([c for c in s if not ((ord('A') <= ord(c) <= ord('Z')) or
                                     (ord('a') <= ord(c) <= ord('z')))])


def find_keeper(paths, root):
    """Return the 1 file in of the identical files in `paths` that we will use"""
    paths = sorted(paths, key=lambda x: (-len(x), x))
    for path in paths:
        other_paths = [p for p in paths if p != path]
        if 'xarc' in path and not any('xarc' in p for p in other_paths):
            print('1 %s -> %s' % (other_paths, path))
            return {path}
        name = extract_name(path, root)
        other_names = [extract_name(p, root) for p in other_paths]

        if all(name in p for p in other_names):
            print('2 %s -> %s' % (other_paths, path))
            return {path}

        for limit in 255, 127:
            if ascii_count(path, limit) < min(ascii_count(p, limit) for p in other_paths):
                print('3 %s -> %s' % (other_paths, path))
                return {path}

        if punc_count(path) < min(punc_count(p) for p in other_paths):
            print('4 %s -> %s' % (other_paths, path))
            return {path}

    print('5 %s -> %s' % (paths[1:], path[0]))
    return {paths[0]}


def corpus_to_keepers(pdf_dir):
    """Return the unique files in `pdf_dir` that we will use"""
    print('corpus_to_keepers: pdf_dir="%s"' % pdf_dir)

    path_list = list(glob(os.path.join(pdf_dir, '**'), recursive=True))
    print('corpus_to_keepers: %d total' % len(path_list))
    path_list = [path for path in path_list if os.path.isfile(path)]
    print('corpus_to_keepers: %d files' % len(path_list))
    path_list = [path for path in path_list if os.path.splitext(path)[1] == '.pdf']
    print('corpus_to_keepers: %d pdf files' % len(path_list))
    # for i, path in enumerate(path_list):
    #     assert os.path.isfile(path), path
    # path_list = [flatten_path(path, pdf_dir) for path in path_list]

    sha1_paths = defaultdict(set)
    xarc = []
    for i, path in enumerate(path_list):
        assert os.path.isfile(path), path
        assert os.path.abspath(path) == path, (os.path.abspath(path), path)
        sha1 = sha1_digest(path)
        sha1_paths[sha1].add(path)
        if 'xarc' in path:
            xarc.append(path)
    print('%d xarc files of %d (raw total: %d)' % (len(xarc), len(sha1_paths), i))
    assert xarc

    for sha1 in sha1_paths:
        paths = sha1_paths[sha1]
        if len(paths) > 1:
            sha1_paths[sha1] = find_keeper(paths, pdf_dir)

    keepers = []
    for paths in sha1_paths.values():
        assert len(paths) == 1, (len(paths), paths)
        keepers.append(list(paths)[0])
    keepers.sort()
    return keepers


exclusions = {
    '/Users/pcadmin/testdata/Year_8_Pythagoras_Booklet.pdf',
    '/Users/pcadmin/testdata/missing.pdf',
    '/Users/pcadmin/testdata/nsdi17-gowda.pdf',
    '/Users/pcadmin/testdata/nsdi17-horn-daniel.pdf',
    '/Users/pcadmin/testdata/rdp2018-03.pdf',
}


def corpus_to_text(pdf_dir, summary_dir):
    """Convert the unique PDF files in `pdf_dir` to file with the same name in `summary_dir`
    """
    keepers = corpus_to_keepers(pdf_dir)

    os.makedirs(summary_dir, exist_ok=True)

    pdf_summary = OrderedDict()
    summary_pdf = OrderedDict()

    for i, pdf_path in enumerate(keepers):

        size = os.path.getsize(pdf_path)
        print('%3d: %s [%.1f]' % (i, pdf_path, size / MBYTE), end=' -> ')
        assert os.path.abspath(pdf_path) == pdf_path

        if min_size <= size <= max_size:
            name = extract_name(pdf_path, pdf_dir)
            assert not name.endswith('.json'), name
            name = '%s.json' % name
            summary_path = os.path.join(summary_dir, name)
            assert summary_path not in summary_pdf, (pdf_path, summary_pdf[summary_path])
            pdf_summary[pdf_path] = summary_path
            summary_pdf[summary_path] = pdf_path
            print(summary_path, end=' ')
            # assert not os.path.exists(summary_path)
            # save_pdf_summary(pdf_path, summary_path)
        print()

    print('^' * 100)
    started = set()
    for i, (pdf_path, summary_path) in enumerate(pdf_summary.items()):
        if pdf_path in exclusions:
            started.add(pdf_path)
            continue
        # if len(started) < len(exclusions):
        #     continue
        print('%4d: %s -> %s' % (i, pdf_path, summary_path), flush=True)
        save_pdf_summary(pdf_path, summary_path)


if __name__ == '__main__':
    corpus_to_text(pdf_dir, summary_dir)
    print('=' * 80)
    for directory in (pdf_dir, summary_dir):
        path_list = list(glob(os.path.join(directory, '**'), recursive=True))
        print('%s: %d files' % (directory, len(path_list)))
