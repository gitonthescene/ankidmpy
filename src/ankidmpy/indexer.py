from ankidmpy.util import Util
import csv
import os.path


class Indexer:

    @classmethod
    def indexIt(cls, full, base):
        filenm = os.path.join(base, 'data.csv')
        try:
            with open(filenm, newline='') as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader)
                guid_column = None
                try:
                    guid_column = header.index('guid')
                except ValueError:
                    Util.err("Missing 'guid' column")
                data = list(reader)
        except PermissionError:
            Util.err("Cannot read file: %s" % (filenm,))

        guids = []
        try:
            with open(filenm, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(header)
                for row in data:
                    guid = row[guid_column]
                    if not guid or (guid in guids) or full:
                        guid = Util.createGuid()
                    guids.append(guid)
                    # FIXME: I'm assuming we're supposed to use the guid
                    # row[guid_column] = guid
                    writer.writerow(row)

        except PermissionError:
            Util.err("Cannot write to file: %s" % (filenm,))

        Util.msg("Successfully reindexed 'data.csv'")
