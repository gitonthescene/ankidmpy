import ankidmpy.builder as builder
import ankidmpy.copier as copier
import ankidmpy.indexer as indexer
import ankidmpy.util as util
import ankidmpy.importer as importer
import os.path
import argparse
import sys

DIRNAME, _ = os.path.split(__file__)
TEMPLATES_DIR = os.path.abspath(os.path.join(DIRNAME, 'templates'))
templates = util.getFilesList(TEMPLATES_DIR, 'dir')


def initDeck(args):
    template = args.template
    if not template in templates:
        util.err('Cannot find template: %s' % (template,))

    util.prepareDir(args.base)

    if not util.isDirEmpty(args.base):
        util.err("Directory '%s' is not empty." % (args.base,))

    importer.importIt(os.path.join(TEMPLATES_DIR, template), args.base,
                      args.deck)


def importDeck(args):
    util.prepareDir(args.base)

    if not util.isDirEmpty(args.base):
        util.err("Directory '%s' is not empty." % (args.base,))

    importer.importIt(args.path, args.base, args.deck)


def buildDeck(args):
    builder.build(args.deck, args.base, args.build, args.lang)


def indexDeck(args):
    indexer.indexIt(args.full, args.base)


def copyDeck(args):
    copier.copy(args.deck1, args.deck2, args.base)


def parse_arguments():
    DESCRIPTION = """
    This tool disassembles CrowdAnki decks into collections of files
    and directories which are easy to maintain. It then allows you to can
    create variants of your deck via combining fields, templates and data 
    that you really need. You can also use this tool to create translations
    of your deck by creating localized columns in data files.
    """
    parser = argparse.ArgumentParser(prog="anki-dm", description=DESCRIPTION)
    parser.set_defaults(command=None)

    subparsers = parser.add_subparsers()

    parser_init = subparsers.add_parser(
        'init', help="Create a new deck from a template.")
    parser_init.add_argument('template',
                             help='Template to use when creating the deck set.')
    parser_init.add_argument(
        '--deck',
        dest='deck',
        help='''Name of the default deck of the deck set being created.
                          If not provided, then the original deck/template name will be used.'''
    )
    parser_init.set_defaults(command=initDeck)

    parser_import = subparsers.add_parser(
        'import', help="Import a CrowdAnki deck to Anki-dm format")
    parser_import.add_argument(
        'path', help='Path to a CrowdAnki deck directory to import.')
    parser_import.add_argument(
        '--deck',
        dest='deck',
        help='''Name of the default deck of the deck set being created.
                          If not provided, then the original deck/template name will be used.'''
    )
    parser_import.set_defaults(command=importDeck)

    parser_build = subparsers.add_parser(
        'build', help="Build Anki-dm deck into CrowdAnki format")
    parser_build.add_argument(
        'deck',
        nargs='*',
        help=
        'Decks to build. If not specified then all decks of the deck set will be built.'
    )
    parser_build.add_argument(
        '--lang',
        dest='lang',
        help='''Build decks for the specific language code.  
                          If omitted then decks for all languages will be built.'''
    )
    parser_build.add_argument('--build',
                              dest='build',
                              help='''Path to the build directory.
                          [Default: build]''')
    parser_build.set_defaults(command=buildDeck)

    parser_copy = subparsers.add_parser(
        'copy', help='Make reindexed copy of Anki-dm deck.')
    parser_copy.add_argument('deck1', help="Source deck")
    parser_copy.add_argument(
        'deck2',
        nargs='?',
        help=
        '''Destination deck. If not provided, this is calculated automatically by suffixing'''
    )
    parser_copy.set_defaults(command=copyDeck)

    parser_index = subparsers.add_parser(
        'index', help="Set guids for rows missing them.")
    parser_index.add_argument('--full',
                              dest='full',
                              action='store_true',
                              help='Reindex all data rows.')
    parser_index.set_defaults(command=indexDeck)

    parser.add_argument('--base',
                        dest='base',
                        default=".",
                        help='''Path to the deck set directory.
                          [Default: src]''')
    parser.add_argument('--templates',
                        dest='templates',
                        action='store_true',
                        help='List all available templates.')

    return parser.parse_args()


def main():

    args = parse_arguments()

    if args.templates:
        if len(templates):
            util.msg('\n'.join(templates))
            sys.exit(0)
        else:
            util.err("No templates found")

    if args.command:
        args.command(args)
