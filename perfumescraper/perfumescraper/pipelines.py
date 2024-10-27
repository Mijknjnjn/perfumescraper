# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
from turtledemo.paint import switchupdown

# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from perfumescraper.items import PerfumeVariant
import re


class PerfumescraperPipeline:
    def process_item(self, item, spider):

        adapter = ItemAdapter(item)
        variant_list = adapter.get('variants')
        giftset_list = adapter.get('giftsets')

        ## REMOVE ALL USELESS WHITESPACES
        for field_name in adapter.field_names():
            value = adapter.get(field_name)
            ## Remove whitespace from strings
            if isinstance(value, str):
                adapter[field_name] = value.strip()
            ## Remove whitespace from perfume variants
            elif isinstance(value, list):
                cleaned_variants = []
                for variant in value:
                    variant_adapter = ItemAdapter(variant)
                    for k, v in variant_adapter.items():
                        if isinstance(v, str):
                            variant_adapter[k] = v.strip()
                    cleaned_variants.append(variant_adapter.item)
                adapter[field_name] = cleaned_variants
            ## Remove whitespace from gift sets
            elif field_name == "giftsets" and isinstance(value, list):
                cleaned_giftsets = []
                for giftset in value:
                    giftset_adapter = ItemAdapter(giftset)
                    for k, v in giftset_adapter.items():
                        if isinstance(v, str):
                            giftset_adapter[k] = v.strip()
                    cleaned_giftsets.append(giftset_adapter.item)
                adapter["giftsets"] = cleaned_giftsets

        ## Sex -> normalization of output
        sex_string = adapter.get('sex')
        if sex_string is not None:
            if sex_string == 'Sex Sex--male':
                adapter['sex'] = 'M'
            if sex_string == 'Sex Sex--female':
                adapter['sex'] = 'W'
            if sex_string == 'Sex Sex--unisex':
                adapter['sex'] = 'U'
            if sex_string == 'Sex Sex--children':
                adapter['sex'] = 'K'

        ## Name -> removes brand name from perfume name
        brand_string = adapter.get('brand')
        name_string = adapter.get('name')
        if name_string.startswith(brand_string):
            adapter['name'] = name_string[len(brand_string):].strip()

        ## Variants -> price, price_old -> removing any string (€) and conevrting from string to float
        for variant in variant_list:
            variant_adapter = ItemAdapter(variant)
            price = variant_adapter.get('price')
            if price is not None:
                variant_adapter['price'] = float(price.replace(' €', '').replace(',', '.'))
            else:
                variant_adapter['price'] = None
            price_old = variant_adapter.get('price_old')
            if price_old is not None:
                variant_adapter['price_old'] = float(price_old.replace(' €', '').replace(',', '.'))
            else: variant_adapter['price_old'] = None

        ## Giftsets -> price, price_old -> removing any string (€) and coneverting from string to float
        ## Giftsets -> name -> remove '\n' in name and replace multiple whitespaces with just sigle one
        for giftset in giftset_list:
            giftset_adapter = ItemAdapter(giftset)
            price = giftset_adapter.get('price')
            if price is not None:
                giftset_adapter['price'] = float(price.replace(' €', '').replace(',', '.'))
            else:
                giftset_adapter['price'] = None
            price_old = giftset_adapter.get('price_old')
            if price_old is not None:
                giftset_adapter['price_old'] = float(price_old.replace(' €', '').replace(',', '.'))
            else:
                giftset_adapter['price_old'] = None
            name = giftset_adapter.get('name')
            if name is not None:
                giftset_adapter['name'] = re.sub(r'\s+', ' ', name).strip()

        ## Category -> normalizing category naming
        category = adapter.get('category')
        match category:
            case 'Parfumy':
                adapter['category'] = 'Perfumes'
            case 'Parfumové extrakty':
                adapter['category'] = 'Perfume Extracts'

        return item


import mysql.connector


class SaveToDatabase:

    def __init__(self):
        self.connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root',
            database='perfumescraper'
        )

        self.cursor = self.connection.cursor()

    def process_item(self, item, spider):
        self.cursor.execute("""INSERT IGNORE INTO PerfumeCategory(Name) VALUES (%s)""", (
            item['category'],))
        self.cursor.execute("""SELECT ID_PerfumeCategory FROM PerfumeCategory WHERE Name = %s""", (
            item['category'],))
        category_id = self.cursor.fetchone()[0]

        self.cursor.execute("""INSERT IGNORE INTO PerfumeBrand(Name) VALUES (%s)""", (
            item['brand'],))
        self.cursor.execute("""SELECT ID_PerfumeBrand FROM PerfumeBrand WHERE Name = %s""", (
            item['brand'],))
        brand_id = self.cursor.fetchone()[0]

        self.cursor.execute(
            """INSERT IGNORE INTO Perfume (ID_PerfumeCategory, ID_PerfumeBrand, Name, Sex) VALUES (%s, %s, %s, %s)""",
            (category_id, brand_id, item['name'], item['sex']))
        self.cursor.execute("""SELECT ID_Perfume FROM Perfume WHERE Name = %s""", (item['name'],))
        perfume_id = self.cursor.fetchone()[0]

        for variant in item.get('variants', []):
            self.cursor.execute(
                """INSERT IGNORE INTO PerfumeVariant(ID_Perfume, Description, URL, Type) VALUES (%s, %s, %s, %s)""",
                (perfume_id, variant['description'], variant['url'], 0))
            self.cursor.execute("""SELECT ID_PerfumeVariant FROM PerfumeVariant WHERE URL = %s""", (variant['url'],))
            variant_id = self.cursor.fetchone()[0]

            self.cursor.execute(
                """INSERT IGNORE INTO PerfumeHistory(ID_PerfumeVariant, Price, Price_old, Available) VALUES (%s, %s, %s, %s)""",
                (variant_id, variant['price'], variant['price_old'], variant['available']))

        for set in item.get('giftsets', []):
            self.cursor.execute(
                """INSERT IGNORE INTO PerfumeVariant(ID_Perfume, Description, URL, Type) VALUES (%s, %s, %s, %s)""",
                (perfume_id, set['description'], set['url'], 1))
            self.cursor.execute("""SELECT ID_PerfumeVariant FROM PerfumeVariant WHERE URL = %s""", (set['url'],))
            set_id = self.cursor.fetchone()[0]

            self.cursor.execute(
                """INSERT INTO PerfumeHistory(ID_PerfumeVariant, Price, Price_old, Available) VALUES (%s, %s, %s, %s)""",
                (set_id, set['price'], set['price_old'], set['available']))

        self.connection.commit()
        return item

    def close_spider(self, spider):
        self.cursor.close()
        self.connection.close()
