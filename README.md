A python script for creating a dataset of revision information for any article on wikipedia, as well as a few examples of data pulled down.

You need:

- [Python](https://www.python.org/), probably 2.7
- [Requests Library](http://docs.python-requests.org/en/latest/)

See `PullRevisionInfo.py` for usage info.

Revision data is stored in `./RevisionData/ARTICLE_NAME/`.  Two CSVs are generated - one for editor frequency and one for change of size + timing of edits.

Example excel worksheets with canned line/scatter plots are included.