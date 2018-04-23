Blank Page Detection
====================

Setup
-----
Add `pdfbox-app-2.0.7.jar` to path


Main Process
------------
1. Run pdf_page_summaries to find pages that contain text marks and pages that contain non-text marks.
2. Examine pages with only text marks and decide which ones are effectively blank


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
Resurrect `text = dehyphenate(text)` in `html_to_text.py`
