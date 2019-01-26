#! ./venv/bin/python
import json
from copy import copy


class ParseCategories:

    sub_cat_id_map = {}
    sub_cat_false_ids = []
    all_sub_categories = []
    new_categories = {}
    category_directory_rename = {}

    def __init__(self):
        print('[Save-On Scraper] Parsing Save-On Data JSON')

    def clear_static(self):
        self.sub_cat_id_map = {}
        self.sub_cat_false_ids = []
        self.all_sub_categories = []
        self.new_categories = {}

    def check_sub_categories(self, sub_cat_arr, parent_ids):
        new_sub_cat_arr = []
        valid_sub_cats = []
        i = 0
        x = 0

        # TODO Explain this shit
        for sub_cat in sub_cat_arr:
            new_sub_cat_arr.append({"id": sub_cat["Id"], "name": sub_cat["Name"], 'parent_ids': parent_ids})
            self.sub_cat_id_map[sub_cat['Id']] = sub_cat['Name']
            if not sub_cat["Subcategories"]:
                new_sub_cat_arr[i]['sub_cat'] = False
                self.sub_cat_false_ids.append({'name': sub_cat['Name'], 'id': sub_cat['Id'], 'pid': parent_ids})
            else:
                new_sub_cat_arr[i]['sub_cat'] = True
                valid_sub_cats.append(sub_cat['Subcategories'])
            i += 1

        if len(valid_sub_cats) != 0:
            for cat in new_sub_cat_arr:
                if cat['sub_cat']:
                    new_parent_ids = copy(parent_ids)
                    new_parent_ids.append(cat['id'])

                    cat['sub_cat'] = self.check_sub_categories(valid_sub_cats[x], new_parent_ids)
                    x += 1

        return new_sub_cat_arr

    def category_directory_rename_map(self, all_sub_categories):
        for name in all_sub_categories:
            new_name = name
            new_name = new_name.replace(' ', '_')
            new_name = new_name.replace('&', 'and')
            new_name = new_name.replace('-', '_')
            new_name = new_name.replace('/', '_and_')

            self.category_directory_rename[name] = new_name

    def create_export_category(self):
        # Loop through all categories where there were no sub categories
        # This means we're at a base level category from where we want to scrape the web data
        for false_id in self.sub_cat_false_ids:
            # pid = Parent ID
            pid = false_id['pid']
            # The sub categories go multiple levels down from the main category (dairy, bakery, meat, etc)
            # Dairy breaks up into 'butter, cheese, dips, eggs, milk, etc
            # The following block negates the multi leveling and forces it into a single category (e.g. Dairy)

            # 1 pid = single level of categorization (e.g. Dairy -> Butter -> Product)
            # where Butter is the single level category, and Dairy is the main category

            # > 1 pid = Multiple levels (e.g. Dairy -> Cheese -> Packaged Cheese -> Product)
            # There are 2 different category levels outside of Dairy, so we change the product
            # category to Cheese, instead of Packaged Cheese
            if len(pid) > 1:
                # sub_cat_id_map maps sub categories to IDs
                # Here we take the second pid value to get the first level sub category we want
                # Above example: pid[0] = Dairy, pid[1] = Cheese
                product_category = self.sub_cat_id_map[pid[1]]
                self.new_categories[false_id['id']] = product_category

                # Allows us to separate our individual first level sub categories
                if product_category not in self.all_sub_categories:
                    self.all_sub_categories.append(product_category)
            else:
                # If pid = 1, that means there was only one level
                # of categorization on that specific sub category
                self.new_categories[false_id['id']] = false_id['name']
                if false_id['name'] not in self.all_sub_categories:
                    self.all_sub_categories.append(false_id['name'])

    def create_export_data(self, cat):

        self.create_export_category()
        self.category_directory_rename_map(self.all_sub_categories)

        new_data = {
            'category': cat['Name'],
            'category_id': cat["Id"],
            'remap_sub_cats': self.new_categories,
            'all_sub_cats': self.all_sub_categories
        }

        return new_data

    def parse_json(self, save_on_data):
        end_data = []

        # Build new category data
        for cat in save_on_data:
            self.check_sub_categories(cat["Subcategories"], [cat['Id']])
            new_data = self.create_export_data(cat)
            end_data.append(new_data)
            self.clear_static()

        return end_data, self.category_directory_rename
