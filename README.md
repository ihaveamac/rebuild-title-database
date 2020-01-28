# rebuild-title-database
Rebuilds the contents of `title.db` for Nintendo 3DS.

This currently does not interact with `title.db` directly, [https://github.com/wwylele/save3ds](save3ds_fuse) must be used manually to extract and rebuild.

This had minimal testing, but it probably works in most cases. File an issue, send me an email, or contact me on Discord if there are problems.

## Summary
1. [Get boot9 and movable.sed.](https://ihaveamac.github.io/dump.html)
2. Run the script with the SD card. Example:  
`<py3-cmd> rebuild-title-database.py -b boot9.bin -m movable.sed -s F: -o out`
3. Import into title.db with save3ds_fuse and the -i flag.

`<py3-cmd>` is often `python3` for *nix and Python from the Microsoft Store, and `py -3` for Windows when installed from python.org.

## `title.db.gz`
This is a gzip'd empty `title.db` file. This can be added manually with a tool like ninfs, or encrypting it in a script with pyctr. Eventually this tool might put it in place automatically.

Decompress with `gzip -d title.db.gz` or `<py3-cmd> -m gzip -d title.db.gz`.

## License
`rebuild-title-database.py` is under the MIT license.
