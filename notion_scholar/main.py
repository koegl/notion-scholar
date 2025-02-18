import sys
import argparse

from notion_scholar.run import run
from notion_scholar.download import download

from notion_scholar.utilities import get_token
from notion_scholar.config import ConfigManager


def get_parser():
    token = get_token()
    config = ConfigManager().get()

    parser = argparse.ArgumentParser(
        description='notion-scholar',
        usage='Use "notion-scholar --help" or "ns --help" for more information',  # noqa: E501
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Parent parser
    parent_parser = argparse.ArgumentParser(add_help=False)

    # Choice of the subparser
    subparsers = parser.add_subparsers(
        help='Selection of the action to perform.', dest='mode',
    )

    # Run parser
    run_parser = subparsers.add_parser(
        'run', parents=[parent_parser],
        help='Run notion-scholar.',
    )
    run_parser.add_argument(
        '-t', '--token',
        default=None, type=str, metavar='',
        help=f'Token used to connect to Notion. \n(default: {token})',
    )
    run_parser.add_argument(
        '-db', '--database-id',
        default=None, type=str, metavar='',
        help=f'Database that will be furnished. The database_id can be found in the url of the database: \n'
             f'https://www.notion.so/{{workspace_name}}/{{database_id}}?v={{view_id}} \n'
             f'(default: {config.get("database_id", None)})',
    )
    run_parser.add_argument(
        '-s', '--string',
        default=None, type=str, metavar='',
        help='Bibtex entries to add (must be in-between three quotes \"\"\"<bib-string>\"\"\"). '
             'By default, the entries will be saved to the bib file from the config. '
             'It is possible to disable this behavior by changing the "save" option: "ns setup -save false".',
    )
    run_parser.add_argument(
        '-pdf', '--pdf_path',
        default=None, type=str, metavar='',
        help='Path to the pdf file.',
        required=False,
    )

    if config.get('file_path', None) is None:
        group = run_parser.add_mutually_exclusive_group(required=True)
    else:
        group = run_parser.add_argument_group()

    group.add_argument(
        '-f', '--file-path',
        default=None, type=str, metavar='',
        help=f'Bib file that will be used. This argument is required if the bib file is not saved in the config and no bib-string is passed. \n'
             f'(default: {config.get("bib_file_path", None)})',  # noqa: E501
    )

    # Download bibtex parser
    download_parser = subparsers.add_parser(
        'download', parents=[parent_parser],
        help='Download the bibtex entries present in the notion database.',
    )
    download_parser.add_argument(
        '-f', '--file-path',
        default=None, type=str, metavar='', required=False,
        help='File in which the bibtex entries will be saved.',
    )
    download_parser.add_argument(
        '-t', '--token',
        default=None, type=str, metavar='', required=False,
        help=f'Token used to connect to Notion. \n(default: {token})',
    )
    download_parser.add_argument(
        '-db', '--database-id',
        default=None, type=str, metavar='',
        help=f'Database that will be downloaded. The database_id can be found in the url of the database: \n'
             f'https://www.notion.so/{{workspace_name}}/{{database_id}}?v={{view_id}} \n'
             f'(default: {config.get("database_id", None)})',
    )

    # Clear config parser
    clear_parser = subparsers.add_parser(  # noqa: F841
        'clear-config', parents=[parent_parser],
        help='Clear the notion-scholar config.',
    )

    # Inspect config parser
    inspect_parser = subparsers.add_parser(  # noqa: F841
        'inspect-config', parents=[parent_parser],
        help='Inspect the notion-scholar config.',
    )

    # Setup parser
    setup_parser = subparsers.add_parser(
        'set-config', parents=[parent_parser],
        help='Save the provided preferences.',
    )
    setup_parser.add_argument(
        '-f', '--file-path',
        default=None, type=str, metavar='',
        help=f'Save the bibtex file that will be used when running notion-scholar without source arguments. '
             f'The path must be absolute and the file need to exist. '
             f'(current: {config.get("bib_file_path", None)})',
    )
    setup_parser.add_argument(
        '-t', '--token',
        default=None, type=str, metavar='',
        help=f'Save the Notion integration token. \n(current: {token})',
    )
    setup_parser.add_argument(
        '-db', '--database-id',
        default=None, type=str, metavar='',
        help=f'Save the database-id in the user config. '
             f'The database_id can be found in the url of the database: \n'
             f'https://www.notion.so/{{workspace_name}}/{{database_id}}?v={{view_id}} \n'
             f'(current: {config.get("database_id", None)})',
    )

    return parser


def main() -> int:
    parser = get_parser()
    arguments = parser.parse_args()

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 1

    need_token_or_database_id = {
        'run': True,
        'download': True,
        'set-config': False,
        'clear-config': False,
        'inspect-config': False,
    }

    kwargs = vars(arguments)
    mode = kwargs.pop('mode', None)
    config_manager = ConfigManager(**kwargs)

    if need_token_or_database_id[mode]:
        token = get_token()
        if token is None and 'token' in arguments and arguments.token is None:
            parser.error(
                "Error: The '--token' argument is required but not provided nor saved.")

        config = config_manager.get()
        if config.get('database_id', None) is None and 'database_id' in arguments and arguments.database_id is None:
            parser.error(
                "Error: The '--database-id' argument is required but not provided nor saved.")

    if mode == 'run':

        config = config_manager.get()

        token = get_token()

        if token is None:
            parser.error(
                "Error: The '--token' argument is required but not provided nor saved.")

        return run(token,
                   config["database_id"],
                   config.get("file_path"),
                   arguments.string,
                   arguments.pdf_path)

    elif mode == 'download':

        config = config_manager.get()
        return download(config["file_path"],
                        config["token"],
                        config["database_id"])

        # return download(**config_manager.get_download_kwargs())

    elif mode == 'set-config':
        config_manager.setup()
        return 0

    elif mode == 'inspect-config':
        config_manager.inspect()
        return 0

    elif mode == 'clear-config':
        config_manager.clear()
        return 0

    else:
        raise NotImplementedError('Invalid mode.')


if __name__ == '__main__':
    sys.exit(main())
