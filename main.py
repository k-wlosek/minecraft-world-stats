from nbt import nbt
import requests
from base64 import b64decode
from json import loads


class Player:
    def __init__(self, uuid: str, filedata: nbt.NBTFile):
        self.cape = None
        self.skin = None
        self.name = None
        self.uuid = uuid
        self.__data = filedata

    def get_player_base_info(self):
        resp = requests.get(f'https://sessionserver.mojang.com/session/minecraft/profile/{self.uuid}').json()
        self.name = resp['name']
        nested = loads(b64decode(resp['properties'][0]['value']).decode(encoding='utf-8'))
        textures = nested['textures']
        self.skin = textures['SKIN']['url']
        self.cape = textures['CAPE']['url']


o = Player('fca56926-f963-442c-a634-4cef0a625a6f', None)
o.get_player_base_info()
