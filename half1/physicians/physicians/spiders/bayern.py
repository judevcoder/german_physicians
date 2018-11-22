# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import json

from scrapy.spider import BaseSpider
from scrapy.http import Request
from selenium import webdriver
from lxml import html

from items import PhysiciansItem, SpecialtiesItem, LocationsItem

sys.path.append(os.path.abspath(os.path.join('../../../..', 'half1')))
import resultpath


class BayernSpider(BaseSpider):
    name = 'bayern'
    allowed_domains = ['kvb.de']

    start_urls = ['https://arztsuche.kvb.de/cargo/app/erweiterteSuche.htm']

    all_detail_link = ['https://arztsuche.kvb.de/cargo/app/suchergebnisse.htm?'
                       'hashwert=97f24e6c79d5c3c7ebedfb3e1f7de67&page=1&resultCount=65000']

    # all_detail_link = ['https://arztsuche.kvb.de/cargo/app/suchergebnisse.htm?hashwert=97f24e6c79d5c3c7ebedfb3e1f7de67&page=871&resultCount=65000']

    result_path_type = 'half1'

    next_page_url = 'https://arztsuche.kvb.de/cargo/app/suchergebnisse.htm?' \
                    'hashwert=97f24e6c79d5c3c7ebedfb3e1f7de67&page={next_page_num}&resultCount=65000'

    # next_page_url = '{response_url}&page={page_num}&resultCount={result_count}'

    state = 'Bayern'

    item_count = 1

    link_count = 1

    out_path = None
    physician_csv = None
    specialty_csv = None
    location_csv = None

    result_count = None

    def __init__(self, *args, **kwargs):
        self.out_path = resultpath.result_path(self.result_path_type, self.name)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        self.physician_csv = self.out_path + self.name + '_physician.csv'
        self.specialty_csv = self.out_path + self.name + '_specialty.csv'
        self.location_csv = self.out_path + self.name + '_location.csv'

        super(BayernSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1

    def start_requests(self):
        yield Request(url=self.all_detail_link[0], callback=self.parse_single_page)

    def parse_start_page(self, response):

        phantomjs_path = resultpath.get_phantomjs_path()
        postal_list = resultpath.csv_to_dict()

        if not os.path.exists(resultpath.get_root_path() + '/csv_json/page_links.json'):
            pages_links = {}
            driver = webdriver.PhantomJS(executable_path=phantomjs_path)
            driver.get(response.url)
            time.sleep(10)
            select_box = driver.find_element_by_id('fachgebiete')
            for i, option in enumerate(select_box.find_elements_by_tag_name('option')):
                if i == 0:
                    option.click()
                    time.sleep(1)
                elif i > 0:
                    driver.get(self.start_urls[0])
                    time.sleep(10)
                    driver.find_elements_by_tag_name('option')[i].click()
                    time.sleep(1)

                for index, value in enumerate(postal_list):
                    if index > 0:
                        driver.get(self.start_urls[0])
                        time.sleep(10)
                        driver.find_elements_by_tag_name('option')[i].click()
                        time.sleep(1)
                    json_data = {}
                    postal_code = value
                    stats = postal_list[value][0]
                    address_input = driver.find_element_by_id('adresse')
                    address_input.clear()
                    address_input.send_keys(postal_code)
                    search_button = driver.find_element_by_id('erweiterteSuche_Submit')
                    search_button.click()
                    time.sleep(10)
                    driver.switch_to_window(driver.window_handles[-1])
                    link = driver.current_url
                    json_data['stats'] = stats
                    json_data['link'] = link
                    pages_links[str(self.link_count) + '-' + postal_code] = json_data
                    self.link_count += 1

            with open(resultpath.get_root_path() + '/csv_json/page_links.json', 'wb') as outfile:
                json.dump(pages_links, outfile)

        json_data = json.load(open(resultpath.get_root_path() + '/csv_json/page_links.json'))
        if len(json_data):
            for key, data in json_data.iteritems():
                link = data['link']
                yield Request(url=link, callback=self.parse_single_page, dont_filter=True)

    def parse_single_page(self, response):

        elements = response.xpath('//div[@class="suchergebnisse_liste"]/'
                                  'div[@class="suchergebnisse_praxis_tabelle"]').extract()

        for element in elements:
            html_element = html.fromstring(element)

            full_name = html_element.xpath('//td[@class="titel_name_zelle"]/a/text()')[0].encode('utf-8')
            first_name = None
            last_name = None
            person = True

            if 'Dr' in full_name or 'Dipl' in full_name:
                person = True
            elif '-' in full_name or 'KfH' in full_name \
                    or 'hospital' in full_name or 'GmbH' in full_name \
                    or 'AG' in full_name or 'Institute' in full_name or 'Inst' in full_name:
                person = False

            if person:
                try:
                    first_name = full_name.split(' ')[-2]
                    last_name = full_name.split(' ')[-1]
                except:
                    print("Can't parse First Name and Last Name")

            remark = []
            remark_list = html_element.xpath('//td[@class="name_zelle"]/table[@class="name_tabelle"][2]/tr/td/text()')
            for val in remark_list:
                if self._clean_text(val) is not '':
                    remark.append(self._clean_text(val).encode('utf-8'))

            result_remark = ', '.join(remark)

            specialities = []

            specialities_under_name = html_element.xpath('//td[@class="fachgebiet_zelle"]/text()')
            for speciality in specialities_under_name:
                if self._clean_text(speciality) is not '':
                    specialities.append(self._clean_text(speciality))
            specialities_under_location = html_element.xpath('//td[@class="suchergebnisse_zusatzinfo_zweite_spalte"][1]'
                                                            '/span[@class="zusatzinfo_text"]/text()')
            for speciality in specialities_under_location:
                if self._clean_text(speciality) is not '':
                    specialities.append(self._clean_text(speciality))

            result_specialities = ', '.join(specialities).encode('utf-8')

            location_name = None
            full_address = None
            address = []
            address_info = html_element.xpath('//table[@class="adresse_tabelle"]/tr/td/text()')
            for info in address_info:
                if self._clean_text(info) is not '':
                    address.append(self._clean_text(info))

            if len(address) == 2:
                full_address = address[0] + ', ' + address[1] + ', Germany'
                location_name = address[0] + ' ' + address[1]
            elif len(address) > 2:
                full_address = address[-2] + ', ' + address[-1] + ', Germany'
                location_name = address[-2] + ' ' + address[-1]

            # street = None
            # postal_code = None
            # city = None
            # if len(address) > 0:
            #     try:
            #         street = address[-2].encode('utf-8')
            #         postal_code = int(address[-1].split()[0])
            #         city = address[-1].split(u'\xa0')[-1].encode('utf-8')
            #     except:
            #         pass

            phone = []
            phone_numbers = html_element.xpath('//td[@class="tel_td"]/../td[2]/text()')
            if len(phone_numbers) > 0:
                for number in phone_numbers:
                    if self._clean_text(number) is not '':
                        phone.append(self._clean_text(number))

            website = []
            email = []
            all_links = html_element.xpath('//table[@class="tel_tabelle"]/tr/td/a/text()')
            for link in all_links:
                if 'http' in self._clean_text(link):
                    if ';' in self._clean_text(link):
                        website.append(self._clean_text(link).split(';')[0])
                elif '@' in self._clean_text(link):
                    email.append(self._clean_text(link))

            parse_items = []
            physicians = PhysiciansItem()
            specialties = SpecialtiesItem()
            locations = LocationsItem()

            physicians['URL'] = response.url
            physicians['GeneratedID'] = self.item_count
            physicians['SitePrimaryKey'] = self.item_count
            physicians['Fullname'] = full_name
            physicians['FirstName'] = first_name
            physicians['LastName'] = last_name
            physicians['StateName'] = self.state
            physicians['remarks'] = result_remark
            physicians['ListType'] = None

            specialties['PhysicianPrimaryID'] = self.item_count
            specialties['SpecialtyName'] = result_specialities

            locations['LocationID'] = self.item_count
            locations['PhysicianID'] = self.item_count
            locations['PageURL'] = response.url
            locations['Address'] = full_address.encode('utf-8')
            locations['Name'] = location_name.encode('utf-8')
            locations['State'] = self.state
            # locations['Street'] = street
            # locations['City'] = city
            # locations['Number'] = postal_code
            locations['email'] = ', '.join(email)
            locations['Phone'] = ', '.join(phone)
            locations['Website'] = ', '.join(website)

            self.item_count += 1

            parse_items.append(physicians)
            parse_items.append(specialties)
            parse_items.append(locations)

            for item in parse_items:
                yield item
        # if self.current_page == 1:
        #     try:
        #         self.result_count = int(response.xpath('//input[@name="resultCount"]/@value').extract()[0])
        #     except:
        #         pass

        next_button = None
        try:
            next_button = response.xpath('//input[@class="BUTTON FORWARD"]')[0]
        except:

            pass
        if next_button:
            self.current_page += 1
            yield Request(
                url=self.next_page_url.format(next_page_num=self.current_page),
                callback=self.parse_single_page
            )
            # if self.current_page == 1:
            #     next_page = self.next_page_url.format(response_url=response.url,
            #                                           page_num=self.current_page + 1,
            #                                           result_count=self.result_count)
            #     self.current_page += 1
            #     yield Request(url=next_page, callback=self.parse_single_page)
            # else:
            #     try:
            #         self.current_page += 1
            #         next_page = response.url.replace(re.search('page=(.*?)Count', response.url)
            #                                          .group(1), str(self.current_page) + '&result')
            #         yield Request(url=next_page, callback=self.parse_single_page)
            #     except:
            #         print("Not Found next page!")
            #         self.current_page = 1
        else:
            print ("Crawling done!")
            return

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
