import csv
import sys
import json

csv.field_size_limit(sys.maxsize)

stat_fields = ['minecraft:play_time', 'minecraft:fish_caught', 'minecraft:sprint_one_cm', 'minecraft:walk_one_cm',
               'minecraft:crouch_one_cm', 'minecraft:sneak_time', 'minecraft:swim_one_cm', 'minecraft:walk_under_water_one_cm',
               'minecraft:walk_on_water_one_cm', 'minecraft:aviate_one_cm']

players = []
with open('out.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
    for i, row in enumerate(csvreader):
        if i:
            # uuid,name,skin,cape,inventory,enderchest,stats,completed_advancements
            name, stats, completed_advancements = row[1], row[6], row[7]
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
            players.append((name, stat_values, n_of_adv))
# print(players)

players_cpy = [x for x in players]
players_cpy.sort(key=lambda x: x[2])  # Sort by n_of_adv
players_cpy.reverse()  # Make sorting decreasing
print(players_cpy)  # List sorted by number of advancements

wanted_stat = 'minecraft:play_time'
players_cpy.sort(key=lambda x: x[1][stat_fields.index(wanted_stat)])  # Sort by wanted stat
players_cpy.reverse()  # Make sorting decreasing
print(players_cpy)  # List sorted by play time


