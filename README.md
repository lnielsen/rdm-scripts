# Helper scripts

### Install

```
$ mkvirtualenv <name>
$ pip install -r requirements.txt
```

### Usage

List all unreleased commits on master/main branch:

```
$ python github.py unreleased -t <gh token> -f md
$ python github.py unreleased -t <gh token> -f txt invenio-theme invenio-search-ui
```

List open PRs against master/main branch:

```
$ python github.py prs -t <gh token> -f txt
$ python github.py unreleased -t <gh token> -f txt invenio-theme invenio-search-ui
```

Supported output formats:

 - ``md``: Markdown table.
 - ``txt``: Bullet list in plain text.
