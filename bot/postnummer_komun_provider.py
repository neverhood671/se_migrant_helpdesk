import json
from typing import Optional

KOMMUNERS_FILE = 'kommunes.json'

class KommuneInfo:
    def __init__(
            self,
            name: str,
            kommun_link: str,
            vuxenutbildningar_link: Optional[str],
            postnummers: list[str]
    ):
        if name is None:
            raise Exception('Kommun name is none')
        if kommun_link is None:
            raise Exception(f'Kommun link is none for Kommun {name}')
        self.name = name
        self.kommun_link = kommun_link
        self.vuxenutbildningar_link = vuxenutbildningar_link
        self.postnummers = postnummers

    @staticmethod
    def from_json(json_dict):
        return KommuneInfo(
            name=json_dict['name'],
            kommun_link=json_dict['kommun_link'],
            vuxenutbildningar_link=json_dict['vuxenutbildningar_link'],
            postnummers=json_dict['postnummers'],
        )

class PostnummerKomunProvider:
    def __init__(self):
        self.kommunes_ny_name: dict[str, KommuneInfo] = dict()
        self.ponstnum_by_kommun: dict[str, KommuneInfo] = dict()

        with open(KOMMUNERS_FILE, 'r') as f:
            postnummer_kommunes_json: list = json.load(f)

        for komun_json in postnummer_kommunes_json:
            komun = KommuneInfo.from_json(komun_json)
            self.kommunes_ny_name[komun.name] = komun
            for pn in komun.postnummers:
                self.ponstnum_by_kommun[pn] = komun

    def get_kommun_info_by_number(self, postnum: str) -> Optional[KommuneInfo]:
        return self.ponstnum_by_kommun.get(postnum)

POSTNUMMER_KOMUN_PROVIDER = PostnummerKomunProvider()