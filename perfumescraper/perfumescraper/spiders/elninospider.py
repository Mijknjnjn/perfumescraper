from asyncio import timeout
from typing import Iterable

import scrapy
from perfumescraper.items import PerfumeItem, PerfumeVariant, GiftSet
from scrapy import Request
from scrapy_playwright.page import PageMethod
from unicodedata import category


class ElninospiderSpider(scrapy.Spider):
    name = 'elninospider'
    max_retries = 3

    def start_requests(self):
        url = 'https://www.parfemy-elnino.sk/parfumy/?c=324&page=1'
        yield scrapy.Request(url,
                             errback=self.errback,
                             meta=dict(
            playwright=True,
            # playwright_include_page=True,
            playwright_page_methods=[
                #PageMethod('wait_for_selector', 'div.ProductList-item.js-tracking-user-event-item', timeout=15000)
                PageMethod('wait_for_selector', 'div.Page', timeout=15000)
            ],
            retry_count=0
        ))

    def parse(self, response):
        # page = response.meta['playwright_page']
        # await page.close()

        count = 0
        x = response.css('a.Paginator-link.Paginator-link--next ::attr(href)').get()

        parfumes = response.css('div.ProductList-item.js-tracking-user-event-item')
        print('Items - ' + str(len(parfumes)))
        for parfume in parfumes:

            sex = parfume.css('div.ProductCard div.ProductCard-content h3.ProductCard-title a i ::attr(class)').get()

            ## Skip sets of products because they are always listed as variants of another product
            is_set = parfume.css('div.ProductCard div.ProductCard-content span.ProductCard-productsNumber').get()
            if is_set is not None:
                count = count + 1
                continue

            #print(parfume.css('div.ProductCard div.ProductCard-content h3 span.ProductCard-baseName ::text').get())


            ## Get product URL autistic devs storing it in 2 different attributes randomly
            parfume_url = 'https://www.parfemy-elnino.sk' + parfume.css('::attr(href)').get()
            if 'schema.org' in parfume_url:
                parfume_url = 'https://www.parfemy-elnino.sk' + parfume.css('::attr(data-href)').get()
            #print(parfume_url)
            yield scrapy.Request(parfume_url, meta=dict(
                playwright=True,
                #playwright_include_page=True,
                playwright_page_methods=[
                   # PageMethod('wait_for_selector','div#product-variants div div#template-container_product-detail_variants-in-stock div.js-product-variant-container.js-discount-prices-container', timeout=15000)
                    PageMethod('wait_for_selector', 'div.Page', timeout=15000)
                ],
                sex=sex,
                x=x,
                retry_count=0,
            ),
                                 errback=self.errback,
                                 callback=self.parse_parfume_page,
                                 )

        ##Goes thru every product page on site
        next_page = response.css('a.Paginator-link.Paginator-link--next ::attr(href)').get()
        if next_page is not None:
            next_page_url = 'https://www.parfemy-elnino.sk/parfumy/' + next_page
            yield scrapy.Request(next_page_url,
                                 errback=self.errback,
                                 meta=dict(
                playwright=True,
                #playwright_include_page=True,
                playwright_page_methods=[
                    #PageMethod('wait_for_selector', 'div.ProductList-item.js-tracking-user-event-item', timeout=15000)
                    PageMethod('wait_for_selector', 'div.Page', timeout=15000)
                ],
                retry_count=0,
            ))

    def parse_parfume_page(self, response):
        # page = response.meta['playwright_page']
        # await page.close()

        perfume_item = PerfumeItem()
        perfume_item['category'] = response.xpath(
            "//div[@class='u-textTruncate' and @data-snippet-id='breadcrumb']/a[position()=4]/text()").get()
        perfume_item['brand'] = response.xpath(
            "//div[@class='u-textTruncate' and @data-snippet-id='breadcrumb']/a[position()=5]/text()").get()
        perfume_item['name'] = response.css('div#template-container_product-detail_title-addon div h1 ::text').get()
        perfume_item['sex'] = response.meta.get('sex')

        # name = response.css('div#template-container_product-detail_title-addon div h1 ::text').get()
        #
        # print(name)

        variants = []
        giftsets = []

        variants_available = response.css('div#product-variants div div#template-container_product-detail_variants-in-stock div.js-product-variant-container.js-discount-prices-container')
        ## Loop goes thru variants that are available
        for variant in variants_available:
            ## Old price is sometimes in <span>, sometimes in <a>
            price_old = variant.css('div div.ProductRow-prices span.Price--old a.Price-retail ::text').get()
            if price_old is None:
                price_old = variant.css('div div.ProductRow-prices span.Price--old ::text').get()
            if price_old is not None and price_old.strip() == '':
                price_old = variant.css('div div.ProductRow-prices span.Price--old span.Price-retail ::text').get()

            description = variant.css('div div.ProductRow-titleWrap h3 a span strong ::text').get()
            if description == 'Set':
                Set_item = GiftSet()
                Set_item['name'] = description
                Set_item['description'] = variant.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3 a span.ProductRow-titleDescription span.ProductRow-titleDescriptionContent  ::text').get()
                Set_item['price'] = variant.css(
                    'div div.ProductRow-prices span.Price.ProductRow-price.js-price ::text').get()
                Set_item['price_old'] = price_old
                Set_item['url'] = 'https://www.parfemy-elnino.sk' + variant.css(
                    'div div.ProductRow-titleWrap h3 a ::attr(href)').get()
                giftsets.append(Set_item)
                continue

            variant_item = PerfumeVariant()
            variant_item['description'] = description
            variant_item['price'] = variant.css('div div.ProductRow-prices span.Price.ProductRow-price.js-price ::text').get()
            variant_item['price_old'] = price_old
            variant_item['available'] = 1
            variant_item['url'] = 'https://www.parfemy-elnino.sk' + variant.css('div div.ProductRow-titleWrap h3 a ::attr(href)').get()
            variants.append(variant_item)

        giftsets_available = response.css('div#product-variants div#template-container_product-detail_variants-gift-boxes div.js-product-variant-container.js-discount-prices-container')

        ## Loops trhu gift sets that are in stock
        for giftset in giftsets_available:
            ## Get old price of gift set (night be storen in 2 ways)
            price_old = giftset.css('div.ProductRow.ProductRow--variant div.ProductRow-prices span.Price--old ::text').get()
            if price_old is None:
                price_old = giftset.css('div.ProductRow.ProductRow--variant div.ProductRow-prices span.Price--old span.Price-retail ::text').get()

            giftset_item = GiftSet()
            giftset_item['name'] = giftset.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3.ProductRow-title a span.ProductRow-titleMain strong ::text').get()
            giftset_item['description'] = giftset.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3.ProductRow-title a span.ProductRow-titleDescription span.ProductRow-titleDescriptionContent ::text').get()
            giftset_item['price'] = giftset.css('div.ProductRow.ProductRow--variant div.ProductRow-prices span.Price.ProductRow-price.js-price ::text').get()
            giftset_item['price_old'] = price_old
            giftset_item['available'] = 1
            giftset_item['url'] = 'https://www.parfemy-elnino.sk' + giftset.css('div.ProductRow--variant div.ProductRow-titleWrap h3.ProductRow-title a ::attr(href)').get()
            giftsets.append(giftset_item)

        variants_not_in_stock = response.css('div#product-variants div#product-variants-not-in-stock div.Toggle-content.js-toggle-element div#template-container_product-detail_variants-not-in-stock div.js-product-variant-container')
        ## Loop for variants not in stock
        for variant in variants_not_in_stock:

            size = variant.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3 a span strong ::text').get()
            ## Loop for all gift sets that are not in stock
            if 'Darčeková kazeta' in size:
                giftset_item = GiftSet()
                giftset_item['name'] = size
                giftset_item['description'] = variant.css('div.ProductRow--variant div.ProductRow-titleWrap h3 a span.ProductRow-titleDescription span.ProductRow-titleDescriptionContent ::text').get()
                giftset_item['available'] = 0
                giftset_item['url'] = 'https://www.parfemy-elnino.sk' + variant.css('div.ProductRow--variant div.ProductRow-titleWrap h3 a ::attr(href)').get()
                giftsets.append(giftset_item);
                continue

            variant_item = PerfumeVariant()
            variant_item['description'] = variant.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3 a span strong ::text').get()
            variant_item['available'] = 0
            variant_item['url'] = 'https://www.parfemy-elnino.sk' + variant.css('div.ProductRow.ProductRow--variant div.ProductRow-titleWrap h3 a ::attr(href)').get()
            variants.append(variant_item)

        perfume_item['variants'] = variants
        perfume_item['giftsets'] = giftsets
        #print(perfume_item)
        yield perfume_item

    def errback(self, failure):
        # page = failure.meta['playwright_page']
        # await page.close()
        error_message = failure.getErrorMessage()
        print(f"Error occurred: {error_message}")
        request = failure.request
        retry_count = request.meta.get('retry_count', 0)
        if retry_count < self.max_retries:
            retry_count += 1
            print(f"Retrying {request.url} (Retry {retry_count}/{self.max_retries})")

            retry_req = request.copy()
            retry_req.meta['retry_count'] = retry_count
            retry_req.dont_filter = True
            yield retry_req
        else:
            print(f"Max retries reached for {request.url}")

