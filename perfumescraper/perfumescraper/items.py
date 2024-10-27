# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PerfumescraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


class PerfumeItem(scrapy.Item):
    """
    Represents a scraped perfume item.

    Attributes:
        brand (str): The brand of the perfume.
        name (str): The specific name of the perfume product.
        sex (str): The target audience for the perfume:
                   'M' - male,
                   'F' - female,
                   'U' - unisex,
                   'K' - children.
        category (str): The category of the perfume.
        variants (list of PerfumeVariant): A list of `PerfumeVariant` objects, representing the different size, price, and availability variants for this perfume.
        giftsets (list of GiftSet): A list of `GiftSet` objects, representing available gift sets for this perfume.
    """
    brand = scrapy.Field()
    name = scrapy.Field()
    sex = scrapy.Field()
    category = scrapy.Field()
    variants = scrapy.Field()
    giftsets = scrapy.Field()

class PerfumeVariant(scrapy.Item):
    """
    Represents a variant of a perfume.

    Attributes:
        description (str): The description of the parfume.
        price (float): The current price of the perfume.
        price_old (float): The old price of the perfume, if it is discounted.
        available (str): Availability of the perfume. ('Y' - in stock, 'N' - not in stock)
        url (str): URL to the product page.
    """
    description = scrapy.Field()
    price = scrapy.Field()
    price_old = scrapy.Field()
    available = scrapy.Field()
    url = scrapy.Field()

class GiftSet(scrapy.Item):
    """
    Represents a collection of gift sets for specific perfume.

    Attributes:
        name (string): The name of the gift set.
        description (string): The description of the gift set.
        price (float): The current price of the gift set.
        price_old (float): The old price of the gift set, if it is discounted.
        available (str): Availability of the gift set. ('Y' - in stock, 'N' - not in stock)
        url (str): URL to the product page.
    """
    name = scrapy.Field()
    description = scrapy.Field()
    price = scrapy.Field()
    price_old = scrapy.Field()
    available = scrapy.Field()
    url = scrapy.Field()
