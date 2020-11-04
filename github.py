"""Compare latest PyPI release against GitHub commit log
"""

import click
import requests
from github3 import login


GLOBAL_PACKAGES = [
    'invenio-app-rdm',
    'invenio-cli',
    'invenio-drafts-resources',
    'invenio-rdm-records',
    'invenio-records-resources',
    'react-invenio-deposit',
    'react-invenio-forms',
]

class MarkdownFormatter:
    def commit_header(self):
        print('| Package name | Version | Unreleased commits |')
        print('|----|----|----|')


    def commit_body(self, res):
        print(f'| {res.name} | {res.pypi_version} | |')

        for _dummy, headline in res:
            print(f'| | | {headline} |')

    def commit_footer(self):
        pass

    def pr_header(self):
        print('| Package name | Assignee | Pull Request |')
        print('|----|----|----|')

    def pr_body(self, res):
        print(f'| {res.name} | | |')
        for p in res:
            assignees = ", ".join([a.login for a in p.assignees]) or ''
            print(f'| | {assignees} | #{p.number}: {p.title} |')

    def pr_footer(self):
        pass


class TextFormatter:
    def commit_header(self):
        pass

    def commit_body(self, res):
        print(f'- {res.name} (v{res.pypi_version})')
        for _dummy, headline in res:
            print(f'  - {headline}')

    def commit_footer(self):
        pass

    def pr_header(self):
        pass

    def pr_body(self, res):
        print(f'- {res.name}')
        for p in res:
            assignees = ", ".join([a.login for a in p.assignees]) or 'UNASSIGNED'
            print(f'  - #{p.number}: {p.title} ({assignees})')

    def pr_footer(self):
        pass


class FormatterFactory:
    formatters = {
        'md': MarkdownFormatter(),
        'txt': TextFormatter(),
    }

    @classmethod
    def create(cls, format):
        return cls.formatters[format]


class Comparison:
    def __init__(self, name, pypi_version, commits):
        self.name = name
        self.pypi_version = pypi_version
        self.commits = commits

    def __iter__(self):
        for c in self.commits.commits:
            headline = c.message.split('\n')[0]
            yield c, headline


class PRs:
    def __init__(self, name, pulls):
        self.name = name
        self.pulls = pulls

    def __iter__(self):
        for p in self.pulls:
            yield p


def pypi_retrieve_info(package_name, client):
    """Retrieve information about latest PyPI release."""
    endpoint = f'https://pypi.org/pypi/{package_name}/json'
    res = client.get(endpoint)
    if res.status_code == 200:
        return res.json()
    return None


def npm_retrieve_info(package_name, client):
    """Retrieve information about latest PyPI release."""
    endpoint = 'https://registry.npmjs.org/{package_name}'
    res = client.get(endpoint)
    if res.status_code == 200:
        return res.json()
    return None


def compare_pypi(name, gh, client):
    pypi = pypi_retrieve_info(name, client)
    pypi_version = pypi['info']['version']

    repo = gh.repository('inveniosoftware', name)

    return Comparison(
        name,
        pypi_version,
        repo.compare_commits(f'v{pypi_version}', 'master'),
    )

def compare_npm(name, gh, client):
    pkg = npm_retrieve_info(name, client)
    npm_version = pkg['dist-tags']['latest']

    repo = gh.repository('inveniosoftware', name)

    return Comparison(
        name,
        npm_version,
        repo.compare_commits(f'v{npm_version}', 'master'),
    )


def list_prs(name, gh):
    repo = gh.repository('inveniosoftware', name)

    return PRs(
        name,
        repo.pull_requests(state='open', sort='updated'),
    )


#
# Click commands
#
@click.group()
def cli():
    """GitHub inspection

    Examples:

      python github.py unreleased -t <token> -f txt

      python github.py unreleased -t <token> -f md invenio-records-resources
    """

@cli.command()
@click.argument('packages', nargs=-1)
@click.option('--format', '-f', type=click.Choice(['md', 'txt']), default='md', help="Output format.")
@click.option('--token', '-t', required=True, help="GitHub access token.")
def unreleased(packages, format, token):
    """Show unreleased commits.

    Examples:

      python github.py unreleased -t <token> -f txt

      python github.py unreleased -t <token> -f md invenio-records-resources
    """
    # Defaults
    gh = login(token=token)
    client = requests.Session()
    formatter = FormatterFactory.create(format)
    if not packages:
        packages = GLOBAL_PACKAGES

    # Compare and output
    formatter.commit_header()
    for p in sorted(packages):
        if p.startswith('react-'):
            res = compare_npm(p, gh, client)
        else:
            res = compare_pypi(p, gh, client)
        formatter.commit_body()
    formatter.commit_footer()



@cli.command()
@click.argument('packages', nargs=-1)
@click.option('--format', '-f', type=click.Choice(['md', 'txt']), default='md', help="Output format.")
@click.option('--token', '-t', required=True, help="GitHub access token.")
def prs(packages, format, token):
    """Show unreleased commits.

    Examples:

      python github.py prs -t <token> -f txt

      python github.py unreleased -t <token> -f md invenio-records-resources
    """
    # Defaults
    gh = login(token=token)
    formatter = FormatterFactory.create(format)
    if not packages:
        packages = GLOBAL_PACKAGES

    # Compare and output
    formatter.pr_header()
    for p in sorted(packages):
        formatter.pr_body(list_prs(p, gh))
    formatter.pr_footer()

if __name__ == '__main__':
    cli()
