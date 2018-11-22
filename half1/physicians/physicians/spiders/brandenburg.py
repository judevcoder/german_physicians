# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import logging

from scrapy.spider import BaseSpider
from scrapy.http import Request, FormRequest
from lxml import html

from items import PhysiciansItem, SpecialtiesItem, LocationsItem

sys.path.append(os.path.abspath(os.path.join('../../../..', 'half1')))
from resultpath import result_path


class BrandenburgSpider(BaseSpider):
    logging.basicConfig(
        filename='log.txt',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
    )
    name = 'brandenburg'
    allowed_domains = ['arztsuche.kvbb.de']

    start_urls = ['https://arztsuche.kvbb.de/ases-kvbb/ases.jsf']

    result_path_type = 'half1'

    state = 'Brandenburg'

    item_count = 1

    view_state = None

    filter_type = 'frem'

    frem_count = 0

    frem_ids = None

    zus_count = 0

    show_detail_id = 'arztlisteDataList:{index}:detailsExpandEintrag'

    detail_first = 0

    next_page = True

    out_path = None
    physician_csv = None
    specialty_csv = None
    location_csv = None

    def __init__(self, *args, **kwargs):

        self.out_path = result_path(self.result_path_type, self.name)

        if not os.path.exists(self.out_path):
            os.makedirs(self.out_path)

        self.physician_csv = self.out_path + self.name + '_physician.csv'
        self.specialty_csv = self.out_path + self.name + '_specialty.csv'
        self.location_csv = self.out_path + self.name + '_location.csv'

        super(BrandenburgSpider, self).__init__(site_name=self.allowed_domains[0], *args, **kwargs)
        self.current_page = 0

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse_start_page, dont_filter=True)

    def parse_start_page(self, response):
        try:
            view_state = response.xpath('//input[@name="javax.faces.ViewState"]/@value').extract()[0].encode('utf-8')
            self.view_state = view_state
        except:
            print("Can't find view state")
            view_state = self.view_state

        start_form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'asesInputForm:j_idt279',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            'asesInputForm:j_idt279': 'asesInputForm:j_idt279',
            'asesInputForm': 'asesInputForm',
            'asesInputForm:searchCriteria': '',
            'javax.faces.ViewState': view_state
        }
        yield FormRequest(
            url=self.start_urls[0],
            formdata=start_form_data,
            # headers=self.headers,
            callback=self.show_all_praxisor,
            dont_filter=True
        )

    def show_all_praxisor(self, response):
        show_all_praxisor_form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'formErgebnisliste:j_idt314:1:j_idt327',
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            'formErgebnisliste:j_idt314:1:j_idt327': 'formErgebnisliste:j_idt314:1:j_idt327',
            'formErgebnisliste': 'formErgebnisliste',
            'javax.faces.ViewState': self.view_state
        }

        yield FormRequest(
            url=self.start_urls[0],
            formdata=show_all_praxisor_form_data,
            callback=self.filter_potsdam,
            dont_filter=True
        )

    def filter_potsdam(self, response):
        potsdam_id = html.fromstring(html.tostring(html.fromstring(response.body)
                                                   .xpath('//div[@title="Potsdam"][1]/../..')[0])).xpath('//a/@id')[0]
        filter_potsdam_form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': potsdam_id,
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            potsdam_id: potsdam_id,
            'formErgebnisliste': 'formErgebnisliste',
            'javax.faces.ViewState': self.view_state
        }
        yield FormRequest(
            url=self.start_urls[0],
            formdata=filter_potsdam_form_data,
            callback=self.filter_allge_prak,
            dont_filter=True
        )

    def filter_allge_prak(self, response):
        allge_prak_id = 'formErgebnisliste:j_idt314:3:j_idt324:0:j_idt325'
        filter_allge_prak_form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': allge_prak_id,
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            allge_prak_id: allge_prak_id,
            'formErgebnisliste': 'formErgebnisliste',
            'javax.faces.ViewState': self.view_state
        }
        yield FormRequest(
            url=self.start_urls[0],
            formdata=filter_allge_prak_form_data,
            callback=self.parse_by_filter_type,
            dont_filter=True
        )

    def parse_by_filter_type(self, response):
        show_all_id = None
        if self.filter_type == 'frem':
            show_all_id = 'formErgebnisliste:j_idt314:5:j_idt327'
        elif self.filter_type == 'zus':
            show_all_id = 'formErgebnisliste:j_idt314:6:j_idt327'
        form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': show_all_id,
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            show_all_id: show_all_id,
            'formErgebnisliste': 'formErgebnisliste',
            'javax.faces.ViewState': self.view_state
        }
        yield FormRequest(
            url=self.start_urls[0],
            formdata=form_data,
            callback=self.filter_target,
            dont_filter=True
        )

    def filter_target(self, response):
        str_id = None

        if self.filter_type == 'frem':

            frem_ids = html.fromstring(response.body).xpath('//*[contains(text(), "Fremdsprachen")]/../a/@id')

            try:
                str_id = frem_ids[self.frem_count].encode('utf-8')
            except:
                "Starting crawl for Zusatzangebote!"
            if self.frem_count == len(frem_ids):
                self.filter_type = 'zus'
                yield Request(
                    url=response.url,
                    callback=self.parse_start_page,
                    dont_filter=True
                )

        elif self.filter_type == 'zus':
            zus_ids = html.fromstring(response.body).xpath('//*[contains(text(), "Zusatzangebote")]/../a/@id')
            try:
                str_id = zus_ids[self.zus_count].encode('utf-8')
            except:
                print("Crawling Done!")

            if self.zus_count == len(zus_ids):
                return

        form_data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': str_id,
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': 'asesAggregationForm asesResultForm',
            str_id: str_id,
            'formErgebnisliste': 'formErgebnisliste',
            'javax.faces.ViewState': self.view_state
        }

        yield FormRequest(
            url=response.url,
            formdata=form_data,
            callback=self.get_all_items,
            dont_filter=True
        )

    def get_all_items(self, response):

        if self.detail_first == 0:
            detail_elements = html.fromstring(response.body).xpath('//div[@id="arztlisteDataList_content"]/'
                                                                   'div[@class="ases-arzt-eintrag"]')
            for index, element in enumerate(detail_elements):
                detail_id = None
                detail_div_id = self.show_detail_id.format(index=index)
                try:
                    detail_id = element.xpath('//div[@id="%s"]/a/@id' % detail_div_id)[0].encode('utf-8')
                except:
                    print ("Parsing Error")

                if detail_id is None:
                    detail_id = html.fromstring(response.body).xpath('//a[contains(@onclick, "%s")]/@id' % detail_div_id)[0].encode('utf-8')

                partial_render = 'arztlisteDataList:{index}:detailsPanel ' \
                                 'arztlisteDataList:{index}:detailsTabView ' \
                                 'arztlisteDataList:{index}:detailsExpandEintrag ' \
                                 'arztlisteDataList:{index}:detailsCollapseEintrag'
                detail_form_data = {
                    'javax.faces.partial.ajax': 'true',
                    'javax.faces.source': detail_id,
                    'javax.faces.partial.execute': '@all',
                    'javax.faces.partial.render': partial_render.format(index=index),
                    detail_id: detail_id,
                    'oeffnungszeitenDialogForm': 'oeffnungszeitenDialogForm',
                    'javax.faces.ViewState': self.view_state
                }

                meta = response.meta.copy()
                meta['index'] = index
                yield FormRequest(
                    url=response.url,
                    formdata=detail_form_data,
                    meta=meta,
                    callback=self.parse_detail_item,
                    dont_filter=True
                )

            if len(detail_elements) < 10:
                self.next_page = False

            if self.next_page:
                self.detail_first += 10
                yield Request(
                    url=self.start_urls[0],
                    callback=self.parse_start_page,
                    dont_filter=True
                )
            else:
                if self.filter_type == 'frem':
                    self.frem_count += 1
                elif self.filter_type == 'zus':
                    self.zus_count += 1

                yield Request(
                    url=self.start_urls[0],
                    callback=self.parse_start_page,
                    dont_filter=True
                )

        elif self.detail_first > 0:
            next_page_form_data = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'arztlisteDataList',
                'javax.faces.partial.execute': 'arztlisteDataList',
                'javax.faces.partial.render': 'arztlisteDataList',
                'javax.faces.behavior.event': 'page',
                'javax.faces.partial.event': 'page',
                'arztlisteDataList_pagination': 'true',
                'arztlisteDataList_first': str(self.detail_first),
                'arztlisteDataList_rows': '10',
                'oeffnungszeitenDialogForm': 'oeffnungszeitenDialogForm',
                'javax.faces.ViewState': self.view_state
            }

            if self.next_page:
                self.detail_first += 10
                yield FormRequest(
                    url=response.url,
                    formdata=next_page_form_data,
                    callback=self.parse_next_page,
                    dont_filter=True
                )

            else:
                if self.filter_type == 'frem':
                    self.frem_count += 1
                elif self.filter_type == 'zus':
                    self.zus_count += 1

                self.detail_first = 0
                yield Request(
                    url=response.url,
                    callback=self.parse_start_page,
                    dont_filter=True
                )

    def parse_next_page(self, response):
        detail_elements = []
        temp_detail_elements = html.fromstring(response.body).xpath('//a[contains(@class, "ui-commandlink")]')
        for element in temp_detail_elements:
            if 'span' in html.tostring(element):
                detail_elements.append(element)
        if len(detail_elements) < 10:
            self.next_page = False
        for index, element in enumerate(detail_elements):
            detail_div_id = self.show_detail_id.format(index=index)
            detail_id = element.xpath('//div[@id="%s"]/a/@id' % detail_div_id)[0].encode('utf-8')
            partial_render = 'arztlisteDataList:{index}:detailsPanel ' \
                             'arztlisteDataList:{index}:detailsTabView ' \
                             'arztlisteDataList:{index}:detailsExpandEintrag ' \
                             'arztlisteDataList:{index}:detailsCollapseEintrag'
            detail_form_data = {
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': detail_id,
                'javax.faces.partial.execute': '@all',
                'javax.faces.partial.render': partial_render.format(index=index),
                detail_id: detail_id,
                'oeffnungszeitenDialogForm': 'oeffnungszeitenDialogForm',
                'javax.faces.ViewState': self.view_state
            }
            meta = response.meta.copy()
            meta['index'] = index
            yield FormRequest(
                url=response.url,
                formdata=detail_form_data,
                meta=meta,
                callback=self.parse_detail_item,
                dont_filter=True
            )

        if self.next_page:
            yield Request(
                url=response.url,
                callback=self.parse_start_page,
                dont_filter=True
            )
        else:
            yield Request(
                url=response.url,
                callback=self.get_all_items,
                dont_filter=True
            )

    def parse_detail_item(self, response):
        parse_items = []
        physicians = PhysiciansItem()
        specialties = SpecialtiesItem()
        locations = LocationsItem()

        try:
            json_data = json.loads(html.fromstring(response.body).xpath('//input/@data-leistungsort-json')[0])
            full_name = self._clean_text(json_data.get('name')).encode('utf-8')
            first_name = full_name.split(' ')[-2]
            last_name = full_name.split(' ')[-1]
            phone = json_data.get('telefon').encode('utf-8')

            remarks = None
            specialities_val = []
            speciality = json_data.get('fachgebiet')
            if speciality:
                specialities_val.append(speciality.encode('utf-8'))
            speciality_titles = html.fromstring(response.body).\
                xpath('//li[contains(@class, "ases-multiline-text")]/b/text()')
            speciality_values = html.fromstring(response.body). \
                xpath('//li[contains(@class, "ases-multiline-text")]/text()')
            if len(speciality_titles) > 0:
                for i, title in enumerate(speciality_titles):
                    if u'Zusatzvertr\xe4ge:' in title:
                        val = self._clean_text(speciality_values[i * 2 + 1])
                        specialities_val.append(val)
                    elif 'Zusatzbezeichnungen' in title:
                        remarks = self._clean_text(speciality_values[i * 2 + 1])

            address = html.fromstring(response.body).xpath('//div[@class="ases-leistungsort-kontaktdaten"]/ul/li/text()')
            location_name = self._clean_text(address[1]).encode('utf-8')
            street = self._clean_text(address[2]).encode('utf-8')
            city = self._clean_text(address[3]).split()[1].encode('utf-8')
            postal_code = self._clean_text(address[3]).split()[0]
            full_address = street + ', ' + postal_code + ' ' + city + ', Germany'

            physicians['URL'] = response.url
            physicians['GeneratedID'] = self.item_count
            physicians['SitePrimaryKey'] = self.item_count
            physicians['Fullname'] = full_name
            physicians['FirstName'] = first_name
            physicians['LastName'] = last_name
            physicians['StateName'] = self.state
            physicians['remarks'] = remarks

            specialties['PhysicianPrimaryID'] = self.item_count
            specialties['SpecialtyName'] = ', '.join(specialities_val)

            locations['LocationID'] = self.item_count
            locations['PhysicianID'] = self.item_count
            locations['Name'] = location_name
            locations['PageURL'] = response.url
            locations['Address'] = full_address
            # locations['Street'] = street
            # locations['City'] = city
            # locations['Number'] = postal_code
            locations['Phone'] = phone
            locations['State'] = self.state

            parse_items.append(physicians)
            parse_items.append(specialties)
            parse_items.append(locations)

            self.item_count += 1

            for parse_item in parse_items:
                yield parse_item

        except:
            print ("Not Found Response!")

    @staticmethod
    def _clean_text(text):
        text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
        text = re.sub("&nbsp;", " ", text).strip()

        return re.sub(r'\s+', ' ', text)
