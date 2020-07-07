import ankidmpy.util as util
import csv
import os.path


def indexIt(full, base):
    filenm = os.path.join(base, 'data.csv')
    try:
        with open(filenm, newline='') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader)
            guid_column = None
            try:
                guid_column = header.index('guid')
            except ValueError:
                util.err("Missing 'guid' column")
            data = list(reader)
    except PermissionError:
        util.err("Cannot read file: %s" % (filenm,))

    guids = []
    try:
        with open(filenm, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for row in data:
                guid = row[guid_column]
                if not guid or (guid in guids) or full:
                    guid = util.createGuid()
                guids.append(guid)
                # FIXME: I'm assuming we're supposed to use the guid
                # row[guid_column] = guid
                writer.writerow(row)

    except PermissionError:
        util.err("Cannot write to file: %s" % (filenm,))

    util.msg("Successfully reindexed 'data.csv'")
