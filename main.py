from functools import lru_cache
from typing import Tuple

import minify_html

import requests
from feedparser import FeedParserDict
from readability import Document
from bs4 import BeautifulSoup as bs, Tag
import feedparser
from feedgen.feed import FeedGenerator

url = "http://www.lvz.de/rss/feed/lvz_region"
source_feed = feedparser.parse(url)


def get_tag_html(tag: Tag):
    return "".join([i.decode() if type(i) is Tag else i for i in tag.contents])


@lru_cache
def get_summary(url: str) -> Tuple[bool, str]:
    response = requests.get(url)

    soup = bs(response.text, "html.parser")
    is_plus_content = (
            "Kostenlos bis"
            in soup.find(
        name="span", attrs={"class": "pdb-parts-paidcontent-freeuntilbadge"}
    ).text
    )

    if is_plus_content:
        print("💸")

    doc = Document(response.text)
    soup = bs(doc.summary(), "html.parser")
    summary = get_tag_html(soup.find(name="div", attrs={"class": "pdb-richtext-field"}))
    return is_plus_content, minify_html.minify(summary)


# <item>
#     <title>Unbekannte schmieren in Roßwein gegen die Polizei</title>
#     <link>http://www.lvz.de/Region/Unbekannte-schmieren-in-Rosswein-gegen-die-Polizei</link>
#     <description>&lt;p class="pda-textparagraph"&gt;Unbekannte Täter verunstalteten die Fassade eines ehemaligen
#         Schulkomplexes in Roßwein. Der Sachschaden beträgt etwa 10 000 Euro. Warum es sich dabei auch um eine Attacke
#         gegen die Polizei handelt.&lt;/p&gt;&lt;p class="pda-textparagraph"&gt;&lt;!-- Methode uuid:
#         "f292ad36-c484-11ec-825e-f5cc19365745"--&gt;&lt;/p&gt;
#     </description>
#     <author>mol-lvz@madsack.de (LVZ Methode)</author>
#     <guid isPermaLink="false">f292ad36-c484-11ec-825e-f5cc19365745</guid>
#     <pubDate>Mon, 25 Apr 2022 11:07:33 +0000</pubDate>
# </item>

# {'title': 'Unbekannte schmieren in Roßwein gegen die Polizei',
#  'title_detail': {'type': 'text/plain', 'language': 'de-DE', 'base': 'https://www.lvz.de/rss/feed/lvz_region',
#                   'value': 'Unbekannte schmieren in Roßwein gegen die Polizei'}, 'links': [
#     {'rel': 'alternate', 'type': 'text/html',
#      'href': 'http://www.lvz.de/Region/Unbekannte-schmieren-in-Rosswein-gegen-die-Polizei'}],
#  'link': 'http://www.lvz.de/Region/Unbekannte-schmieren-in-Rosswein-gegen-die-Polizei',
#  'summary': '<p class="pda-textparagraph">Unbekannte Täter verunstalteten die Fassade eines ehemaligen Schulkomplexes in Roßwein. Der Sachschaden beträgt etwa 10 000 Euro. Warum es sich dabei auch um eine Attacke gegen die Polizei handelt.</p><p class="pda-textparagraph"><!-- Methode uuid: "f292ad36-c484-11ec-825e-f5cc19365745"--></p>',
#  'summary_detail': {'type': 'text/html', 'language': 'de-DE', 'base': 'https://www.lvz.de/rss/feed/lvz_region',
#                     'value': '<p class="pda-textparagraph">Unbekannte Täter verunstalteten die Fassade eines ehemaligen Schulkomplexes in Roßwein. Der Sachschaden beträgt etwa 10 000 Euro. Warum es sich dabei auch um eine Attacke gegen die Polizei handelt.</p><p class="pda-textparagraph"><!-- Methode uuid: "f292ad36-c484-11ec-825e-f5cc19365745"--></p>'},
#  'authors': [{'name': 'LVZ Methode', 'email': 'mol-lvz@madsack.de'}], 'author': 'mol-lvz@madsack.de (LVZ Methode)',
#  'author_detail': {'name': 'LVZ Methode', 'email': 'mol-lvz@madsack.de'}, 'id': 'f292ad36-c484-11ec-825e-f5cc19365745',
#  'guidislink': False, 'published': 'Mon, 25 Apr 2022 11:07:33 +0000',
#  'published_parsed': time.struct_time(tm_year=2022, tm_mon=4, tm_mday=25, tm_hour=11, tm_min=7, tm_sec=33, tm_wday=0,
#                                       tm_yday=115, tm_isdst=0)}

from feedgen.feed import FeedGenerator

fg = FeedGenerator()
fg.id(url)
fg.title(source_feed.feed.title)
fg.author(source_feed.feed.authors[0])
fg.link(href=source_feed.feed.link, rel='alternate')
fg.logo('https://www.lvz.de/bundles/molasset/images/sites/desktop/lvz/apple-touch-icon.png')
fg.subtitle(source_feed.feed.subtitle)
fg.link(href=url, rel='self')
fg.language(source_feed.feed.language)

for entry in source_feed.entries:
    is_premium, summary = get_summary(entry.link)
    title = entry.title if not is_premium else f'💸 - {entry.title}'

    fe = fg.add_entry()
    fe.id(entry.guid)
    fe.title(title)
    fe.link(href=entry.link)
    fe.summary(summary)
    fe.author(entry.authors[0])
    print(fe)

fg.atom_file('atom.xml')
