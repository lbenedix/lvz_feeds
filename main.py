from functools import lru_cache
from typing import Tuple

import minify_html

import requests
from feedgen.entry import FeedEntry
from feedparser import FeedParserDict
from readability import Document
from bs4 import BeautifulSoup as bs, Tag
import feedparser
from feedgen.feed import FeedGenerator
from tinydb import TinyDB, Query

feeds = [
    "http://www.lvz.de/rss/feed/lvz_leipzig",
    "http://www.lvz.de/rss/feed/lvz_region",
    "http://www.lvz.de/rss/feed/lvz_kultur",
]


def get_tag_html(tag: Tag):
    return "".join([i.decode() if type(i) is Tag else i for i in tag.contents])


@lru_cache
def get_summary(url: str) -> Tuple[str, str]:
    response = requests.get(url)

    try:
        soup = bs(response.text, "html.parser")
        plus_close = "pdb-parts-paidcontent-freeuntilbadge_close"
        plus_open = "pdb-parts-paidcontent-freeuntilbadge_open"

        prefix = "free"
        if len(soup.findAll("span", {"class": plus_open})) > 0:
            prefix = "+ open"
        elif len(soup.findAll("span", {"class": plus_close})) > 0:
            prefix = "+ closed"

        print(prefix, url)

        doc = Document(response.text)
        soup = bs(doc.summary(), "html.parser")
        summary = get_tag_html(soup.find(name="div", attrs={"class": "pdb-richtext-field"}))
        return prefix, minify_html.minify(summary)
    except:
        return prefix, ""


def setup_feed(source_feed, url) -> FeedGenerator:
    fg = FeedGenerator()
    fg.id(url)
    fg.title(source_feed.feed.title)
    fg.author(source_feed.feed.authors[0])
    fg.link(href=source_feed.feed.link, rel='alternate')
    fg.logo('https://www.lvz.de/bundles/molasset/images/sites/desktop/lvz/apple-touch-icon.png')
    fg.subtitle(source_feed.feed.subtitle)
    fg.link(href=url, rel='self')
    fg.language(source_feed.feed.language)
    fg.updated(source_feed.updated)

    return fg


def to_fe(item: dict) -> FeedEntry:
    fe = FeedEntry()
    fe.id(item['guid'])
    fe.title(item['title'])
    fe.link(href=item['link'])
    fe.summary(item['summary'])
    fe.author(item['author'])
    fe.published(item['published'])
    return fe


def get_items(source_feed: FeedParserDict, db: TinyDB):
    print('📖 getting all items', source_feed.href)

    for entry in source_feed.entries:
        Item = Query()
        if len(db.search(Item.guid == entry.guid)) > 0:
            print('skip')
            continue

        prefix, summary = get_summary(entry.link)

        if prefix == '+ closed':
            print('skip paywall')
            continue

        title = f'{prefix} - {entry.title}'

        item = {
            "guid": entry.guid,
            "title": title,
            "link": entry.link,
            "summary": summary,
            "author": entry.authors[0],
            "published": entry.published,
            "status": prefix,
        }
        db.insert(item)


def generate_feed(source_feed: FeedParserDict, db: TinyDB):
    print('📝 generating feed', source_feed.href)

    fg = setup_feed(source_feed, source_feed.href)

    for item in db.all():
        fg.add_entry(to_fe(item))

    fg.atom_file(f"{feed_id}_atom.xml")


if __name__ == '__main__':

    for feed_url in feeds:
        print(feed_url)

        feed_id = feed_url.split('/')[-1]
        db = TinyDB(f'{feed_id}.json')
        source_feed = feedparser.parse(feed_url)

        get_items(source_feed, db)
        generate_feed(source_feed, db)
