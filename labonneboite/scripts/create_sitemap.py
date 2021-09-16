from datetime import datetime
import operator
import os

from flask import Flask, render_template
# FIXME drop deprecated flask-script
# see https://flask-script.readthedocs.io/en/latest/
from flask_script import Manager
from slugify import slugify

from labonneboite.common import geocoding
from labonneboite.conf import settings

# max URLs in a sitemap
# See https://en.wikipedia.org/wiki/Sitemaps#Sitemap_limits
MAX_URLS = 50000

app = Flask(__name__)

manager = Manager(app)

@manager.command
def sitemap():
    """
    To rebuild the sitemap,
    simply run "make create_sitemap" and then commit the new sitemap.xml file.
    Currently you don't need to run it more than once as its content is pretty much static.
    """
    pages = []
    now_str = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

    cities = [city for city in geocoding.get_cities() if city['zipcode'].endswith('00')]
    top_cities = [
        (city['slug'], city['zipcode'])
        for city in sorted(cities, key=operator.itemgetter('population'), reverse=True)[:94]
    ]

    rome_descriptions = list(settings.ROME_DESCRIPTIONS.values())

    for rome in rome_descriptions:
        occupation = slugify(rome)
        for city, zipcode in top_cities:
            url = "https://labonneboite.pole-emploi.fr/entreprises/%s-%s/%s" % (city, zipcode, occupation)
            pages.append((url, now_str))

    # Handle max URLs in a sitemap
    # See https://en.wikipedia.org/wiki/Sitemaps#Sitemap_limits
    initialCount = len(pages)
    if initialCount > MAX_URLS:
        lineStart = '\n * SKIPPED: '
        print('Warning: sitemap should have at most 50K URLs\nDrop these URLs, they will not be indexed in sitemap.xml', lineStart, lineStart.join(map(lambda p: p[0], pages[50000:])))
        pages = pages[:MAX_URLS]

    # Write the sitemap to file
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    sitemap_filename = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../web/static/sitemap.xml")
    with open(sitemap_filename, "w") as f:
        f.write(sitemap_xml)

    # Print summary
    print("Generated sitemap.xml using %s pages. Dropped %s pages\nTotal: %s cities x %s rome_descriptions = %s pages" % (
        len(pages),
        initialCount - len(pages),
        len(top_cities),
        len(rome_descriptions),
        initialCount,
    ))

if __name__ == "__main__":
    manager.run()
