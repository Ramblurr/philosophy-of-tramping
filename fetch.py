#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
converts a blogspot blog into an ebook.

currently customized for http://www.cynicalreflections.net/
"""

import sys
import os
import urllib
from lxml import html
import md5

from urlparse import urlparse
from os.path import basename, splitext

import feedparser
from slugify import slugify
from tidylib import tidy_document, tidy_fragment

if sys.version_info[0] < 3:
    import codecs
    _open_func_bak = open  # Make a back up, just in case
    open = codecs.open

OUT_DIR = 'out'
IMAGES = 'images'

TIDY_OPTS = {
    "output-xhtml": 1,     # XHTML instead of HTML4
    "indent": 1,           # Pretty; not too much of a performance hit
    "tidy-mark": 0,        # No tidy meta tag in output
    "wrap": 0,             # No wrapping
    "alt-text": "",        # Help ensure validation
    "doctype": 'strict',   # Little sense in transitional for tool-generated markup...
    "force-output": 1,     # May not get what you expect but you will get something
 }

def download_images(source):
    page = html.fromstring(source)
    imgs = page.xpath('//img/@src')
    for img in imgs:
        m = md5.new()
        m.update(img)
        image_name, ext = splitext(basename(urlparse(img).path))
        image_name = m.hexdigest() + '-' + slugify(urllib.unquote(image_name)) + ext
        image_file = os.path.join(OUT_DIR, IMAGES, image_name)
        print("     fetching image: %s" % image_name)
        urllib.urlretrieve(img, image_file)
        source = source.replace(img, os.path.join(IMAGES, image_name))

    return source


def has_link(entry, link):
    for l in entry['links']:
        if l['href'] == link:
            return True
    return False

def fixup_links(curr_chapter, chapter):
    with open(chapter['local'], 'r+', encoding='utf-8') as f:
        content = f.read()
        content.replace(curr_chapter['link'], curr_chapter['slug'])
        f.seek(0)
        f.write(content)
        f.truncate()

def wrap_html(curr_chapter):
    with open(curr_chapter['local'], 'r+', encoding='utf-8') as f:
        content = f.read()
        header = """<?xml version='1.0' encoding='utf-8'?>
            <html xmlns="http://www.w3.org/1999/xhtml">
            <head><title>%s</title></head>
            <body><h1 class="chapter">%s</h1>""" % (curr_chapter['title'],
                                    curr_chapter['title'])
        footer = "</body></html>"
        doc = "%s%s%s" % (header, content, footer)
        clean = tidy_document(doc, options=TIDY_OPTS)
        f.seek(0)
        f.write(clean[0])
        f.truncate()

def main():
    if len(sys.argv) != 2:
        print("usage: %s <list of urls.txt>" % (sys.argv[0]))
        sys.exit(1)

# read list of chapters
    with open(sys.argv[1], mode ='r', encoding='utf-8') as f:
        chapters = f.readlines()

# fetch feed
    rssurl = "http://www.cynicalreflections.net/feeds/posts/default?max-results=99"
    feed = feedparser.parse(rssurl)

    print("=====\nFound %s entries" % (len(feed['entries'])))

    chapter_list = list()

# fetch all chapters
    for entry in feed['entries']:
        for index, chapter_link in enumerate(chapters):
            chapter_link = chapter_link.strip()
            if not has_link(entry, chapter_link):
                continue
# munge title
            title = entry['title']
            title = title.replace(u"A Philosophy of Tramping—", "")
            title = title.replace(u"A Philosophy of Tramping —", "").strip()
            slug = slugify(title)
            print("+ parsing chapter %s" % (chapter_link))

            content = entry['content'][0]['value']
            content = tidy_fragment(content, options=TIDY_OPTS)[0]
            content = download_images(content)

            filename = os.path.join(OUT_DIR, "%s-%s.xhtml" % (index, slug))
            chapter_list.append({'index': index, 'link': chapter_link,
                                 'slug': slug, 'local': filename, 'title': title})

            with open(filename, 'w+', encoding='utf-8') as f:
                f.write(content)

# sort posts
    chapter_list = sorted(chapter_list, key=lambda k: k['index'])

# fix up internal links
    for curr_chapter in chapter_list:
        for chapter in chapter_list:
            fixup_links(curr_chapter, chapter)

# wrap html
    for curr_chapter in chapter_list:
        wrap_html(curr_chapter)

# create toc
    toc_entries = list()
    for chapter in chapter_list:
        toc_entries.append('<li style="margin: 1em 0;"><a href="%s">%s</a></li>'
                           % (os.path.basename(chapter['local']),
                              chapter['title']))

    toc_template = """<h1 id="toc">A Philosophy of Tramping</h1>
                        <h2>Ian Cutler</h2>
                        <p>Compiled from http://www.cynicalreflections.net</p>
            <ul style='list-style: none; text-ident:0em; page-break-after:always;'>
                    %s
                    </ul>
                    """ % ('\n'.join(toc_entries))

    toc_content = tidy_document(toc_template, options=TIDY_OPTS)[0]

    with open(os.path.join(OUT_DIR, 'toc.html'), 'w') as f:
        f.write(toc_content)

    print("===== Done =====")
    print("Fetched and processed %s chapters" % (len(chapter_list)))
    for chapter in chapter_list:
        print("    * %s " % (chapter['title']))

if __name__ == '__main__':
    main()
