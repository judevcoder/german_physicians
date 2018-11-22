# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import signals
from scrapy.contrib.exporter import CsvItemExporter
from spiders.items import PhysiciansItem, SpecialtiesItem, LocationsItem
from spiders.resultpath import result_path, clean_csv


class PhysiciansPipeline(object):
    def __init__(self, spider):
        self.files = []
        self.full_path = result_path(spider.result_path_type, spider.name)
        file1 = open(self.full_path + 'temp_physicians.csv', 'wb')
        self.files.extend([file1])
        self.exporter1 = CsvItemExporter(fields_to_export=PhysiciansItem.fields.keys(), file=file1)

        file2 = open(self.full_path + 'temp_specialities.csv', 'wb')
        self.files.extend([file2])
        self.exporter2 = CsvItemExporter(fields_to_export=SpecialtiesItem.fields.keys(), file=file2)

        file3 = open(self.full_path + 'temp_locations.csv', 'wb')
        self.files.extend([file3])
        self.exporter3 = CsvItemExporter(fields_to_export=LocationsItem.fields.keys(), file=file3)

    @classmethod
    def from_crawler(cls, crawler):
        spider = crawler.spider
        pipeline = cls(spider)
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        self.exporter1.start_exporting()
        self.exporter2.start_exporting()
        self.exporter3.start_exporting()

    def spider_closed(self, spider):
        self.exporter1.finish_exporting()
        self.exporter2.finish_exporting()
        self.exporter3.finish_exporting()
        for _file in self.files:
            _file.close()

        clean_csv(self.full_path)

    def process_item(self, item, spider):
        self.exporter1.export_item(item)
        self.exporter2.export_item(item)
        self.exporter3.export_item(item)
        return item
