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
]

class MarkdownFormatter:
    def header(self):
        print('| Package name | Version | Unreleased commits |')
        print('|----|----|----|')


    def body_item(self, res):
        print(f'| {res.name} | {res.pypi_version} | |')

        for _dummy, headline in res:
            print(f'| | | {headline} |')

    def footer(self):
        pass


class TextFormatter:
    def header(self):
        pass

    def body_item(self, res):
        print(f'- {res.name} (v{res.pypi_version})')
        for _dummy, headline in res:
            print(f'  - {headline}')

    def footer(self):
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

    def has_commits(self):
        return len(self.commits.commits) > 0

    def __iter__(self):
        for c in self.commits.commits:
            headline = c.message.split('\n')[0]
            yield c, headline


def retrieve_info(package_name, client):
    """Retrieve information about latest PyPI release."""
    endpoint = 'https://pypi.org/pypi/{}/json'.format(package_name)
    res = client.get(endpoint)
    if res.status_code == 200:
        return res.json()
    return None


def compare_pkg(name, gh, client):
    pypi = retrieve_info(name, client)
    pypi_version = pypi['info']['version']

    repo = gh.repository('inveniosoftware', name)

    return Comparison(
        name,
        pypi_version,
        repo.compare_commits(f'v{pypi_version}', 'master'),
    )

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
    formatter.header()
    for p in sorted(packages):
        formatter.body_item(compare_pkg(p, gh, client))
    formatter.footer()

if __name__ == '__main__':
    cli()
