#!/usr/bin/env python3

# This file is a part of rebuild-title-database.
#
# Copyright (c) 2020 Ian Burgwin
# This file is licensed under The MIT License (MIT).
# You can find the full license text in LICENSE.md in the root of this project.

from argparse import ArgumentParser
import gzip
from hashlib import sha256
from pathlib import Path
import sys

from pyctr.crypto import CryptoEngine, Keyslot

parser = ArgumentParser(description='Copy a clean version of title.db and import.db.')
parser.add_argument('-b', '--boot9', help='boot9')
parser.add_argument('-m', '--movable', help='movable.sed', required=True)
parser.add_argument('-s', '--sd', help='SD card (containing "Nintendo 3DS")')

args = parser.parse_args()

crypto = CryptoEngine(boot9=args.boot9)
crypto.setup_sd_key_from_file(args.movable)

id0 = Path(args.sd) / 'Nintendo 3DS' / crypto.id0.hex()

# Only continue if there is one id1 directory.
# If there isn't, the user needs to remove the unwanted ones.
id1_list = [x for x in id0.iterdir() if len(x.parts[-1]) == 32]
if len(id1_list) > 1:
    print('There are multiple id1 directories in', id0, file=sys.stderr)
    print('Please remove the rest.', file=sys.stderr)
    sys.exit(1)
elif len(id1_list) < 1:
    print('No id1 directory could be found in', id0, file=sys.stderr)
    sys.exit(2)

id1 = id1_list[0]

dbs_folder = id1 / 'dbs'
dbs_folder.mkdir(exist_ok=True)

title_db_path = dbs_folder / 'title.db'
import_db_path = dbs_folder / 'import.db'

with gzip.open('title.db.gz') as gzfh:
    db_data = gzfh.read()

with title_db_path.open('wb') as fh:
    with crypto.create_ctr_io(Keyslot.SD, fh, CryptoEngine.sd_path_to_iv('/dbs/title.db')) as cfh:
        cmac = crypto.create_cmac_object(Keyslot.CMACSDNAND)
        cmac_data = [b'CTR-9DB0', 0x2.to_bytes(4, 'little'), db_data[0x100:0x200]]
        cmac.update(sha256(b''.join(cmac_data)).digest())

        cfh.write(cmac.digest())
        cfh.write(db_data[0x10:])

with import_db_path.open('wb') as fh:
    with crypto.create_ctr_io(Keyslot.SD, fh, CryptoEngine.sd_path_to_iv('/dbs/import.db')) as cfh:
        cmac = crypto.create_cmac_object(Keyslot.CMACSDNAND)
        cmac_data = [b'CTR-9DB0', 0x3.to_bytes(4, 'little'), db_data[0x100:0x200]]
        cmac.update(sha256(b''.join(cmac_data)).digest())

        cfh.write(cmac.digest())
        cfh.write(db_data[0x10:])
