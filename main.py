import json
from const import *
from nbt import nbt
import requests
from base64 import b64decode
from json import loads
import os
import csv
import logging


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
        try:
            self.__data = nbt.NBTFile(self.file, 'rb')
        except nbt.MalformedFileError:
            logging.debug(f"Malformed NBT file for {self.uuid}, no data will be saved")
            self.__data = None  # Failed to read NBT file

    def get_player_base_info(self) -> bool:
        resp = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid[:36]}').json()
        # Cut off trailing numbers from UUID to make it valid
        if 'errorMessage' in resp:
            # API returned an error, such as invalid UUID
            return False
        self.name = resp['name']
        nested = loads(b64decode(resp['properties'][0]['value']).decode(encoding='utf-8'))
        textures = nested['textures']
        self.skin = textures['SKIN']['url']
        try:
            self.cape = textures['CAPE']['url']
        except KeyError:
            logging.debug(f"Player {self.name} has no cape, skipping")
        return True

    def read_containers(self):
        """
        Reads player-tied containers, such as Inventory and Enderchest
        Both are saved as class properties in format [(item, count), (item, count)]
        """
        if self.__data:
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
        try:
            # Climb up directory tree
            with open(os.path.join(head.replace('playerdata', 'stats'), tail.replace('.dat', '.json')), 'r') as j:
                self.__data = json.load(j)
        except FileNotFoundError:
            self.__data = None  # No stats found for UUID
            logging.debug(f'No stats for {self.name}, uuid: {self.uuid}')

    def get_stats(self):
        if self.__data:
            # All stats as dict, ex. game_time is in ['minecraft:custom']['minecraft:total_world_time']
            self.stats = self.__data['stats']


class PlayerAdvancements(Player):
    def __init__(self, uuid: str, filename: str):
        super().__init__(uuid, filename)
        self.completed: list[str] = []
        self.read_json()

    def read_json(self):
        head, tail = os.path.split(self.file)
        try:
            with open(os.path.join(head.replace('playerdata', 'advancements'), tail.replace('.dat', '.json')),
                      'r') as j:
                self.__data = json.load(j)
        except FileNotFoundError:
            self.__data = None  # Not found, no advancements probably
            logging.debug(f'No advancements for {self.name}, uuid: {self.uuid}')

    def get_advancements(self):
        if self.__data:
            for advancement, value in self.__data.items():
                try:
                    if value['done']:
                        self.completed.append(advancement)
                except TypeError:
                    # Last field is int - version of file - ignore
                    pass


if __name__ == "__main__":
    world_name = PLAYERDATA_DIR.split('/')[0] or PLAYERDATA_DIR.split('\\')[0]
    logging.info(f'Output to {world_name}_playerinfo.csv')

    # ChatGPT actually helped on this one, (the well documented portion) after 20min of back and forth
    files = [f for f in os.listdir(PLAYERDATA_DIR) if f.endswith('.dat') and not f.endswith('_old.dat')]
    players = []

    for file in files:
        if '-' in file:
            base_name, ext = os.path.splitext(file)
            uuid, nums = base_name.rsplit('-', 1)
            try:
                nums = int(nums)
                base_file = f"{uuid}.dat"
                if base_file not in files:
                    continue
                base_path = os.path.join(PLAYERDATA_DIR, base_file)
                nums_path = os.path.join(PLAYERDATA_DIR, file)
                if os.path.getsize(base_path) > os.path.getsize(nums_path):
                    players.append(base_file)
                else:
                    players.append(file)
                    files.remove(base_file)
            except ValueError:
                players.append(file)
        else:
            players.append(file)

    # Remove duplicates
    players = list(set(players))

    # Add files with numbers if they have a larger size
    for file in files:
        if '-' in file:
            base_name, ext = os.path.splitext(file)
            uuid, nums = base_name.rsplit('-', 1)
            try:
                nums = int(nums)
                base_file = f"{uuid}.dat"
                if base_file in players:
                    continue
                base_path = os.path.join(PLAYERDATA_DIR, base_file)
                nums_path = os.path.join(PLAYERDATA_DIR, file)
                if os.path.getsize(nums_path) > os.path.getsize(base_path):
                    players.append(file)
            except ValueError:
                pass

    with open(f'{world_name}_playerinfo.csv', 'w', newline='') as csvfile:
        csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        # Write first row (col names)
        csvwriter.writerow(
            ['uuid', 'name', 'skin', 'cape', 'inventory', 'enderchest', 'stats', 'completed_advancements'])
        for file in players:
            uuid: str = file.replace('.dat', '')
            adv: PlayerAdvancements = PlayerAdvancements(uuid, PLAYERDATA_DIR + file)
            success: bool = adv.get_player_base_info()
            if not success:  # Do not write invalid uuids
                logging.debug(f"Reading for {adv.name} failed, problematic UUID: {file.replace('.dat', '')}")
                continue
            logging.info(f'Reading info for {adv.name}')
            adv.read_containers()
            adv.get_advancements()
            st: PlayerStats = PlayerStats(uuid, PLAYERDATA_DIR + file)
            st.get_stats()

            csvwriter.writerow([adv.uuid, adv.name, adv.skin, adv.cape,
                                adv.inventory, adv.enderchest, st.stats, adv.completed])
