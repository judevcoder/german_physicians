import os

from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings

from baden import BadenSpider
from bayern import BayernSpider
from berlin import BerlinSpider
from brandenburg import BrandenburgSpider
from bremen import BremenSpider
from hamburg import HamburgSpider

configure_logging()
settings = get_project_settings()
runner = CrawlerRunner(settings)


def run_spider():
    runner.crawl(BadenSpider)
    runner.crawl(BayernSpider)
    runner.crawl(BerlinSpider)
    runner.crawl(BrandenburgSpider)
    runner.crawl(BremenSpider)
    runner.crawl(HamburgSpider)
    d = runner.join()
    d.addBoth(lambda _: reactor.stop())
    try:
        reactor.run()
    except:
        pass

run_spider()

output_path = os.path.dirname(os.path.abspath(__file__)).replace('physicians/physicians/spiders', '') + 'OUTPUT/'
spider_name_list = ['baden', 'bayern', 'berlin', 'brandenburg', 'bremen', 'hamburg']
for name in spider_name_list:
    temp_physician_path = output_path + name + '/temp_physicians.csv'
    if os.path.isfile(temp_physician_path):
        os.remove(temp_physician_path)

    temp_specialities_path = output_path + name + '/temp_specialities.csv'
    if os.path.isfile(temp_specialities_path):
        os.remove(temp_specialities_path)

    temp_locations_path = output_path + name + '/temp_locations.csv'
    if os.path.isfile(temp_locations_path):
        os.remove(temp_locations_path)

print("Crawling Done!")
