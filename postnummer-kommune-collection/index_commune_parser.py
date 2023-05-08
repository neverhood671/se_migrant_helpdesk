import json
import os
import re
from html.parser import HTMLParser
from random import randint
from time import sleep
from typing import Optional

import requests

POSTNUMMER_KOMMUNE_FILE = 'postnummer_kommune.json'
KOMMUNER_LINKS_FILE = 'kommunerlista.json'
KOMMUNER_VUXENUTBILDNINGAR_FILE = 'lankar-till-vuxenutbildningar-i-sveriges-kommuner.json'

ALL_LAN_WORLDPOSTALCODES_LINKS = [
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-blekinge-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-dalarnas-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-gavleborgs-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-gotlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-hallands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-jamtlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-jonkopings-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-kalmar-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-kronobergs-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-norrbottens-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-orebro-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-ostergotlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-skane-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-sodermanlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-stockholms-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-uppsala-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-varmlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-vasterbottens-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-vasternorrlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-vastmanlands-lan",
    "https://www.worldpostalcodes.org/l1/se/se/sverige/lista/r1/lista-over-postnummer-i-vastra-gotalands-lan",
]


class PostnummerKommunePair:
    def __init__(self, postnummer: str, kommune: str):
        self.postnummer: str = postnummer
        self.kommune: str = kommune

    def to_dict(self):
        return {
            'postnummer': self.postnummer,
            'kommune': self.kommune
        }

    def get_formatted_kommun(self):
        if self.kommune == 'Falu kommun':
            return 'Falun'
        elif self.kommune == 'Göteborgs Stad':
            return 'Göteborg'
        else:
            formatted_kommune = re.sub(r's? kommun', '', self.kommune)
            if formatted_kommune in [
                'Hagfor', 'Tranå', 'Alingså', 'Vännä', 'Storfor', 'Torså', 'Sotenä', 'Borå', 'Munkfor', 'Västerå',
                'Göteborgs Stad', 'Strängnä', 'Bollnä', 'Hällefor', 'Kramfor', 'Degerfor', 'Höganä', 'Hofor', 'Grum',
                'Robertsfor', 'Bengtsfor', 'Mönsterå'
            ]:
                return formatted_kommune + 's'
            else:
                return formatted_kommune

    @staticmethod
    def from_json(json_dict):
        return PostnummerKommunePair(
            postnummer=json_dict['postnummer'],
            kommune=json_dict['kommune'],
        )


class KommuneInfo:
    def __init__(
            self,
            name: str,
            kommun_link: str,
            vuxenutbildningar_link: Optional[str],
            postnummers: list[str]
    ):
        if name is None:
            raise Exception('Kommun is none')
        if kommun_link is None:
            raise Exception(f'Kommun link is none for Kommun {name}')
        self.name = name
        self.kommun_link = kommun_link
        self.vuxenutbildningar_link = vuxenutbildningar_link
        self.postnummers = postnummers

    def to_dict(self):
        return {
            'name': self.name,
            'kommun_link': self.kommun_link,
            'vuxenutbildningar_link': self.vuxenutbildningar_link,
            'postnummers': self.postnummers,
        }


class PostnummerCommuneParser(HTMLParser):

    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
        self.tr_tag = False
        self.td_tag = False
        self.a_tag = False
        self.td_num = 0
        self.postnummer_kommunes: list[PostnummerKommunePair] = list()
        self.current_postnum = '0'

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.tr_tag = True
        elif tag == "td" and self.tr_tag:
            self.td_tag = True
            self.td_num += 1
        elif tag == "a":
            self.a_tag = True

    def handle_endtag(self, tag):
        if tag == "tr":
            self.tr_tag = False
            self.td_num = 0
        elif tag == "td" and self.tr_tag:
            self.td_tag = False
        elif tag == "a":
            self.a_tag = False

    def handle_data(self, data):
        if self.tr_tag and self.a_tag:
            if self.td_num == 1:
                self.current_postnum = data.replace(" ", "").strip()
            elif self.td_num == 3:
                self.postnummer_kommunes.append(
                    PostnummerKommunePair(self.current_postnum, data)
                )


