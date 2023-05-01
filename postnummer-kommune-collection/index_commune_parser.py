from html.parser import HTMLParser


class PostnummerKommunePair:
    def __init__(self, postnummer, kommune):
        self.postnummer = postnummer
        self.kommune = kommune

    def to_dict(self):
        return {
            'postnummer': self.postnummer,
            'kommune': self.kommune
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

    def to_json_list(self):
        return list(map(lambda t: t.to_dict(), self.postnummer_kommunes))

import requests
import json
import sys
from random import randint
from time import sleep

test = False
for arg in sys.argv:
    if arg == 'test':
        test = True

all_lan_links = [
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

parser = PostnummerCommuneParser()

for link in all_lan_links:
    response = requests.get(link)
    parser.feed(response.text)
    sleep(randint(1, 3))

json_list = parser.to_json_list()
if test:
    json_str = json.dumps(json_list, indent=2, sort_keys=True, default=str)
    file_name = 'postnummer_kommune_test.json'
else:
    json_str = json.dumps(json_list, sort_keys=True, default=str)
    file_name = 'postnummer_kommune.json'
f = open(file_name, "w")
f.write(json_str)
f.close()
