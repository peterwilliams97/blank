Blank Page Detection
====================

Setup
-----
Add `pdfbox-app-2.0.7.jar` to path


Instructions
============
* Gather pdf files in `pdf_dir` (default `~/testfiles`)
`prodigy dataset -a "Peter Williams" blank "Blank pages corpus"` once only


Main Process
------------
1. Run pdf_page_summaries to find pages that contain text marks and pages that contain non-text marks.
2. Run `python make_page_corpus.py` to create preprocessed corpus in `summary_dir` (default `~/testdata.pages1`)
3. Use `prodigy textcat.teach blank en_core_web_lg all.pages.jsonl --label BLANK` to examine pages with only text marks and decide which ones are effectively blank


Initial Detection Algorithm
---------------------------
1. Pages with no marks are blank. This won't change.
2. Pages with non-text marks are not blank.
3. Human panel will go through pages with text marks and decide if they are blank
4. Use ML to model 3.


Initial Blank Page Heuristic
----------------------------
These are pages that have only text marks.

1. "Page intentionally left blank"
2. Page number only
3. Watermark only
4. Page number and watermark.


TODO
----
Fix page number detection for ~/testdata/Year_8_Pythagoras_Booklet.pdf
use text location as a hint
Powerpoint decks where successive pages are supersets of previous page. Can we find the last page
in such a sequence?

http://localhost:8000/jkraaijeveld_thesis.pdf#page=3
http://localhost:8000/lantz.dissertation.pdf#page=2
http://localhost:8000/Preservation%20of%20privacy%20in%20public-key%20cryptography.pdf#page=4
http://localhost:8000/10.1.1.458.9390.pdf#page=19
http://localhost:8000/talk_Eval.pdf#page=56
http://localhost:8000/23-parallel-scan.pdf#page=21

HEURISTICS
==========
No mark except near top and bottom of page
Less than 3 lines (usually)

