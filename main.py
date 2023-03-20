import json

from nbt import nbt
import requests
from base64 import b64decode
from json import loads
import os


class Player:
    def __init__(self, uuid: str, filename: str):
        self.__data = None
        self.enderchest = None
        self.inventory = None
        self.cape = None
        self.skin = None
        self.name = None
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
        self.inventory = []
        for slot in [x.tags for x in self.__data['Inventory']]:
            self.inventory.append((slot[1], slot[2].value))
        self.enderchest = []
        for slot in [x.tags for x in self.__data['EnderItems']]:
            self.enderchest.append((slot[1], slot[2].value))


class PlayerStats(Player):
    def __init__(self, uuid: str, filename: str):
        super().__init__(uuid, filename)
        self.read_json()

    def read_json(self):
        head, tail = os.path.split(self.file)
        with open(os.path.join(head.replace('playerdata', 'stats'), tail.replace('.dat', '.json')), 'r') as j:
            self.__data = json.load(j)

    def get_stats(self):
        self.stats = self.__data['stats']


class PlayerAdvancements(Player):
    def __init__(self, uuid: str, filename: str):
        super().__init__(uuid, filename)
        self.read_json()

    def read_json(self):
        head, tail = os.path.split(self.file)
        with open(os.path.join(head.replace('playerdata', 'advancements'), tail.replace('.dat', '.json')), 'r') as j:
            self.__data = json.load(j)

    def get_advancements(self):
        # print(self.__data)
        self.completed = []
        for advancement, value in self.__data.items():
            try:
                if value['done']:
                    self.completed.append(advancement)
            except TypeError:
                # Last field is int - version of file - ignore
                pass


o = PlayerAdvancements('fca56926-f963-442c-a634-4cef0a625a6f', "NBTTest/playerdata/fca56926-f963-442c-a634"
                                                               "-4cef0a625a6f.dat")
o.read_nbt()
o.read_containers()
o.get_advancements()
p = PlayerStats('fca56926-f963-442c-a634-4cef0a625a6f', "NBTTest/playerdata/fca56926-f963-442c-a634-4cef0a625a6f.dat")
p.get_stats()

