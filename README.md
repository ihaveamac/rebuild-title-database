# rebuild-title-database
Rebuilds the contents of `title.db` for Nintendo 3DS.

This currently does not interact with `title.db` directly, [https://github.com/wwylele/save3ds](save3ds_fuse) must be used manually to extract and rebuild.

This had minimal testing, but it probably works in most cases. File an issue, send me an email, or contact me on Discord if there are problems.

## Summary
1. [Get boot9 and movable.sed.](https://ihaveamac.github.io/dump.html)
2. Install the requirements: `<py3-cmd> -m pip install --user -r requirements.txt`
3. Run the script with the SD card. Example:  
`<py3-cmd> rebuild-title-database.py -b boot9.bin -m movable.sed -s F: -o out`
4. Import into title.db with save3ds_fuse and the -i flag.

`<py3-cmd>` is often `python3` for *nix and Python from the Microsoft Store, and `py -3` for Windows when installed from python.org.

## fix-titledb.py
This fixes the CMAC of `title.db` on the SD card. With `--copy-clean` it will copy an empty one from `title.db.gz` and fix the CMAC.

## License
`rebuild-title-database.py` and `fix-titledb.py` are under the MIT license.
