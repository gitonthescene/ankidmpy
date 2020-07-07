import csv
import json
import re
from collections import defaultdict
import uuid
import random
import os.path
import sys

GUID_CHARS = 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789' + "!#$%&()*+,-./:;<=>?@[]^_`{|}~"


def prepareDir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory, 0o755)
    if not os.path.isdir(directory):
        raise RuntimeError("Cannot create directory: %s" % (directory,))


def msg(msg):
    print(msg)


def err(msg):
    raise RuntimeError(msg)


def warn(msg):
    print(msg, file=sys.stderr)


def toJson(data):
    res = json.dumps(data, indent=2, ensure_ascii=False)
    return re.sub(r'/^(  +?)\\1(?=[^ ])/m', '\1', res)


def getFilesList(directory, typ='file'):
    data = []
    try:
        for fn in os.listdir(directory):
            if fn in ('.', '..'):
                continue
            if typ == 'file' and os.path.isfile(os.path.join(directory, fn)):
                data.append(fn)
            elif typ == 'dir' and os.path.isdir(os.path.join(directory, fn)):
                data.append(fn)
            else:
                data.append(fn)
    except:
        pass

    return data


def getJsons(directory):
    return [
        getJson(os.path.join(directory, fn)) for fn in getFilesList(directory)
    ]


def getFields(directory):
    return dict((base, getJson(os.path.join(directory, base + ext)))
                for base, ext in map(os.path.splitext, getFilesList(directory))
                if ext == '.json')


def getTemplates(directory):
    data = dict()
    for fn in getFilesList(directory):
        base, ext = os.path.splitext(fn)
        if ext != '.html':
            continue
        html = getRaw(os.path.join(directory, fn))
        lines = html.splitlines()
        try:
            idx = lines.index('--')
        except ValueError:
            raise RuntimeError(
                "Incorrect template: %s.  It must consist of two parts divided by '--' on a separate line."
            )
        data[base] = dict(qfmt='\n'.join(lines[:idx]),
                          afmt='\n'.join(lines[idx + 1:]),
                          name=base,
                          bafmt='',
                          bqfmt='',
                          did=None)
    return data


def getRaw(fn, required=True):
    if not required and not os.path.exists(fn):
        return None
    with open(fn) as f:
        contents = f.read()
    return contents


def getFieldDefaults():
    return dict(font='Arial', media=[], rtl=False, size=20, sticky=False)


def getJson(fn, required=True):
    data = getRaw(fn, required)
    if not data:
        return []
    return json.loads(data)


def getCsv(fn, required=True):
    if not required and not os.path.exists(fn):
        return None

    langs = defaultdict(dict)
    result = defaultdict(lambda: defaultdict(list))
    with open(fn, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)
        for i, col in enumerate(header):
            if ':' in col:
                field, lang = col.rsplit(':', 1)
                if field == 'guid':
                    warn('Translating "guid" field doesn\'t make any sense.')
                langs[lang][field] = i
            else:
                langs['default'][col] = i

        for lang, cols in langs.items():
            if lang != 'default':
                langs[lang].update(langs['default'])

            langs[lang] = cols = dict(
                reversed(pr) for pr in langs[lang].items())

        for row in reader:
            for lang, cols in langs.items():
                for i, cell in enumerate(row):
                    if i in cols:
                        result[lang][cols[i]].append(cell)

    if not result:
        # Create one row anyway
        for lang, cols in langs.items():
            for i, col in enumerate(cols):
                result[lang][col].append('')

    return result


def createGuid():
    table = GUID_CHARS
    num = random.randint(0, 2**63)
    buf = ""
    while num:
        mod = num % len(table)
        num = int((num - mod) / len(table))
        buf = table[mod] + buf
    return buf


def createUuid():
    return str(uuid.uuid1())


def uuidEncode(uuid, lang):
    if lang == 'default':
        return uuid
    table = '0123456789abcdef'
    lang_code = sum(ord[c] for c in lang)

    result = ''
    for a in uuid:
        if a == '-':
            result += '-'
            continue
        try:
            an = table.index(a)
        except:
            err("Cannot encode 'uuid': uuid char not found: %s. 'lang' = %s, 'uuid' = %s"
                % (a, lang, uuid))
        cn = an + lang_code % len(table)
        result += table[cn]

    return result


def guidEncode(guid, uuid):
    return _guidTransform(guid, uuid, 'encode')


def guidDecode(guid, uuid):
    return _guidTransform(guid, uuid, 'decode')


def _guidTransform(guid, uuid, direction='encode'):
    table = GUID_CHARS
    i = 0
    result = ''
    for b in uuid:
        cn = 0
        a = guid[i]
        try:
            an = table.index(a)
        except:
            err("Cannot encode 'guid': guid char not found: %s.  'guid' = %s, 'uuid' = %s"
                % (a, guid, uuid))
        try:
            bn = table.index(b)
        except:
            err("Cannot encode 'guid': guid char not found: %s.  'guid' = %s, 'uuid' = %s"
                % (b, guid, uuid))

        if dir == 'encode':
            cn = an - bn
        else:
            cn = an + bn

        if cn >= len(table):
            cn = cn % len(table)
        elif cn < 0:
            cn = len(table) + cn

        result += table[cn]
        i = (i + 1) % len(guid)

    # FIXME: Original code wrapped around and overwrote beginning if len(guid) < len(uuid)
    # Is this just a makeshift hash?  I guess we check that the generated hashes are unique
    # afterward.  I guess you roll the dice when you reindex.  GUID seems to be a misnomer.

    rln = len(result)
    gln = len(guid)
    if rln < gln:
        return result
    if rln % gln == 0:
        return result[-gln:]

    split = (int(rln / gln)) * gln
    return result[split:] + result[-gln:split]


def isDirEmpty(directory):
    try:
        return len(os.listdir(directory)) - 2
    except:
        return None


def deckToFilename(deck):
    filename = deck.replace('_', '___')
    filename = filename.replace('::', '__')
    return ensureFilename(filename)


def filenameToDeck(filename):
    deck = re.sub(r'(_+)', lambda m: '::' if len(m[1]) == 2 else m[1], filename)
    deck = deck.replace('___', '_')
    return deck


def ensureFilename(filename):
    allowed_chars = 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789' + "$-_ "
    result = ''
    for char in filename:
        result += char if char in allowed_chars else '-'

    return result


def checkFieldName(name):
    if name in ('guid', 'tags'):
        err("Fields with names 'guid' and 'tags' are reserved.  Please rename them first."
           )
    return name
