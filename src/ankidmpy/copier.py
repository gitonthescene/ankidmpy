import ankidmpy.util as util
import shutil
import os.path


def copy(deck1, deck2, base):
    deck1_path = os.path.join(base, 'decks', util.deckToFilename(deck1))

    if not os.path.isdir(deck1_path):
        util.err("Source deck not found: %s" % (deck1,))

    deck2_suffix = ""
    if deck2:
        deck2_path = os.path.join(base, 'decks', util.deckToFilename(deck2))
    else:
        i = 1
        while True:
            deck2_suffix = " (%d)" % (i,)
            deck2_path = deck1_path + deck2_suffix
            if not os.path.exists(deck2_path):
                break
            i += 1

    try:
        shutil.copytree(deck1_path, deck2_path)
    except PermissionError:
        util.err("Cannot copy files")

    deck_build = util.getJson(os.path.join(deck2_path, 'build.json'))

    deck_build['deck']['uuid'] = util.createUuid()
    deck_build['config']['uuid'] = util.createUuid()
    deck_build['model']['uuid'] = util.createUuid()

    with open(os.path.join(deck2_path, 'build.json'), 'w') as f:
        f.write(util.toJson(deck_build))

    util.msg("Created deck: %s" % deck2 if deck2 else deck1 + deck2_suffix)
