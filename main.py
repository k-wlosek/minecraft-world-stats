import json
from nbt import nbt
import requests
from base64 import b64decode
from json import loads
import os
import csv


class Player:
    def __init__(self, uuid: str, filename: str):
        # Initialize class fields
        self.__data: nbt.NBTFile = None
        self.enderchest: list[tuple] = []
        self.inventory: list[tuple] = []
        self.cape: str = ''
        self.skin: str = ''
        self.name: str = ''
        self.uuid = uuid
        self.file = filename
        self.read_nbt()  # Populate private members

    def read_nbt(self):
        self.__data = nbt.NBTFile(self.file, 'rb')

    def get_player_base_info(self):
        resp = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid}').json()
        self.name = resp['name']
        nested = loads(b64decode(resp['properties'][0]['value']).decode(encoding='utf-8'))
        textures = nested['textures']
        self.skin = textures['SKIN']['url']
        self.cape = textures['CAPE']['url']

    def read_containers(self):
        """
        Reads player-tied containers, such as Inventory and Enderchest
        Both are saved as class properties in format [(item, count), (item, count)]
        """
        for slot in [x.tags for x in self.__data['Inventory']]:
            self.inventory.append((slot[1], slot[2].value))
        self.enderchest = []
        for slot in [x.tags for x in self.__data['EnderItems']]:
            self.enderchest.append((slot[1], slot[2].value))


class PlayerStats(Player):
    def __init__(self, uuid: str, filename: str):
        super().__init__(uuid, filename)
        self.stats: dict[str] = {}
        self.read_json()

    def read_json(self):
        head, tail = os.path.split(self.file)
        # Climb up directory tree
        with open(os.path.join(head.replace('playerdata', 'stats'), tail.replace('.dat', '.json')), 'r') as j:
            self.__data = json.load(j)

    def get_stats(self):
        # All stats as dict, ex. game_time is in ['minecraft:custom']['minecraft:total_world_time']
        self.stats = self.__data['stats']


class PlayerAdvancements(Player):
    def __init__(self, uuid: str, filename: str):
        super().__init__(uuid, filename)
        self.completed: list[str] = []
        self.read_json()

    def read_json(self):
        head, tail = os.path.split(self.file)
        with open(os.path.join(head.replace('playerdata', 'advancements'), tail.replace('.dat', '.json')), 'r') as j:
            self.__data = json.load(j)

    def get_advancements(self):
        for advancement, value in self.__data.items():
            try:
                if value['done']:
                    self.completed.append(advancement)
            except TypeError:
                # Last field is int - version of file - ignore
                pass


if __name__ == "__main__":
    PLAYERDATA_DIR = 'NBTTest/playerdata/'
    world_name = PLAYERDATA_DIR.split('/')[0] or PLAYERDATA_DIR.split('\\')[0]

    with open(f'{world_name}_playerinfo.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Write first row (col names)
        csvwriter.writerow(['uuid', 'name', 'skin', 'cape', 'inventory', 'enderchest', 'stats', 'completed_advancements'])
        for file in os.listdir(PLAYERDATA_DIR):
            if file.endswith('.dat'):  # Possible backups in form of .dat_old, dismiss them
                adv: PlayerAdvancements = PlayerAdvancements(file.replace('.dat', ''), PLAYERDATA_DIR + file)
                adv.get_player_base_info()
                adv.read_containers()
                adv.get_advancements()
                st: PlayerStats = PlayerStats(file.replace('.dat', ''), PLAYERDATA_DIR + file)
                st.get_stats()

                csvwriter.writerow([adv.uuid, adv.name, adv.skin, adv.cape,
                                    adv.inventory, adv.enderchest, st.stats, adv.completed])