def to_json_list(postnummer_kommunes: list[PostnummerKommunePair]):
    return list(map(lambda t: t.to_dict(), postnummer_kommunes))


def to_json_dict_num_kommun(postnummer_kommunes: list[PostnummerKommunePair]):
    json_dict = dict()
    for pair in postnummer_kommunes:
        json_dict[pair.postnummer] = pair.kommune
    return json_dict


def collect_kommune_infos(
        postnummer_kommunes: list[PostnummerKommunePair],
        kommuner_links: dict[str, str],
        kommunes_vuxenutbildningar: dict[str, str]
):
    kommune_infos = list()
    kommune_infos_dict = dict()
    for pk in postnummer_kommunes:
        kommune_name = pk.get_formatted_kommun()
        kommune = kommune_infos_dict.get(kommune_name)
        if kommune is None:
            kommune = KommuneInfo(
                name=kommune_name,
                kommun_link=kommuner_links.get(kommune_name),
                vuxenutbildningar_link=kommunes_vuxenutbildningar.get(kommune_name),
                postnummers=list()
            )
            kommune_infos.append(kommune)
            kommune_infos_dict[kommune_name] = kommune
        kommune.postnummers.append(pk.postnummer)
    return kommune_infos


def to_json_kommun_list(kommune_infos: list[KommuneInfo]):
    json_list = list()
    for kommun in kommune_infos:
        json_list.append(kommun.to_dict())
    return json_list


def read_and_save_from_worldpostalcodes():
    parser = PostnummerCommuneParser()

    for link in ALL_LAN_WORLDPOSTALCODES_LINKS:
        response = requests.get(link)
        parser.feed(response.text)
        sleep(randint(1, 3))

    json_str = json.dumps(json_list, sort_keys=True, default=str)
    save_to_file(POSTNUMMER_KOMMUNE_FILE, json_str)


def load_from_file() -> list[PostnummerKommunePair]:
    with open(POSTNUMMER_KOMMUNE_FILE, 'r') as f:
        postnummer_kommunes_json = json.load(f)
        return list(map(lambda t: PostnummerKommunePair.from_json(t), postnummer_kommunes_json))


def save_to_file(file_name: str, data: str):
    f = open(file_name, "w")
    f.write(data)
    f.close()


if not os.path.isfile(POSTNUMMER_KOMMUNE_FILE):
    read_and_save_from_worldpostalcodes()

postnummer_kommunes: list[PostnummerKommunePair] = load_from_file()

kommuner_links = dict()
with open(KOMMUNER_LINKS_FILE, 'r') as f:
    kommuner_links: dict[str, str] = json.load(f)

kommunes_vuxenutbildningar = dict()
with open(KOMMUNER_VUXENUTBILDNINGAR_FILE, 'r') as f:
    kommunes_vuxenutbildningar: dict[str, str] = json.load(f)

# check kommunes_vuxenutbildningar
undefined_kommun = set()
for k in kommunes_vuxenutbildningar.keys():
    if k not in kommuner_links.keys():
        undefined_kommun.add(k)

if len(undefined_kommun) > 0:
    raise Exception(f'Undefined kommun in kommunes_vuxenutbildningar: {undefined_kommun}')

# check postnummer_kommunes
undefined_kommun = set()
for pk in postnummer_kommunes:
    k = pk.get_formatted_kommun()
    if k not in kommuner_links.keys():
        undefined_kommun.add(k)

if len(undefined_kommun) > 0:
    raise Exception(f'Undefined kommun in postnummer_kommunes: {undefined_kommun}')

json_list = to_json_list(postnummer_kommunes)
save_to_file(
    'postnummer_kommune_pretty.json',
    json.dumps(json_list, indent=2, sort_keys=True, default=str)
)

kommune_infos = collect_kommune_infos(
    postnummer_kommunes=postnummer_kommunes,
    kommuner_links=kommuner_links,
    kommunes_vuxenutbildningar=kommunes_vuxenutbildningar
)
json_list = to_json_kommun_list(kommune_infos)
save_to_file(
    'kommunes.json',
    json.dumps(json_list, sort_keys=True, default=str)
)
save_to_file(
    'kommunes_pretty.json',
    json.dumps(json_list, indent=2, sort_keys=True, default=str)
)
