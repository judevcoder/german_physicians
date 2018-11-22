# -*- coding: utf-8 -*-

import os
import sys
import re

from scrapy.spider import BaseSpider
from scrapy.http import Request
from lxml import html

from items import PhysiciansItem, SpecialtiesItem, LocationsItem


class BadenSpider(BaseSpider):
    name = 'baden'
    allowed_domains = ['arztsuche-bw.de']

    start_urls = ['http://www.arztsuche-bw.de/index.php?suchen=1&'
                  'sorting=name&direction=ASC&arztgruppe=alle&'
                  'id_fachgruppe=&vorname=&nachname=ohne+Titel+%28Dr.%29&'
                  'plz=&ort=&strasse=&landkreis=']

    next_page_link = 'http://www.arztsuche-bw.de/index.php?suchen=1&offset={offset}' \
                     '&id_z_arzt_praxis=0&id_fachgruppe=0&id_zusatzbezeichnung=0' \
                     '&id_genehmigung=0&id_dmp=0&id_zusatzvertraege=0&id_sprache=0' \
                     '&vorname=&nachname=ohne+Titel+%28Dr.%29&arztgruppe=alle&geschlecht=&' \
                     'wochentag=&zeiten=&fa_name=&plz=&ort=&strasse=&schluesselnr=&' \
                     'schluesseltyp=lanr7&landkreis=&id_leistungsort_art=0&id_praxis_zusatz=0&' \
                     'sorting=name&direction=ASC&checkbox_content=&name_schnellsuche=&' \
                     'fachgebiet_schnellsuche='

    result_path_type = 'half1'

    current_page = 1

    item_count = 1

    state = 'Baden-Württemberg'

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

        super(BadenSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_page)

    def parse_page(self, response):

        item_list = response.xpath('//li[contains(@class, "resultrow")]').extract()
        for item in item_list:

            parse_items = []
            physicians = PhysiciansItem()
            specialties = SpecialtiesItem()
            locations = LocationsItem()

            lanr = None
            location_name = None
            street = None
            postal_code = None
            city = None
            emails = None
            websites = None

            item_html = html.fromstring(item)

            full_name = item_html.xpath('//li/dl/dd[@class="name"]/dl/dt[1]/text()')
            if len(full_name) == 1:
                full_name = full_name[0].encode('utf-8')
            elif len(full_name) > 1:
                full_name = ' '.join(full_name).encode('utf-8')

            first_name = full_name.split(' ')[-2]
            last_name = full_name.split(' ')[-1]

            physician_keys = item_html.xpath('//dd[contains(@class, "detaildaten")]/'
                                             'div[contains(@class, "column")]/dl/dd/text()')
            for key in physician_keys:
                if 'LANR' in key:
                    lanr = int(self._clean_text(key.split(':')[1]))

            address = item_html.xpath('//li/dl/dd[@class="adresse"]/p/text()')
            if len(address) > 0:
                location_name = address[0].encode('utf-8')
                full_address = address[1] + ', ' + address[2] + ', Germany'
            else:
                full_address = None
                # street = address[1].encode('utf-8')
                # postal_code = address[2].split(' ')[0]
                # city = self._clean_text(address[2].encode('utf-8').replace(postal_code.encode('utf-8'), ''))

            contact_numbers = item_html.xpath('//li/dl/dd[@class="adresse"]/dl/dd/text()')
            numbers = []
            if len(contact_numbers) > 0:
                for number in contact_numbers:
                    if 'Telefon' in number.encode('utf-8'):
                        numbers.append(number.encode('utf-8').split(':')[1])
                    elif 'Telefax' in number.encode('utf-8'):
                        numbers.append(number.encode('utf-8').split(':')[1])
                    elif 'Mobil' in number.encode('utf-8'):
                        numbers.append(number.encode('utf-8').split(':')[1])
            phone_number = ', '.join(numbers)

            contact_links = item_html.xpath('//li/dl/dd[@class="adresse"]/dl/dd/a/text()')
            email_list = []
            website_list = []
            if len(contact_links) > 0:
                for link in contact_links:
                    if 'http' in link:
                        website_list.append(link)
                    else:
                        email_list.append(self.deobfuscate(link))

            if len(email_list) > 0:
                emails = ', '.join(email_list)
            if len(website_list) > 0:
                websites = ' '.join(website_list)

            gmap_link = item_html.xpath('//li/dl/dd/div/div/button[@class="kv-button"]/@onclick')
            if gmap_link:
                gmap_link = re.search('window.open(.*?)&output=embed', gmap_link[0]).group(1).replace('(', '').replace("'", '')

            specialty_val = item_html.xpath('//li//dl[@class="bulletlist"]/dd/text()')
            if len(specialty_val) > 0:
                specialty_val = ', '.join(specialty_val)

            physicians['URL'] = response.url
            physicians['GeneratedID'] = self.item_count
            physicians['SitePrimaryKey'] = self.item_count
            physicians['Fullname'] = full_name
            physicians['FirstName'] = first_name
            physicians['LastName'] = last_name
            physicians['StateName'] = self.state
            physicians['LANR'] = lanr
            physicians['ListType'] = None

            specialties['PhysicianPrimaryID'] = self.item_count
            specialties['SpecialtyName'] = specialty_val

            locations['LocationID'] = self.item_count
            locations['PageURL'] = response.url
            locations['Name'] = location_name
            locations['PhysicianID'] = self.item_count
            locations['Address'] = full_address
            locations['State'] = self.state
            # locations['Street'] = street
            # locations['Number'] = int(postal_code)
            # locations['City'] = city
            locations['email'] = emails
            locations['Phone'] = phone_number
            locations['Website'] = websites
            locations['GMaps_link'] = gmap_link

            self.item_count += 1

            parse_items.append(physicians)
            parse_items.append(specialties)
            parse_items.append(locations)
            for parse_item in parse_items:
                yield parse_item

        next_page_button = response.xpath("//button[contains(@class, 'next-button')]/@class").extract()[0]
        if 'inaktiv' in next_page_button:
            return
        else:
            next_page = self.next_page_link.format(offset=self.current_page*20)
            self.current_page += 1
            yield Request(url=next_page, callback=self.parse_page)

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)

    @staticmethod
    def de_obfuscate_text(coded, key):
        offset = (len(key) - len(coded)) % len(key)
        shifted_key = key[offset:] + key[:offset]
        lookup = dict(zip(key, shifted_key))
        return "".join(lookup.get(ch, ch) for ch in coded)

    @staticmethod
    def deobfuscate(s):
        s = s[::-1]
        final_s = ''
        characters = "123456789qwertzuiopasdfghjklyxcvbnmMNBVCXYLKJHGFDSAPOIUZTREWQ"
        char_len = len(characters)
        for i, char in enumerate(s):
            if char in characters:
                cur_pos = characters.index(char)
                cpos = cur_pos - (char_len - 1) // 2
                cpos = char_len + cpos if cpos < 0 else cpos
                final_s += characters[cpos]
            else:
                final_s += char
        return ''.join(final_s).strip('@')
