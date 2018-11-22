# coding=utf-8
import os
import sys
import re
import urllib

from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
from urlparse import urljoin
from lxml import html

from items import PhysiciansItem, SpecialtiesItem, LocationsItem

sys.path.append(os.path.abspath(os.path.join('../../../..', 'half1')))
import resultpath


class BerlinSpider(BaseSpider):
    name = 'berlin'
    allowed_domains = ['kvberlin.de']

    start_urls = ['https://www.kvberlin.de/60arztsuche/suche.php']

    result_path_type = 'half1'

    detail_page =['https://www.kvberlin.de/60arztsuche/detail1.php?id=622184704&go=0&Arztdataberechtigung=']

    primary_key = 1

    item_count = 1

    state_name = 'Berlin'

    headers = {'Content-Type': 'application/json'}

    out_path = None
    physician_csv = None
    specialty_csv = None
    location_csv = None

    def __init__(self, *args, **kwargs):
        self.out_path = resultpath.result_path(self.result_path_type, self.name)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        self.physician_csv = self.out_path + self.name + '_physician.csv'
        self.specialty_csv = self.out_path + self.name + '_specialty.csv'
        self.location_csv = self.out_path + self.name + '_location.csv'

        super(BerlinSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 1

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_start_page)

    def parse_start_page(self, response):

        area_vals = response.xpath('//select[@name="Fachgebiet"]/option/text()').extract()
        districts_vals = response.xpath('//select[@name="Stadtteil"]/option/text()').extract()

        for i in range(0, len(area_vals) - 1):
            for j in range(0, len(districts_vals) - 1):

                if i == 0:
                    area = ''
                else:
                    area = area_vals[i]

                if j == 0:
                    districts = ''
                else:
                    districts = districts_vals[j]

                form_data = {
                    'Fachgebiet': area,
                    'Stadtteil': districts,
                    'Psychotherapeut': 'an',
                    'Fachgebiet_liste': 'fachgebiete',
                    'Schwerpunkt': '',
                    'Schwerpunkt_liste': 'schwerpunkte',
                    'Zusatzbezeichnung': '',
                    'Zusatzbezeichnung_liste': 'zusatzbezeichnungen',
                    'Name': '',
                    'Arztdataberechtigung': '',
                }
                meta = response.meta.copy()
                meta['form_data'] = form_data
                yield FormRequest(
                    url=response.url,
                    method='POST',
                    formdata=form_data,
                    meta=meta,
                    callback=self.parse_result_link,
                    dont_filter=True
                )

    def parse_result_link(self, response):
        meta = response.meta.copy()
        start = meta.get('start')
        area = meta['form_data']['Fachgebiet']
        districts = meta['form_data']['Stadtteil']
        last_page = meta.get('last_page')

        total_count = re.search('ergab(.*?)Treffer', response.body_as_unicode())
        if total_count:
            try:
                total_count = int(self._clean_text(total_count.group(1)))
            except:
                print("Can't find physician in this page!")

        detail_page_links = response.xpath('//table[@class="search"]/tr/td[@class="tabletext"][1]/a/@href').extract()
        if len(detail_page_links) > 0:
            for detail_page_link in detail_page_links:
                url = urljoin(response.url, detail_page_link)
                yield Request(url=url, callback=self.parse_detail_page)

        if last_page:
            return

        next_button = False
        if not last_page:
            last_page = False

        pagination_text = response.xpath('//td[@class="nav2"]/a/text()').extract()
        for text in pagination_text:
            if 'Letzte' in self._clean_text(text):
                last_page = True
                break
            try:
                if u'N\xe4chste 10 Treffer' in self._clean_text(text):
                    next_button = True
                    break
            except:
                print('Please find next page!')

        if next_button or last_page:
            if start:
                start = int(start)
            elif start is None:
                start = 11

            if start >= total_count:
                start = total_count

            form_data = {
                    'Fachgebiet': area,
                    'Stadtteil': districts,
                    'Psychotherapeut': 'an',
                    'Fachgebiet_liste': 'fachgebiete',
                    'Schwerpunkt': '',
                    'Schwerpunkt_liste': 'schwerpunkte',
                    'Zusatzbezeichnung': '',
                    'Zusatzbezeichnung_liste': 'zusatzbezeichnungen',
                    'Name': '',
                    'Arztdataberechtigung': '',
                    'start': str(start),
                }

            meta['start'] = start + 10
            meta['form_data'] = form_data
            meta['last_page'] = last_page

            yield FormRequest(
                url=self.start_urls[0],
                method='POST',
                formdata=form_data,
                meta=meta,
                callback=self.parse_result_link,
                dont_filter=True
            )

    def parse_detail_page(self, response):
        parse_items = []
        physicians = self.parse_physician(response)
        specialties = self.parse_specialties(response)
        locations = self.parse_locations(response)

        self.item_count += 1

        parse_items.append(physicians)
        parse_items.append(specialties)
        parse_items.append(locations)

        for item in parse_items:
            yield item

    def parse_physician(self, response):
        physicians = PhysiciansItem()

        full_name = response.xpath('//table/tr/td/h1/text()').extract()[0].encode('utf-8')
        first_name = None
        last_name = None
        try:
            first_name = full_name.split()[-2]
            last_name = full_name.split()[-1]
        except:
            print("Can't parse First name and Last name!")

        site_primary_key = int(re.search('id=(.*?)&go', response.url).group(1))

        physicians['URL'] = response.url
        physicians['GeneratedID'] = self.item_count
        physicians['SitePrimaryKey'] = site_primary_key
        physicians['ListType'] = None
        physicians['Fullname'] = full_name
        physicians['FirstName'] = first_name
        physicians['LastName'] = last_name
        physicians['StateName'] = self.state_name
        # physicians['LANR'] = response.url
        # physicians['remarks'] = response.url
        return physicians

    def parse_specialties(self, response):
        specialties = SpecialtiesItem()

        speciality_name = []
        specialites_title = response.xpath('//td[@align="left"]/p/b/text()').extract()
        if len(specialites_title) > 0:
            for title in specialites_title:
                if 'Fachgebiete' in title:
                    speciality_vals = response.xpath('//td[@align="left"]/p/b[contains(text(), "%s")]'
                                                    '/../following::ul[1]/li/text()' % title).extract()
                    if len(speciality_vals) > 0:
                        for speciality in speciality_vals:
                            speciality_name.append(self._clean_text(speciality).encode('utf-8'))
                elif 'Schwerpunkte' in title:
                    speciality_vals = response.xpath('//td[@align="left"]/p/b[contains(text(), "%s")]'
                                                     '/../following::ul[1]/li/text()' % title).extract()
                    if len(speciality_vals) > 0:
                        for speciality in speciality_vals:
                            speciality_name.append(self._clean_text(speciality).encode('utf-8'))
                # elif 'Schwerpunkte' in title:
                #     speciality_vals = response.xpath('//td[@align="left"]/p/b[contains(text(), "%s")]'
                #                                      '/../following::ul[1]/li/text()' % title).extract()
                #     if len(speciality_vals) > 0:
                #         for speciality in speciality_vals:
                #             speciality_name.append(self._clean_text(speciality).encode('utf-8'))

        specialties['PhysicianPrimaryID'] = int(re.search('id=(.*?)&go', response.url).group(1))
        specialties['SpecialtyName'] = ', '.join(speciality_name)
        return specialties

    def parse_locations(self, response):
        locations = LocationsItem()

        physician_id = int(re.search('id=(.*?)&go', response.url).group(1))
        location_name = response.xpath('//table/tr/td/h2/text()').extract()[0].encode('utf-8')

        address = response.xpath('//table/tr/td/h2/following::p').extract()
        full_address = None
        street = None
        zip_code = None
        city = None
        phone = []
        email = []
        website = []

        try:
            temp_addr = html.fromstring(address[0]).xpath('//p/text()')
            full_address = self._clean_text(temp_addr[0]) + ', ' + self._clean_text(temp_addr[1]) + ', Germany'
            # street = self._clean_text(html.fromstring(address[0]).xpath('//p/text()')[0])
            # zip_code = int(self._clean_text(html.fromstring(address[0]).xpath('//p/text()')[1].split()[0]))
            # city = self._clean_text(html.fromstring(address[0]).xpath('//p/text()')[1].split()[1])
        except:
            print("Can't find location details information!")

        try:
            contact_infos = html.fromstring(address[1]).xpath('//p/text()')
            if len(contact_infos) > 0:
                for info in contact_infos:
                    if 'Nummer' in self._clean_text(info):
                        phone_number = self._clean_text(info).split(':')[1].replace(' ', '')
                        phone.append(phone_number)
                    elif 'E-Mail' in self._clean_text(info):
                        email_text = response.xpath('//table/tr/td/p/a/@href').extract()
                        for text in email_text:
                            if '@' in text:
                                email.append(self._clean_text(text).replace('mailto:', ''))
                            elif 'http' in text:
                                website.append(self._clean_text(text).replace(' ', ''))
        except:
            print("Can't find contact information!")

        locations['LocationID'] = self.item_count
        locations['PageURL'] = response.url
        locations['Name'] = location_name
        locations['PhysicianID'] = physician_id
        locations['Address'] = full_address
        # locations['Street'] = street
        # locations['Number'] = zip_code
        # locations['City'] = city
        locations['email'] = ', '.join(email).encode('utf-8')
        locations['Phone'] = ', '.join(phone)
        locations['Website'] = ', '.join(website).encode('utf-8')
        locations['State'] = self.state_name

        return locations

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
