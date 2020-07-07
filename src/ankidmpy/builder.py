import ankidmpy.util as util
from collections import defaultdict
import shutil
import os.path


def build(decks, src_dir, build_dir, lang):
    glbals = dict(deck=util.getJson(os.path.join(src_dir, 'deck.json')),
                  config=util.getJson(os.path.join(src_dir, 'config.json')),
                  model=util.getJson(os.path.join(src_dir, 'model.json')),
                  media=util.getFilesList(os.path.join(src_dir, 'media')),
                  templates=util.getTemplates(os.path.join(
                      src_dir, 'templates')),
                  desc=util.getRaw(os.path.join(src_dir, 'desc.html')),
                  css=util.getRaw(os.path.join(src_dir, 'style.css')),
                  data=util.getCsv(os.path.join(src_dir, 'data.csv')))

    languages = list(glbals['data'].keys())
    if lang:
        if lang not in languages:
            util.err("Language '%s' is not available." % (lang,))
        languages = [lang]

    for lang in languages:
        decks_build = _readDecks(decks, os.path.join(src_dir, 'decks'))
        for deck, deck_build in decks_build.items():
            util.msg("Building deck: %s (Language: %s)" % (deck, lang))

            deck_build['deck']['uuid'] = util.uuidEncode(
                deck_build['deck']['uuid'], lang)
            deck_build['config']['uuid'] = util.uuidEncode(
                deck_build['config']['uuid'], lang)
            deck_build['model']['uuid'] = util.uuidEncode(
                deck_build['model']['uuid'], lang)

            deck_data = {
                '__type__':
                    'Deck',
                'crowdanki_uuid':
                    deck_build['deck']['uuid'],
                'name':
                    util.filenameToDeck(deck if lang ==
                                        'default' else "%s[%s]" % (deck, lang)),
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
            deck_data['deck_configurations'][-1].update(deck_build['@config'])

            deck_data['deck_config_uuid'] = deck_build['config']['uuid']

            deck_templates_info = []
            k = 0
            for template in deck_build['templates']:
                template_filename = util.ensureFilename(template)
                if not template_filename in glbals['templates']:
                    err("Field template '%s% not found." % (template,))
                deck_templates_info.append(dict(name=template, ord=k))
                deck_templates_info[-1].update(
                    glbals['templates'][template_filename])
                k += 1

            deck_fields_info = []
            i = 0
            for field in deck_build['fields']:
                if field not in glbals['data'][lang]:
                    util.err("Field '%s' not found" % (field,))
                deck_fields_info.append(dict(name=field, ord=i))
                deck_fields_info[-1].update(util.getFieldDefaults())
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
                util.err("Missed required 'guid' column in 'data.csv'")

            if len(glbals['data'][lang]['guid']) != len(
                    set(glbals['data'][lang]['guid'])):
                util.err(
                    "Found duplicate values in 'guid' column.  Run 'index' command."
                )

            deck_fields_data = defaultdict(lambda: defaultdict(list))
            deck_media = []
            for field in deck_build['fields']:
                if field not in glbals['data'][lang]:
                    util.err("Column '%s' is missing in 'data.csv'." % (field,))
                for i, cell in enumerate(glbals['data'][lang][field]):
                    deck_fields_data[i]['fields'].append(cell)
                    # FIXME: This seems like it would lead to duplicates
                    # Should it be seeing if the media_file is referenced??
                    for media_file in glbals['media']:
                        if cell in media_file:
                            deck_media.append(media_file)

            for i, cell in enumerate(glbals['data'][lang]['guid']):
                if not cell:
                    util.err("""Missing value in the 'guid' field in the row:

'index' command to fix the problem.""" %
                             (util.toJson(deck_fields_data[i]['fields']),))
                deck_fields_data[i]['guid'] = util.guidDecode(
                    cell, deck_build['model']['uuid'])

            if 'tags' in glbals['data'][lang]:
                for i, cell in enumerate(glbals['data'][lang]['tags']):
                    deck_fields_data[i]['tags'] = cell.split(' ')

            deck_data['media_files'] = deck_media
            deck_data['notes'] = []
            for i, row in sorted(deck_fields_data.items(), key=lambda x: x[0]):
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
            util.prepareDir(deck_dir)
            with open(os.path.join(deck_dir, localized_deck + '.json'),
                      'w') as f:
                f.write(util.toJson(deck_data))

            util.prepareDir(os.path.join(deck_dir, 'media'))
            for media_file in deck_media:
                shutil.copy(os.path.join(src_dir, 'media', media_file),
                            os.path.join(deck_dir, 'media', media_file))


def _readDecks(decks, directory):
    decks_data = dict()

    if not decks:
        decks = util.getFilesList(directory)

    for deck in decks:
        deck_filename = util.deckToFilename(deck)
    dirnm = os.path.join(directory, deck_filename)
    if os.path.exists(dirnm) and os.path.isdir(dirnm):
        decks_data[deck_filename] = _readDeck(dirnm)
    else:
        util.err("Deck not found: %s" % (dirnm,))

    return decks_data


def _readDeck(directory):
    inDir = lambda fn: os.path.join(directory, fn)
    deck_data = util.getJson(inDir('build.json'), required=False)
    deck_data['@deck'] = util.getJson(inDir('deck.json'), required=False)
    deck_data['@config'] = util.getJson(inDir('config.json'), required=False)
    deck_data['@desc'] = util.getRaw(inDir('info.html'), required=False)
    deck_data['@model'] = util.getJson(inDir('model.json'), required=False)
    deck_data['@css'] = util.getRaw(inDir('style.css'), required=False)
    return deck_data
