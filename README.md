# Stats for Minecraft World

Place world save in the same directory as `.py` files. Set `PLAYERDATA_DIR` in `const.py` to `playerdata` directory in your save (usually `<world_name>/playerdata`)

Run `main.py` to generate a CSV file with collected playerdata.

Then analyse it on your own or use `analyse.py` to create charts for specified stats (see `stat_fields` in mentioned file).
Results will be available in `out/` directory and charts for top 10 players will be in `out/top10/`.

