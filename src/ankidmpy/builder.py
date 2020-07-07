from ankidmpy.util import Util
from collections import defaultdict
import shutil
import os.path


class Builder:

    @classmethod
    def build(cls, decks, src_dir, build_dir, lang):
        glbals = dict(deck=Util.getJson(os.path.join(src_dir, 'deck.json')),
                      config=Util.getJson(os.path.join(src_dir, 'config.json')),
                      model=Util.getJson(os.path.join(src_dir, 'model.json')),
                      media=Util.getFilesList(os.path.join(src_dir, 'media')),
                      templates=Util.getTemplates(
                          os.path.join(src_dir, 'templates')),
                      desc=Util.getRaw(os.path.join(src_dir, 'desc.html')),
                      css=Util.getRaw(os.path.join(src_dir, 'style.css')),
                      data=Util.getCsv(os.path.join(src_dir, 'data.csv')))

        languages = list(glbals['data'].keys())
        if lang:
            if lang not in languages:
                Util.err("Language '%s' is not available." % (lang,))
            languages = [lang]

        for lang in languages:
            decks_build = cls._readDecks(decks, os.path.join(src_dir, 'decks'))
            for deck, deck_build in decks_build.items():
                Util.msg("Building deck: %s (Language: %s)" % (deck, lang))

                deck_build['deck']['uuid'] = Util.uuidEncode(
                    deck_build['deck']['uuid'], lang)
                deck_build['config']['uuid'] = Util.uuidEncode(
                    deck_build['config']['uuid'], lang)
                deck_build['model']['uuid'] = Util.uuidEncode(
                    deck_build['model']['uuid'], lang)

                deck_data = {
                    '__type__':
                        'Deck',
                    'crowdanki_uuid':
                        deck_build['deck']['uuid'],
                    'name':
                        Util.filenameToDeck(deck if lang ==
                                            'default' else "%s[%s]" %
                                            (deck, lang)),
                    'desc':
                        deck_build.get('@desc') or glbals['desc']
                }
                deck_data.update(glbals['deck'])
                deck_data.update(deck_build['@deck'])

                deck_data['deck_configurations'] = [{
                    '__type__': 'DeckConfig',
                    'crowdanki_uuid': deck_build['config']['uuid'],
                    'name': deck_build['config']['name']
                }]
                deck_data['deck_configurations'][-1].update(glbals['config'])
                deck_data['deck_configurations'][-1].update(
                    deck_build['@config'])

                deck_data['deck_config_uuid'] = deck_build['config']['uuid']

                deck_templates_info = []
                k = 0
                for template in deck_build['templates']:
                    template_filename = Util.ensureFilename(template)
                    if not template_filename in glbals['templates']:
                        cls.err("Field template '%s% not found." % (template,))
                    deck_templates_info.append(dict(name=template, ord=k))
                    deck_templates_info[-1].update(
                        glbals['templates'][template_filename])
                    k += 1

                deck_fields_info = []
                i = 0
                for field in deck_build['fields']:
                    if field not in glbals['data'][lang]:
                        Util.err("Field '%s' not found" % (field,))
                    deck_fields_info.append(dict(name=field, ord=i))
                    deck_fields_info[-1].update(Util.getFieldDefaults())
                    i += 1
                deck_data['note_models'] = [{
                    '__type__': 'NoteModel',
                    'crowdanki_uuid': deck_build['model']['uuid'],
                    'name': deck_build['model']['name'],
                    'flds': deck_fields_info,
                    'tmpls': deck_templates_info,
                    'css': deck_build.get('@css') or glbals['css']
                }]
                deck_data['note_models'][-1].update(glbals['model'])
                deck_data['note_models'][-1].update(deck_build['@model'])

                if 'guid' not in glbals['data'][lang]:
                    Util.err("Missed required 'guid' column in 'data.csv'")

                if len(glbals['data'][lang]['guid']) != len(
                        set(glbals['data'][lang]['guid'])):
                    Util.err(
                        "Found duplicate values in 'guid' column.  Run 'index' command."
                    )

                deck_fields_data = defaultdict(lambda: defaultdict(list))
                deck_media = []
                for field in deck_build['fields']:
                    if field not in glbals['data'][lang]:
                        Util.err("Column '%s' is missing in 'data.csv'." %
                                 (field,))
                    for i, cell in enumerate(glbals['data'][lang][field]):
                        deck_fields_data[i]['fields'].append(cell)
                        # FIXME: This seems like it would lead to duplicates
                        # Should it be seeing if the media_file is referenced??
                        for media_file in glbals['media']:
                            if cell in media_file:
                                deck_media.append(media_file)

                for i, cell in enumerate(glbals['data'][lang]['guid']):
                    if not cell:
                        Util.err(
                            """Missing value in the 'guid' field in the row:
%s
Run 'index' command to fix the problem.""" %
                            (Util.toJson(deck_fields_data[i]['fields']),))
                    deck_fields_data[i]['guid'] = Util.guidDecode(
                        cell, deck_build['model']['uuid'])

                if 'tags' in glbals['data'][lang]:
                    for i, cell in enumerate(glbals['data'][lang]['tags']):
                        deck_fields_data[i]['tags'] = cell.split(' ')

                deck_data['media_files'] = deck_media
                deck_data['notes'] = []
                for i, row in sorted(deck_fields_data.items(),
                                     key=lambda x: x[0]):
                    deck_data['notes'].append({
                        '__type__': 'Note',
                        'data': '',
                        'fields': row['fields'],
                        'flags': 0,
                        'guid': row['guid'],
                        'note_model_uuid': deck_build['model']['uuid'],
                        'tags': row.get('tags') or []
                    })

                localized_deck = deck if lang == 'default' else '_'.join(
                    (deck, lang))
                build_dir = build_dir or 'build'
                deck_dir = os.path.join(build_dir, localized_deck)
                Util.prepareDir(deck_dir)
                with open(os.path.join(deck_dir, localized_deck + '.json'),
                          'w') as f:
                    f.write(Util.toJson(deck_data))

                Util.prepareDir(os.path.join(deck_dir, 'media'))
                for media_file in deck_media:
                    shutil.copy(os.path.join(src_dir, 'media', media_file),
                                os.path.join(deck_dir, 'media', media_file))

    @classmethod
    def _readDecks(cls, decks, directory):
        decks_data = dict()

        if not decks:
            decks = Util.getFilesList(directory)

        for deck in decks:
            deck_filename = Util.deckToFilename(deck)
        dirnm = os.path.join(directory, deck_filename)
        if os.path.exists(dirnm) and os.path.isdir(dirnm):
            decks_data[deck_filename] = cls._readDeck(dirnm)
        else:
            Util.err("Deck not found: %s" % (dirnm,))

        return decks_data

    @classmethod
    def _readDeck(cls, directory):
        inDir = lambda fn: os.path.join(directory, fn)
        deck_data = Util.getJson(inDir('build.json'), required=False)
        print("DAM", deck_data)
        deck_data['@deck'] = Util.getJson(inDir('deck.json'), required=False)
        deck_data['@config'] = Util.getJson(inDir('config.json'),
                                            required=False)
        deck_data['@desc'] = Util.getRaw(inDir('info.html'), required=False)
        deck_data['@model'] = Util.getJson(inDir('model.json'), required=False)
        deck_data['@css'] = Util.getRaw(inDir('style.css'), required=False)
        return deck_data
