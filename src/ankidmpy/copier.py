from ankidmpy.util import Util
import shutil
import os.path


class Copier:

    @classmethod
    def copy(cls, deck1, deck2, base):
        deck1_path = os.path.join(base, 'decks', Util.deckToFilename(deck1))

        if not os.path.isdir(deck1_path):
            Util.err("Source deck not found: %s" % (deck1,))

        deck2_suffix = ""
        if deck2:
            deck2_path = os.path.join(base, 'decks', Util.deckToFilename(deck2))
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
            Util.err("Cannot copy files")

        deck_build = Util.getJson(os.path.join(deck2_path, 'build.json'))

        deck_build['deck']['uuid'] = Util.createUuid()
        deck_build['config']['uuid'] = Util.createUuid()
        deck_build['model']['uuid'] = Util.createUuid()

        with open(os.path.join(deck2_path, 'build.json'), 'w') as f:
            f.write(Util.toJson(deck_build))

        Util.msg("Created deck: %s" % deck2 if deck2 else deck1 + deck2_suffix)
