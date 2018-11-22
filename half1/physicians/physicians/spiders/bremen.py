# -*- coding: utf-8 -*-

import os
import sys
import re

from scrapy.spider import BaseSpider
from scrapy.http import Request
from urlparse import urljoin
from logging import WARNING

from items import PhysiciansItem, SpecialtiesItem, LocationsItem


class BremenSpider(BaseSpider):
    name = 'bremen'
    allowed_domains = ['kvhb.de']

    start_urls = [
        'https://www.kvhb.de/dsearch/kinder%C3%A4rzte?option_doctors_name=&radio1=bremen&'
        'option_fremdsprachen=0&op=SUCHEN&form_build_id=form-7HN7CDu1__c6dwI6A7KeQ5E_tjVxUpiEa_hslC97b5o&'
        'form_id=doctor_search_form',
        'https://www.kvhb.de/dsearch/haus%C3%A4rzte?option_doctors_name=&radio1=bremen&'
        'option_fremdsprachen=0&op=SUCHEN&form_build_id=form-dmLor6gGr2hKTf_5OF_q0FAkVHCq05vbJAUknKd-mcM&'
        'form_id=doctor_search_form',
        'https://www.kvhb.de/dsearch/fach%C3%A4rzte?option_doctors_name=&option_fachrichtung=0&'
        'option_zusatzbezeichnung=0&radio1=bremen&option_fremdsprachen=0&op=SUCHEN&'
        'form_build_id=form-xwH5IJiLBAZGxM38AUhuc5ls3zkgOoDpsvjz_nUPBLg&form_id=doctor_search_form'
    ]

    result_path_type = 'half1'

    item_count = 1

    list_type = ['Kinder', u'Haus\xe4rzte', u'Fach\xe4rzte']

    state = 'Bremen'

    out_path = None
    physician_csv = None
    specialty_csv = None
    location_csv = None

    def __init__(self, *args, **kwargs):
        sys.path.append(os.path.abspath(os.path.join('../../../..', 'half1')))
        import resultpath

        self.out_path = resultpath.result_path(self.result_path_type, self.name)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        self.physician_csv = self.out_path + self.name + '_physician.csv'
        self.specialty_csv = self.out_path + self.name + '_specialty.csv'
        self.location_csv = self.out_path + self.name + '_location.csv'

        super(BremenSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield Request(url='https://www.kvhb.de', callback=self.parse_list_type)

    def parse_list_type(self, response):
        meta = response.meta
        for i, start_url in enumerate(self.start_urls):
            current_list_type = self.list_type[i]
            meta['list_type'] = current_list_type
            yield Request(url=start_url, meta=meta, callback=self.parse_page_links)

    def parse_page_links(self, response):

        meta = response.meta
        next_page = response.xpath("//li[@class='pager-next']/a/@href").extract()
        next_page = urljoin(response.url, next_page[0]) if next_page else None

        current_page_links = response.xpath("//div[@class='doctor-info']/div[@class='name']/a/@href").extract()
        if current_page_links:
            for link in current_page_links:
                yield Request(url=urljoin(response.url, link), meta=meta, callback=self.parse_single_page)

        if next_page:
            yield Request(url=next_page, meta=meta, callback=self.parse_page_links)

    def parse_single_page(self, response):
        items = []
        physicians = self.parse_physician(response)
        specialties = self.parse_speciality(response)
        locations = self.parse_location(response)

        self.item_count += 1

        items.append(physicians)
        items.append(specialties)
        items.append(locations)

        for item in items:
            yield item

    def parse_physician(self, response):
        list_type = response.meta['list_type']
        physicians = PhysiciansItem()
        primary_key = re.search('dpage/(.*?)/', response.url).group(1)

        full_name = response.xpath('//div[@id="center"]/h1/text()').extract()
        if full_name:
            full_name = self._clean_text(full_name[0]).encode('utf-8')

        first_name = full_name.split(' ')[-2]
        last_name = full_name.split(' ')[-1]

        physicians['URL'] = response.url
        physicians['GeneratedID'] = self.item_count
        physicians['SitePrimaryKey'] = primary_key
        physicians['Fullname'] = full_name
        physicians['FirstName'] = first_name
        physicians['LastName'] = last_name
        physicians['StateName'] = self.state
        physicians['ListType'] = list_type

        return physicians

    def parse_speciality(self, response):
        specialities = SpecialtiesItem()
        speciality = []
        specialty_name = response.xpath('//div[@class="speciality"]/text()').extract()
        if len(specialty_name) > 0:
            for name in specialty_name:
                speciality.append(name)

        specialities['PhysicianPrimaryID'] = re.search('dpage/(.*?)/', response.url).group(1)
        specialities['SpecialtyName'] = ', '.join(specialty_name)
        return specialities

    def parse_location(self, response):
        locations = LocationsItem()

        full_name = response.xpath('//div[@id="center"]/h1/text()').extract()
        if full_name:
            full_name = self._clean_text(full_name[0]).encode('utf-8')

        address = response.xpath('//div[@id="address"]/div[@class="text"]/text()').extract()
        if len(address) == 2:
            full_address = ', '.join(address) + ', Germany'
        elif len(address) > 2:
            full_address = address[0] + ', ' + address[1] + ', Germany'
        else:
            full_address = None
        # street = address[0].encode('utf-8')
        # postal_code = int(address[1].split(' ')[0].encode('utf-8'))
        # city = address[1].split(' ')[1].encode('utf-8')
        name = response.xpath('//div[@id="address"]/div[@class="add-info"]/text()').extract()

        try:
            if name[0] is not None:
                name = name[0].encode('utf-8')
        except:
            self.log('Found no name, name is same wit physician name', WARNING)
            name = full_name

        phone = []
        telephone = response.xpath('//div[@id="telefon"]/span/text()').extract()
        if len(telephone) > 0:
            for number in telephone:
                phone.append(number.encode('utf-8'))

        locations['LocationID'] = self.item_count
        locations['PageURL'] = response.url
        locations['Name'] = name
        locations['PhysicianID'] = re.search('dpage/(.*?)/', response.url).group(1)
        locations['Address'] = full_address
        locations['State'] = self.state
        # locations['Street'] = street
        # locations['Number'] = postal_code
        # locations['City'] = city
        locations['Phone'] = ', '.join(phone)

        return locations

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
