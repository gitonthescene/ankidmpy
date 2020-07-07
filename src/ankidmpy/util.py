import csv
import json
import re
from collections import defaultdict
import uuid
import random
import os.path
import sys


class Util:
    GUID_CHARS = 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789' + "!#$%&()*+,-./:;<=>?@[]^_`{|}~"

    @classmethod
    def prepareDir(cls, directory):
        if not os.path.exists(directory):
            os.makedirs(directory, 0o755)
        if not os.path.isdir(directory):
            raise RuntimeError("Cannot create directory: %s" % (directory,))

    @classmethod
    def msg(cls, msg):
        print(msg)

    @classmethod
    def err(cls, msg):
        raise RuntimeError(msg)

    @classmethod
    def warn(cls, msg):
        print(msg, file=sys.stderr)

    @classmethod
    def toJson(cls, data):
        res = json.dumps(data, indent=2, ensure_ascii=False)
        return re.sub(r'/^(  +?)\\1(?=[^ ])/m', '\1', res)

    @classmethod
    def getFilesList(cls, directory, typ='file'):
        data = []
        try:
            for fn in os.listdir(directory):
                if fn in ('.', '..'):
                    continue
                if typ == 'file' and os.path.isfile(os.path.join(directory,
                                                                 fn)):
                    data.append(fn)
                elif typ == 'dir' and os.path.isdir(os.path.join(directory,
                                                                 fn)):
                    data.append(fn)
                else:
                    data.append(fn)
        except:
            pass

        return data

    @classmethod
    def getJsons(cls, directory):
        return [
            cls.getJson(os.path.join(directory, fn))
            for fn in cls.getFilesList(directory)
        ]

    @classmethod
    def getFields(cls, directory):
        return dict(
            (base, cls.getJson(os.path.join(directory, base + ext)))
            for base, ext in map(os.path.splitext, cls.getFilesList(directory))
            if ext == '.json')

    @classmethod
    def getTemplates(cls, directory):
        data = dict()
        for fn in cls.getFilesList(directory):
            base, ext = os.path.splitext(fn)
            if ext != '.html':
                continue
            html = cls.getRaw(os.path.join(directory, fn))
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

    @classmethod
    def getRaw(cls, fn, required=True):
        if not required and not os.path.exists(fn):
            return None
        with open(fn) as f:
            contents = f.read()
        return contents

    @classmethod
    def getFieldDefaults(cls):
        return dict(font='Arial', media=[], rtl=False, size=20, sticky=False)

    @classmethod
    def getJson(cls, fn, required=True):
        data = cls.getRaw(fn, required)
        if not data:
            return []
        return json.loads(data)

    @classmethod
    def getCsv(cls, fn, required=True):
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
                        cls.warn(
                            'Translating "guid" field doesn\'t make any sense.')
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

    @classmethod
    def createGuid(cls):
        table = cls.GUID_CHARS
        num = random.randint(0, 2**63)
        buf = ""
        while num:
            mod = num % len(table)
            num = int((num - mod) / len(table))
            buf = table[mod] + buf
        return buf

    @classmethod
    def createUuid(cls):
        return str(uuid.uuid1())

    @classmethod
    def uuidEncode(cls, uuid, lang):
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
                cls.err(
                    "Cannot encode 'uuid': uuid char not found: %s. 'lang' = %s, 'uuid' = %s"
                    % (a, lang, uuid))
            cn = an + lang_code % len(table)
            result += table[cn]

        return result

    @classmethod
    def guidEncode(cls, guid, uuid):
        return cls._guidTransform(guid, uuid, 'encode')

    @classmethod
    def guidDecode(cls, guid, uuid):
        return cls._guidTransform(guid, uuid, 'decode')

    @classmethod
    def _guidTransform(cls, guid, uuid, direction='encode'):
        table = cls.GUID_CHARS
        i = 0
        result = ''
        for b in uuid:
            cn = 0
            a = guid[i]
            try:
                an = table.index(a)
            except:
                cls.err(
                    "Cannot encode 'guid': guid char not found: %s.  'guid' = %s, 'uuid' = %s"
                    % (a, guid, uuid))
            try:
                bn = table.index(b)
            except:
                cls.err(
                    "Cannot encode 'guid': guid char not found: %s.  'guid' = %s, 'uuid' = %s"
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

    @classmethod
    def isDirEmpty(cls, directory):
        try:
            return len(os.listdir(directory)) - 2
        except:
            return None

    @classmethod
    def deckToFilename(cls, deck):
        filename = deck.replace('_', '___')
        filename = filename.replace('::', '__')
        return cls.ensureFilename(filename)

    @classmethod
    def filenameToDeck(cls, filename):
        deck = re.sub(r'(_+)', lambda m: '::'
                      if len(m[1]) == 2 else m[1], filename)
        deck = deck.replace('___', '_')
        return deck

    @classmethod
    def ensureFilename(cls, filename):
        allowed_chars = 'abcdefghijklmnopqrstuvwxyz' + 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' + '0123456789' + "$-_ "
        result = ''
        for char in filename:
            result += char if char in allowed_chars else '-'

        return result

    @classmethod
    def checkFieldName(cls, name):
        if name in ('guid', 'tags'):
            cls.err(
                "Fields with names 'guid' and 'tags' are reserved.  Please rename them first."
            )
        return name
