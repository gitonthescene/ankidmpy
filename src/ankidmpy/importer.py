import ankidmpy.util as util
from collections import defaultdict
import shutil
import csv
import os.path


def importIt(path, directory, deck=None):
    path = path.rstrip('/')
    _, basename = os.path.split(path)
    filenm = os.path.join(path, basename + '.json')
    if not os.path.exists(filenm):
        filenm = os.path.join(path, 'deck.json')

    directory = directory.rstrip('/')
    if not directory:
        directory = 'src'

    build_info = defaultdict(dict)

    deck_data = util.getJson(filenm)

    if len(deck_data['deck_configurations']) > 1 or len(
            deck_data['note_models']) > 1:
        util.err("Multiple models or configurations per deck is not supported")

    if len(deck_data['deck_configurations']) == 0 or len(
            deck_data['note_models']) == 0:
        util.err(
            "Decks with empty models or configurations are note supported.  Try adding one card in your deck."
        )

    build_info['deck']['uuid'] = util.createUuid()

    dictSlice = lambda d, kys: {key: d[key] for key in d.keys() & kys}

    deck_info = dictSlice(deck_data, {'dyn', 'extendNew', 'extendRev'})
    deck_info['children'] = []
    with open(os.path.join(directory, 'deck.json'), 'w') as f:
        f.write(util.toJson(deck_info))

    configuration = deck_data['deck_configurations'][0]
    build_info['config']['uuid'] = util.createUuid()
    build_info['config']['name'] = configuration['name']
    configuration_info = dictSlice(configuration, {
        'autoplay', 'dyn', 'lapse', 'maxTaken', 'new', 'replayq', 'rev', 'timer'
    })
    with open(os.path.join(directory, 'config.json'), 'w') as f:
        f.write(util.toJson(configuration_info))

    desc = deck_data['desc']
    with open(os.path.join(directory, 'desc.html'), 'w') as f:
        f.write(desc)

    # FIXME: This is the requirement that there be only one model
    model = deck_data['note_models'][0]
    build_info['model']['uuid'] = util.createUuid()
    build_info['model']['name'] = model['name']
    model_info = dictSlice(model, {'latexPost', 'latexPre', 'type'})
    model_info['vers'] = []

    with open(os.path.join(directory, 'model.json'), 'w') as f:
        f.write(util.toJson(model_info))

    field_list = [v['name'] for v in model['flds']]

    notes = deck_data['notes']
    header = ['guid'] + field_list + ['tags']
    csvfn = os.path.join(directory, 'data.csv')
    try:
        with open(csvfn, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for note in notes:
                row = [
                    util.guidEncode(note['guid'], build_info['model']['uuid'])
                ]

                for i, field in enumerate(field_list):
                    row.append(note['fields'][i])
                row.append(' '.join(note['tags']))

                writer.writerow(row)

    except PermissionError:
        util.err("Cannot write to file: %s" % (csvfn,))

    media_files = deck_data['media_files']
    util.prepareDir(os.path.join(directory, 'media'))
    for media_file in media_files:
        shutil.copy(os.path.join(path, 'media', media_file),
                    os.path.join(directory, 'media', media_file))

    templates = model['tmpls']
    fulltemplateDirname = os.path.join(directory, 'templates')
    util.prepareDir(fulltemplateDirname)
    for template in templates:
        template_filename = util.ensureFilename(template['name'])
        with open(
                os.path.join(fulltemplateDirname, template_filename + '.html'),
                'w') as f:
            f.write(template['qfmt'])
            f.write("\n\n--\n\n")
            f.write(template['afmt'])

    template_list = [v['name'] for v in templates]

    css = model['css']
    with open(os.path.join(directory, 'style.css'), 'w') as f:
        f.write(css + '\n')

    if deck:
        deck_name = deck
    else:
        deck_name = deck_data['name']
        deck = deck_name

    deck_dir_name = util.deckToFilename(deck_name)
    fulldirname = os.path.join(directory, 'decks', deck_dir_name)
    util.prepareDir(fulldirname)

    build_info.update({'fields': field_list, 'templates': template_list})
    with open(os.path.join(fulldirname, 'build.json'), 'w') as f:
        f.write(util.toJson(build_info))

    util.msg("Created deck: %s" % (deck,))
