#! ./venv/bin/python

import json
import math
import os
import pprint
import shutil
from copy import copy
from datetime import datetime

import requests

from util.parse_categories import ParseCategories


class SaveOnScraper:

    user_id = 'd1f2c2de-9677-449b-a3ff-0c04bd374664'

    item_properties = ["Brand", "Name", "Category", "CurrentPrice", "RegularPrice", "Size",
                       "CurrentUnitPrice", "Description", "Sku", "Sale"]

    item_property_map = {"Brand": "brand", "Name": "name", "Category": "category", "CurrentPrice": "current_price",
                         "RegularPrice": "regular_price", "Size": "size", "CurrentUnitPrice": "current_unit_price",
                         "Description": "description", "Sku": "sku", "Sale": "sale"}

    auth_key_len = 0
    item_query_quantity = 0
    num_of_cats = 0
    num_completed = 0
    item_count = 0

    base_link = ''
    base_link_api = ''
    auth_link = ''
    data_link = ''

    _headers = {}
    remap_data = ''

    log_prefix = '[Save-On Scraper]: '

    json_file_data = []
    multi_data_file = False
    sub_cat_finished = False

    startTime = ''
    last_category = False

    def __init__(self):

        self.startTime = datetime.now()

        self.auth_key_len = 37
        self.item_query_quantity = 20

        self.base_link = 'https://shop.saveonfoods.com/store/7C561153#/category/'
        self.base_link_api = 'https://shop.saveonfoods.com/api/product/v7/products/category/'
        self.auth_link = '{0}579,674/butter%20%26%20margarine/1?queries=sort%3DBrand'.format(self.base_link)
        self.data_link = 'https://shop.saveonfoods.com/api/product/v7/' \
                         'categories/store/7C561153?userId=d1f2c2de-9677-449b-a3ff-0c04bd374664'

        self._headers = {'Authorization': self.get_auth_key(self.auth_link),
                         'Accept': 'application/vnd.mywebgrocer.grocery-list+json'}

        save_on_data = self.get_all_data()
        save_on_data, self.remap_data = ParseCategories().parse_json(save_on_data)

        self.scrape_data(save_on_data)

    def get_all_data(self):
        _headers = copy(self._headers)
        _headers['Accept'] = 'application/vnd.mywebgrocer.category-tree+json'
        r = requests.get(self.data_link, headers=_headers)
        _json_str = r.json()

        return _json_str

    def scrape_data(self, save_on_data):
        cwd = os.getcwd()
        data_path = '{0}/save-on-data/'.format(cwd)

        rename_map = self.remap_data

        if not os.path.exists(data_path):
            os.makedirs(data_path)

        for category in save_on_data:
            category_name = category['category']
            sub_categories = category['all_sub_cats']

            cn = category_name.replace(' ', '_')
            cn = cn.replace('/', '_')
            cn = cn.replace('&', 'and')

            category_path = data_path + cn

            if not os.path.exists(category_path):
                os.makedirs(category_path)
            else:
                shutil.rmtree(category_path)
                os.makedirs(category_path)

            print('\n{0}[MAIN] {1}'.format(self.log_prefix, category_name))
            print('{0}-------------------------------------------'.format(self.log_prefix))

            num_main_sub_cats_completed = 1
            for sub_cat in sub_categories:

                self.json_file_data = []

                print('{0}Category: \'{1}\''.format(self.log_prefix, sub_cat))

                file_name = '{0}.json'.format(rename_map[sub_cat])
                file_path = '{0}{1}/{2}'.format(data_path, cn, file_name)

                self.num_of_cats = 0
                self.num_completed = 0

                for cat_id, sub_cat_name in category['remap_sub_cats'].items():
                    if sub_cat_name == sub_cat:
                        self.num_of_cats += 1

                for cat_id, sub_cat_name in category['remap_sub_cats'].items():

                    self.item_count = 0

                    if sub_cat_name == sub_cat:
                        self.num_completed += 1
                        product_category = cat_id

                        if category is save_on_data[-1]:
                            if cat_id == 1437:
                                self.last_category = True

                        if self.num_of_cats == self.num_completed:
                            self.multi_data_file = False
                        else:
                            self.multi_data_file = True

                        url = "{0}{2}/store/7C561153?sort=Brand&take=20&userId={1}".format(self.base_link_api,
                                                                                           self.user_id,
                                                                                           product_category)

                        data = self.print_data(self._headers, 1, url)
                        page_numbers = self.get_page_numbers(data)

                        # Set page_numbers to 1 for low data set testing
                        # page_numbers = 1

                        if page_numbers > 1:
                            for item in self.print_data(self._headers, page_numbers, url):
                                data["Items"].append(item)

                        self.build_product_export(data, file_path, file_name, self.multi_data_file)

                num_main_sub_cats_completed += 1

    def get_page_numbers(self, data):
        item_count = data["ItemCount"]
        self.item_count = item_count
        num_of_pages = math.ceil(item_count / self.item_query_quantity)

        return num_of_pages

    def build_product_export(self, product_data, file_path, file_name, multi_data_file):

        for item in product_data["Items"]:
            new_item = {}
            for _property in self.item_properties:
                if _property != 'Sale':
                    new_item[self.item_property_map[_property]] = item[_property]
                else:
                    if item[_property] is not None:
                        new_item_sale = {
                            "date_text": item[_property]["DateText"],
                            "description": item[_property]["Description2"]
                        }
                    else:
                        new_item_sale = 'false'

                    new_item["sale"] = new_item_sale

            self.json_file_data.append(new_item)

        if not multi_data_file:
            with open(file_path, 'w') as outfile:
                json.dump(self.json_file_data, outfile)

        if self.last_category:
            build_time = datetime.now() - self.startTime
            seconds = build_time.seconds
            print('{0}BUILD SUCCESS'.format(self.log_prefix))
            print('{0}BUILD TIME: {1}'.format(self.log_prefix, self.return_formatted_time(seconds)))

    @staticmethod
    def return_formatted_time(time_seconds):

        if time_seconds >= 60:
            time_minutes = math.floor(time_seconds / 60)
            time_seconds = time_seconds - (time_minutes * 60)
            return '{0}m {1}s'.format(time_minutes, time_seconds)
        else:
            return '0m {0}s'.format(time_seconds)

    def get_auth_key(self, fetch_auth_url):
        print("{0}Generating Auth Key...".format(self.log_prefix))
        r = requests.get(fetch_auth_url)
        h = json.loads(self.fix_headers_string(str(r.headers)))

        set_cookie = h["Set-Cookie"]
        set_cookie = set_cookie.replace('MWG_GSA_S={\'AuthorizationToken\':\'', ' ')
        auth_key = set_cookie[1:self.auth_key_len]

        print("{0}Auth Key Generated!".format(self.log_prefix))
        return auth_key

    @staticmethod
    def fix_headers_string(header_str):
        header_str = header_str.replace('\"', '!~~')
        header_str = header_str.replace('\'', '"')
        header_str = header_str.replace('!~~', '\'')

        return header_str

    def print_data(self, headers, num_of_pages, url):
        data = []
        try:
            for i in range(num_of_pages):
                skip = i * 20
                if i == 0:
                    if num_of_pages > 1:
                        continue
                    else:
                        r = requests.get(url, headers=headers, params={'skip': skip})
                        _json_str = r.json()

                        return _json_str
                else:

                    r = requests.get(url, headers=headers, params={'skip': skip})
                    _json_str = r.json()

                    for item in _json_str["Items"]:
                        data.append(item)

            return data

        except requests.HTTPError:
            self.get_auth_key(self.auth_link)


if __name__ == '__main__':
    SaveOnScraper()
