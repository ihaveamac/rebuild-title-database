# rebuild-title-database
Rebuilds the contents of `title.db` for Nintendo 3DS.

This currently does not interact with `title.db` directly, [save3ds_fuse](https://github.com/wwylele/save3ds) must be used manually to extract and rebuild.

This had minimal testing, but it probably works in most cases. File an issue, send me an email, or contact me on Discord if there are problems.

## Summary
1. [Get boot9 and movable.sed.](https://ihaveamac.github.io/dump.html)
2. Install the requirements: `<py3-cmd> -m pip install --user -r requirements.txt`
3. Run the script with the SD card. Example:  
`<py3-cmd> rebuild-title-database.py -b boot9.bin -m movable.sed -s F: -o out`
4. Import into title.db with save3ds_fuse and the -i flag.

`<py3-cmd>` is often `python3` for *nix and Python from the Microsoft Store, and `py -3` for Windows when installed from python.org.

## fix-titledb.py
This copies a clean version of `title.db` and `import.db` from `title.db.gz`.

## License
`rebuild-title-database.py` and `fix-titledb.py` are under the MIT license.
