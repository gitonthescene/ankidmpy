# **ankidmpy**

**ankidmpy** ( pronounced "anki-dumpy" ) is a straightforward port of [anki-dm](https://github.com/OnkelTem/anki-dm)    to `python`.   The original **anki-dm** is written in `PHP` and is a tool to work with the [CrowdAnki plugin](https://github.com/Stvad/CrowdAnki) for the [Anki](https://apps.ankiweb.net/) spaced repetition memory app to facilitate collaborative building of flash card decks. 

## Overview
**CrowdAnki** also aims to facilitate collaboration by extracting all the details of an Anki deck into a single json file for easier editing.  Building on this, **anki-dm** splits this single json file into several files: one containing the raw data, one each for template layout of the cards, one for css styling, etc, allowing each of them to be edited independently.

Reversing the process, you can *build* a **CrowdAnki** file from these edited files and in turn *import* these files back into **Anki** with the plug-in to be used for spaced repetition memorization.

## Usage
The usage is nearly identical to the original **anki-dm** with only slight differences to accommodate standard arg parsing in `python`.

```sh
$ python -m ankidmpy --help
usage: anki-dm [-h] [--base BASE] [--templates]
               {init,import,build,copy,index} ...

This tool disassembles CrowdAnki decks into collections of files and
directories which are easy to maintain. It then allows you to can create
variants of your deck via combining fields, templates and data that you really
need. You can also use this tool to create translations of your deck by
creating localized columns in data files.

positional arguments:
  {init,import,build,copy,index}
    init                Create a new deck from a template.
    import              Import a CrowdAnki deck to Anki-dm format
    build               Build Anki-dm deck into CrowdAnki format
    copy                Make reindexed copy of Anki-dm deck.
    index               Set guids for rows missing them.

optional arguments:
  -h, --help            show this help message and exit
  --base BASE           Path to the deck set directory. [Default: src]
  --templates           List all available templates.
$
```
There are several sub-commands which each take their own options.   The `--base` switch applies to each of these sub-commands and must be supplied before the sub-command.   This switch indicates the root directory to use when looking for or generating new files.

The `--templates` switch simply lists the sample **CrowdAnki** decks which can be built upon to generate new decks and doesn't require a sub-command.

Help for the sub-commands can be found by applying `--help` to the sub-command:

```sh
$ python -m ankidmpy init --help
usage: anki-dm init [-h] [--deck DECK] template

positional arguments:
  template     Template to use when creating the deck set.

optional arguments:
  -h, --help   show this help message and exit
  --deck DECK  Name of the default deck of the deck set being created. If not
               provided, then the original deck/template name will be used.
$
```

## Building
**ankidmpy** is currently written in Pure `Python` with no dependencies.  I've only tried it with Python3.7 so far but it may work in earlier versions.

You can run **ankidmpy** with `python -m ankidmpy` by pointing your `PYTHONPATH` at the `src` directory or you can use [poetry](https://python-poetry.org/docs/) to build a wheel distribution like so:

```sh
$ poetry install
$ poetry build
```
Once you run `poetry install` you can also run **ankidmpy** using the **poetry** script like so:

```sh
$ poetry run anki-dm --help
```
See the **poetry** documentation for more details.
