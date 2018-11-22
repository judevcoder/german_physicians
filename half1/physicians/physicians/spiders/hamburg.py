# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import requests

from scrapy.spider import BaseSpider
from scrapy.http import Request
from urlparse import urljoin
from lxml import html

from items import PhysiciansItem, SpecialtiesItem, LocationsItem


class HamburgSpider(BaseSpider):
    name = 'hamburg'
    allowed_domains = ['kvhh.net']

    start_urls = ['http://www.kvhh.net/kvhh/arztsuche/index/p/274']

    search_page = 'http://www.kvhh.net/kvhh/arztsuche/suche/p/274/0/suche/?' \
                  'fname=&fstrasse=&fstadtteil={select_val}&ffachgebiet=-1&fschwerpunkt=&' \
                  'fzusatz=&fleistung=-1&ffremdsprache=-1&arzt_sprechzeiten%5Bfvon%5D=&' \
                  'arzt_sprechzeiten%5Bfbis%5D=&fbarriere=0&submit=Suchen'

    result_path_type = 'half1'

    state = 'Hamburg'

    current_page = 0

    item_count = 1

    out_path = None
    physician_csv = None
    specialty_csv = None
    location_csv = None

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                             '(KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    def __init__(self, *args, **kwargs):
        sys.path.append(os.path.abspath(os.path.join('../../../..', 'german_physicians')))
        import resultpath

        self.out_path = resultpath.result_path(self.result_path_type, self.name)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        self.physician_csv = self.out_path + self.name + '_physician.csv'
        self.specialty_csv = self.out_path + self.name + '_specialty.csv'
        self.location_csv = self.out_path + self.name + '_location.csv'

        super(HamburgSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_start_page)

    def parse_start_page(self, response):
        select_val_list = response.xpath('//select[@id="fstadtteil"]/option/@value').extract()
        for select_val in select_val_list:
            search_page = self.search_page.format(select_val=select_val)
            detail_page_links = html.fromstring(requests.get(search_page).text).xpath('//td[@class='
                                                                                      '"arztsuche-arzt-name"]/a/@href')
            for detail_page_link in detail_page_links:
                url = urljoin(response.url, detail_page_link)
                yield Request(url=url, callback=self.parse_detail_page)

    def parse_detail_page(self, response):
        parse_items = []
        physicians = self.parse_physician(response)
        specialties = self.parse_speciality(response)
        locations = self.parse_location(response)

        self.item_count += 1

        parse_items.append(physicians)
        parse_items.append(specialties)
        parse_items.append(locations)

        for parse_item in parse_items:
            yield parse_item

    def parse_physician(self, response):
        physicians = PhysiciansItem()

        physician_name = self._clean_text(response.xpath(
            '//div[@class="arztsuche-content-kopf-anschrift"]/text()'
        ).extract()[0]).encode('utf-8')

        try:
            first_name = physician_name.split(' ')[-2].encode('utf-8')
        except:
            first_name = physician_name.split(' ')[-2]

        try:
            last_name = physician_name.split(' ')[-1].encode('utf-8')
        except:
            last_name = physician_name.split(' ')[-1]
            pass
        primary_key = int(re.search('AID/(.*?)/PID', response.url).group(1))
        remarks = self._clean_text(response.xpath(
            '//tr/td[text()="%s"]/../td/text()' % 'Zusatz/Bereich'
        ).extract()[1]).encode('utf-8')

        physicians['URL'] = response.url
        physicians['GeneratedID'] = self.item_count
        physicians['SitePrimaryKey'] = primary_key
        physicians['Fullname'] = physician_name
        physicians['FirstName'] = first_name
        physicians['LastName'] = last_name
        physicians['StateName'] = self.state
        physicians['remarks'] = remarks

        return physicians

    def parse_speciality(self, response):
        specialties = SpecialtiesItem()

        speciality_id = int(re.search('AID/(.*?)/PID', response.url).group(1))
        speciality = []
        content_list = response.xpath('//div[@class="arztsuche-content-daten"]/table/tr').extract()
        for content in content_list:
            try:
                content_text = html.fromstring(content).xpath('//tr/td/text()')
                content_key = content_text[0]
                content_text.pop(0)
                content_val = content_text
                if 'Fachgebiet' in content_key.encode('utf-8'):
                    if len(content_val) > 1:
                        for val in content_val:
                            if self._clean_text(val) is not '':
                                speciality.append(self._clean_text(val))

                    else:
                        if self._clean_text(content_val[0]) is not '':
                            speciality.append(self._clean_text(content_val[0]))
                elif 'Schwerpunkte' in content_key.encode('utf-8'):
                    if len(content_val) > 1:
                        for val in content_val:
                            if self._clean_text(val) is not '':
                                speciality.append(self._clean_text(val))

                    else:
                        if self._clean_text(content_val[0]) is not '':
                            speciality.append(self._clean_text(content_val[0]))
                elif 'Genehmigte Leistungen' in content_key.encode('utf-8'):
                    if len(content_val) > 1:
                        for val in content_val:
                            if self._clean_text(val) is not '':
                                speciality.append(self._clean_text(val))

                    else:
                        if self._clean_text(content_val[0]) is not '':
                            speciality.append(self._clean_text(content_val[0]))
            except:
                print("There is no specialities")

        specialties['SpecialtyName'] = ', '.join(speciality)
        specialties['PhysicianPrimaryID'] = speciality_id

        return specialties

    def parse_location(self, response):
        locations = LocationsItem()

        location_name = self._clean_text(response.xpath(
            '//div[@class="arztsuche-content-kopf-anschrift"]/text()'
        ).extract()[0]).encode('utf-8')
        location_id = int(re.search('PID/(.*)', response.url).group(1))
        physician_id = int(re.search('AID/(.*?)/PID', response.url).group(1))
        location_infos = response.xpath('//div[@class="arztsuche-content-kopf-anschrift"]/text()').extract()
        street = self._clean_text(location_infos[1]).encode('utf-8')
        # postal_code = int(self._clean_text(location_infos[2]).split(' ')[0])
        # city = self._clean_text(location_infos[2]).split(' ')[1].encode('utf-8')
        full_address = street + self._clean_text(location_infos[2]).encode('utf-8') + ', Germany'

        phone_number = None
        try:
            if location_infos[3] and 'Tel.' in self._clean_text(location_infos[3]):
                phone_number = self._clean_text(location_infos[3].replace('Tel.', '')).encode('utf-8')
        except:
            pass

        web_site = None
        try:
            if location_infos[4] and 'Internet' in self._clean_text(location_infos[4]):
                web_site = response.xpath('//div[@class="arztsuche-content-kopf-anschrift"]/a/@href').extract()[0]
        except:
            pass

        locations['LocationID'] = location_id
        locations['PageURL'] = response.url
        locations['PhysicianID'] = physician_id
        locations['Address'] = full_address
        locations['Name'] = location_name
        # locations['Street'] = street
        # locations['Number'] = postal_code
        # locations['City'] = city
        locations['Phone'] = phone_number
        locations['Website'] = web_site
        locations['HBSNR'] = location_id
        locations['State'] = self.state

        return locations

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
