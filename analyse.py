import csv
import sys
import json
import matplotlib.pyplot as plt
import matplotlib.image as image
import requests
from matplotlib.offsetbox import (OffsetImage, AnnotationBbox)


def offset_image(coord: int, name: str, ax: plt.Axes, image: list):
    img = image
    im = OffsetImage(img, zoom=0.72)
    im.image.axes = ax
    ab = AnnotationBbox(im, (coord, 0),  xybox=(0., -16.), frameon=False,
                        xycoords='data',  boxcoords="offset points", pad=0)
    ax.add_artist(ab)


def plot(player_list: list[tuple], values: list, name: str, title: str, xlabel: str, ylabel: str):
    players_names = [x[0] for x in player_list]
    skins = []
    for x in player_list:
        img_data = requests.get(f'https://crafatar.com/avatars/{x[1]}?size=32').content
        with open('tmp.jpg', 'wb') as handler:
            handler.write(img_data)
        im = image.imread('tmp.jpg')
        skins.append(im)

    fig, ax = plt.subplots()
    bars = ax.bar(range(len(players_names)), values, width=0.5, align="center")
    ax.set_xticks(range(len(players_names)))
    ax.set_xticklabels(players_names)
    ax.tick_params(axis='x', which='major', pad=26)

    for i, c in enumerate(players_names):
        offset_image(i, c, ax, skins[i])

    # Axis formatting.
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
    ax.spines['bottom'].set_color('#DDDDDD')
    ax.tick_params(bottom=False, left=False)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color='#EEEEEE')
    ax.xaxis.grid(False)

    # Grab the color of the bars, so we can make the
    # text the same color.
    bar_color = bars[0].get_facecolor()

    # Add text annotations to the top of the bars.
    # Note, you'll have to adjust this slightly (the 0.3)
    # with different data.
    for bar in bars:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.3,
            round(bar.get_height(), 1),
            horizontalalignment='center',
            color=bar_color,
            weight='bold'
        )

    # fig.tight_layout()
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    ax.set_title(title)

    plt.savefig(name)


if __name__ == "__main__":
    csv.field_size_limit(sys.maxsize)

    stat_fields = ['minecraft:play_time', 'minecraft:fish_caught', 'minecraft:sprint_one_cm', 'minecraft:walk_one_cm',
                   'minecraft:crouch_one_cm', 'minecraft:sneak_time', 'minecraft:swim_one_cm',
                   'minecraft:walk_under_water_one_cm', 'minecraft:walk_on_water_one_cm', 'minecraft:aviate_one_cm']
    CSV_FILE = 'NBTTest_playerinfo.csv'

    players = []
    with open(CSV_FILE, newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for i, row in enumerate(csvreader):
            if i:
                # uuid,name,skin,cape,inventory,enderchest,stats,completed_advancements
                name, uuid, stats, completed_advancements = row[1], row[0], row[6], row[7]
                json_acceptable_string = stats.replace("'", "\"")
                stats_json = json.loads(json_acceptable_string)
                general_stats = stats_json['minecraft:custom']
                stat_values = []
                for stat in stat_fields:
                    try:
                        stat_values.append(general_stats[stat])
                    except KeyError:
                        # Player has 0 of this stat - therefore error - key does not exist
                        stat_values.append(0)
                n_of_adv = len(completed_advancements.strip('[]').split(', '))
                players.append((name, uuid, stat_values, n_of_adv))

    # Sort by x
    players_cpy = [x for x in players]
    players_cpy.sort(key=lambda x: x[3])  # Sort by n_of_adv
    players_cpy.reverse()  # Make sorting decreasing
    counts = [x[3] for x in players_cpy]
    plot(players_cpy, counts, 'advancements.png', 'Advancements', 'Players', 'Advancement count')

    # wanted_stat = 'minecraft:play_time'
    for stat in stat_fields:
        stat_name = stat.split(':')[1]
        players_cpy.sort(key=lambda x: x[2][stat_fields.index(stat)])  # Sort by wanted stat
        players_cpy.reverse()  # Make sorting decreasing
        vals = [x[2][stat_fields.index(stat)] for x in players_cpy]
        plot(players_cpy, vals, f'{stat_name}.png', stat_name, 'Players', 'Value')
