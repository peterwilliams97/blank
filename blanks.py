import pandas as pd
import numpy as np
from pprint import pprint


pd.set_option('display.max_columns', 200)
pd.set_option('display.width', 1000)


def parse_pages(text):
    # print('$$$', text, type(text))
    if isinstance(text, float) and np.isnan(text):
        return None
    vals = [int(s.strip()) for s in text.split(',')]
    return [v - 1 if v > 0 else v for v in vals]


df = pd.read_csv('blank_pages.csv')
print(df.describe())
print(df)
print(df.columns)
pages = df['What page?']
i_name = list(df.columns).index('Document name')
i_pages = list(df.columns).index('What page?')

print('i_pages=%d' % i_pages)
assert i_pages >= 0, i_pages
print(pages)
print(pages.dtype)
page_list = []
blank_pages_map = {}
for _, row in df.iterrows():
    name = 'blank_pages_%s' % row[i_name]
    vals = parse_pages(row[i_pages])
    page_list.append((name, vals))
    blank_pages_map[name] = vals

for i, (n, p) in enumerate(page_list):
    print(i, n, p)
pprint(blank_pages_map)
