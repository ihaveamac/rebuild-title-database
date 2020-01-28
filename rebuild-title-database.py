#!/usr/bin/env python3

# This file is a part of rebuild-title-database.
#
# Copyright (c) 2020 Ian Burgwin
# This file is licensed under The MIT License (MIT).
# You can find the full license text in LICENSE.md in the root of this project.

from argparse import ArgumentParser
from pathlib import Path
from random import randint
import sys

from pyctr.crypto import CryptoEngine, Keyslot
from pyctr.type.ncch import NCCHReader, NCCHSection
from pyctr.type.tmd import TitleMetadataReader
from pyctr.util import roundup

# the size of each file and directory in a title's contents are rounded up to this
TITLE_ALIGN_SIZE = 0x8000

parser = ArgumentParser(description='Rebuilds 3DS Title Database.')
parser.add_argument('-b', '--boot9', help='boot9')
parser.add_argument('-m', '--movable', help='movable.sed', required=True)
parser.add_argument('-s', '--sd', help='SD card (containing "Nintendo 3DS")', required=True)
parser.add_argument('-o', '--output', help='output directory for title info entries', required=True)

args = parser.parse_args()

crypto = CryptoEngine(boot9=args.boot9)
crypto.setup_sd_key_from_file(args.movable)

out = Path(args.output)
out.mkdir(exist_ok=True)

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

for tmd_path in id1.rglob('*.tmd'):
    tmd_id = int(tmd_path.name[0:8], 16)
    tmd_path_for_cid = '/' + '/'.join(tmd_path.parts[len(id1.parts):])

    with tmd_path.open('rb') as tmd_fh:
        with crypto.create_ctr_io(Keyslot.SD, tmd_fh, crypto.sd_path_to_iv(tmd_path_for_cid)) as tmd_cfh:
            tmd = TitleMetadataReader.load(tmd_cfh)

    print('Parsing', tmd.title_id)

    if tmd.title_id.startswith('0004008c'):
        # DLC puts contents into different folders, the first content always goes in the first one
        content0_path = tmd_path.parent / '00000000' / (tmd.chunk_records[0].id + '.app')
        has_manual = False
    else:
        content0_path = tmd_path.parent / (tmd.chunk_records[0].id + '.app')
        has_manual = any(x for x in tmd.chunk_records if x.cindex == 1)
    content0_path_for_cid = '/' + '/'.join(content0_path.parts[len(id1.parts):])

    with content0_path.open('rb') as ncch_fh:
        with crypto.create_ctr_io(Keyslot.SD, ncch_fh, crypto.sd_path_to_iv(content0_path_for_cid)) as ncch_cfh:
            ncch = NCCHReader(ncch_cfh, load_sections=False)
            ncch_product_code = ncch.product_code
            # NCCH version is required for DLP child to work I think. I remember something didn't work if it wasn't
            #   set in the title info entry.
            ncch_version = ncch.version

            try:
                with ncch.open_raw_section(NCCHSection.ExtendedHeader) as e:
                    e.seek(0x200 + 0x30)
                    extdata_id = e.read(8)
            except KeyError:
                # not an executable title
                extdata_id = b'\0' * 8

    tidlow_path = tmd_path.parents[1]

    # this is for the tidlow directory itself, which rglob doesn't include
    sizes = [1]

    # Get every file and include their size, except the directories for DLC content (the contents inside still count).
    # This will also find the cmd file name.
    # This is quite a lazy method to do things but it works!

    # cmd_id should almost certainly be found. If not, the title will be skipped at the end of the loop.
    cmd_id = None
    for f in tmd_path.parents[1].rglob('*'):
        if f.name.endswith('.cmd'):
            cmd_id = int(f.name[0:8], 16)
        # exclude DLC separate directories (00000000, etc) but include all others
        # this won't match the tidlow directory which is not included in this search like above
        try:
            bytes.fromhex(f.name)
            include_if_dir = False
        except ValueError:
            include_if_dir = True
        if not (f.name.startswith('.') or (f.is_dir() and not include_if_dir)):
            sizes.append(f.stat().st_size if f.is_file() else 1)

    if cmd_id is None:
        print(f'Could not find a cmd file for {tmd.title_id}, skipping.')
        continue

    title_size = sum(roundup(x, TITLE_ALIGN_SIZE) for x in sizes)

    # this starts building the title info entry
    title_info_entry_data = [
        # title size
        title_size.to_bytes(8, 'little'),
        # title type, seems to usually be 0x40
        0x40.to_bytes(4, 'little'),
        # title version
        int(tmd.title_version).to_bytes(2, 'little'),
        # ncch version
        ncch_version.to_bytes(2, 'little'),
        # flags_0, only checking if there is a manual
        (1 if has_manual else 0).to_bytes(4, 'little'),
        # tmd content id
        tmd_id.to_bytes(4, 'little'),
        # cmd content id
        cmd_id.to_bytes(4, 'little'),
        # flags_1, only checking save data
        (1 if tmd.save_size else 0).to_bytes(4, 'little'),
        # extdataid low
        extdata_id[0:4],
        # reserved
        b'\0' * 4,
        # flags_2, only using a common value
        0x100000000.to_bytes(8, 'little'),
        # product code
        ncch_product_code.encode('ascii').ljust(0x10, b'\0'),
        # reserved
        b'\0' * 0x10,
        # unknown
        randint(0, 0xFFFFFFFF).to_bytes(4, 'little'),
        # reserved
        b'\0' * 0x2c
    ]

    title_info_entry = b''.join(title_info_entry_data)
    tie_path = out / tmd.title_id
    with tie_path.open('wb') as o:
        o.write(title_info_entry)
