# -*- coding: utf-8 -*-
#==============================================================================
#title           :search_products.py
#description     :A spider to scrape etsy.com products based on a search string.
#author          :Patrick Alves (cpatrickalves@gmail.com)
#updated by      :Qin Liu (eeliuqin@gmail.com)
#last Update     :09-28-2022
#usage           :scrapy crawl search_products -a search='animal succulent planter' -a total_page_count=2 -a start_page=1 -o sample-search-products.csv
#python version  :3.6
#==============================================================================


import scrapy
import os
import sys
import csv
import glob
import json
from scrapy.http import Request
from etsy.items import ProductItem
from scrapy.loader import ItemLoader

# Spider Class
class ProductsSpider(scrapy.Spider):
    # Spider name
    name = 'search_products'
    allowed_domains = ['etsy.com']
    start_urls = ['https://www.etsy.com/']

    # Default number of pages to scrapy
    TOTAL_PAGE_COUNT = 10

    # Number of products per page of search results
    PRODUCTS_CNT_PER_PAGE = 12

    # Count the number of items scraped
    COUNTER = 0

    # Start page number
    START_PAGE = 1

    # Get only the products URLs
    URLS_ONLY = False

    # Number of reviews per page in reviews section
    REVIEWS_CNT_PER_PAGE = 4


    def __init__(self, search, total_page_count=1, urls_only=False, start_page=1, *args, **kwargs):
        if search:
            # Build the search URL
            # With start_page, we can start from the last blocked page
            self.start_urls = [f'https://www.etsy.com/search?q={search}&ref=pagination&page={start_page}']
            # Set the maximum number of pages
            if total_page_count:
                self.TOTAL_PAGE_COUNT = int(total_page_count)

            if start_page:
                self.START_PAGE = int(start_page)

            # Get only the products URLs
            self.URLS_ONLY = bool(urls_only)

        super(ProductsSpider, self).__init__(*args, **kwargs)


    # Parse the first page result and go to the next page
    def parse(self, response):
        c_page = int(response.url.split('=')[-1])
        print(f"parse url {response.url}, page number: {c_page}")

        # Get the list of products from html response
        products_list = response.xpath('//div[@data-search-results=""]/div//li//a[contains(@class, "listing-link")]/@href').extract()
        products_id_list = [product_href.split("/")[4] for product_href in products_list]


        print(f"#### FOUND {len(products_id_list)} PRODUCTS")

        if self.URLS_ONLY: # Get the url without go to the product page
            for product_id in products_id_list:

                # Create the ItemLoader object that stores each product information
                l = ItemLoader(item=ProductItem(), response=response)

                product_url = f'https://www.etsy.com/listing/{product_id}'
                l.add_value('url', product_url)
                yield l.load_item()

        else: # Go to the product's page to fetch price/title/ratings
            for product_id in products_id_list:
                product_url = f'https://www.etsy.com/listing/{product_id}'
                
                yield scrapy.Request(product_url, callback=self.parse_product, dont_filter=True)

        # Stops if already scraped TOTAL_PAGE_COUNT pages
        # Otherwise go to the next page
        if c_page - self.START_PAGE < self.TOTAL_PAGE_COUNT - 1:
            next_page_number = c_page + 1
            next_page_url = '='.join(response.url.split('=')[:-1]) + '=' + str(next_page_number)

            # If the current list is not empty
            if len(products_id_list) > 0:
                yield scrapy.Request(next_page_url)


    # Get the HTML from product's page and get the data
    def parse_product(self, response):
        # Get the product ID (ex: 666125766)
        product_id = response.url.split('/')[4]
        # c_page = int(response.url.split('=')[-1])
        print(f"parse_product() for product {product_id}")

        # Stops if the COUNTER reaches the maximum set value
        if self.COUNTER >= self.TOTAL_PAGE_COUNT * self.PRODUCTS_CNT_PER_PAGE:
            print("max count reached")
            raise scrapy.exceptions.CloseSpider(reason='Max count reached - {} items'.format(self.COUNTER))

        # Check if the product is available
        no_available_message = response.xpath('//h2[contains(text(), "Darn")]')
        if no_available_message:
            print("the product is not available")
            return []

        # Create the ItemLoader object that stores each product information
        l = ItemLoader(item=ProductItem(), response=response)

        l.add_value('product_id', product_id)

        # Get the produc Title
        l.add_xpath('title', '//meta[@property="og:title"]/@content')

        # Get the product price
        l.add_xpath('price', '//div[contains(@data-buy-box-region, "price")]//p//text()', re='(\d+(?:\.\d+)?)')

        # Get the product URL (ex: www.etsy.com/listing/666125766)
        l.add_value('url', '/'.join(response.url.split('/')[2:5]))

        # # ========== Start: QL comment out, feel free to add them back ==========
        # # Get the product description
        # l.add_xpath('description', '//div[@data-id="description-text"]/div/p/text()')

        # # Get each product option and save in a list
        # product_options = []
        # product_options_list = response.xpath('//*[contains(@id, "inventory-variation-select")]')
        # for options in product_options_list:
        #     # Get list of options
        #     temp_list = options.xpath('.//text()').extract()
        #     # Remove '\n' strings
        #     temp_list = list(map(lambda s: s.strip(), temp_list))
        #     # Remove empty strings ('')
        #     temp_list = list(filter(lambda s: s != '', temp_list))

        #     # Filter the 'Quantity' option
        #     if temp_list[0] != '1':
        #         # Create the final string:
        #         # example: "Select a color: White, Black, Red, Silver"
        #         product_options.append(temp_list[0] +': ' + ', '.join(temp_list[1:]))

        # # Separate each option with a | (pipe) symbol
        # l.add_value('product_options', '|'.join(product_options))

        # QL: it's actually store rating, not product rating
        # l.add_xpath('rating', '//a[@href="#reviews"]//input[@name="rating"]/@value')

        # # Get the number of votes (number of reviews)
        # l.add_xpath('number_of_reviews', '//button[@id="same-listing-reviews-tab"]/span/text()')

        # # Count the number of product images
        # images_sel = response.xpath('//ul[@data-carousel-pagination-list=""]/li/img/@data-src-delay').extract()
        # l.add_value('count_of_images', len(images_sel))
        # l.add_value('images_urls', images_sel)

        # l.add_xpath('base_image_url', '//img[contains(@data-carousel-first-image, "")]/@src')

        # Get the product overview
        # l.add_xpath('overview', '//*[@class="listing-page-overview-component"]//li')
        # # ========== End: QL comment out, feel free to add them back ==========

        # Get the number of people that add the product in favorites
        l.add_xpath('favorited_by', '//a[contains(text(), " favorites")]/text()', re='(\d+)')

        # Get the name of the Store 
        l.add_xpath('store_name', '//div[@id="listing-page-cart"]//span/text()')


        # ============== Start: Product Reviews ==============
        # Spider will create Ajax requests to get reviews in the product's page
        # Only some reviews are for that product, the others are reviews for other products
        # Each page on reviews' section has 4 reviews, change `page` in formdata to go to next page
        ajax_url = "https://www.etsy.com/api/v3/ajax/bespoke/member/neu/specs/reviews"

        # Getting the session cookie
        get_cookie = response.request.headers['Cookie'].split(b';')[0].split(b'=')
        cookies = {get_cookie[0].decode("utf-8"):get_cookie[1].decode("utf-8")}

        # Getting the x-csrf-token
        headers = {'x-csrf-token': response.xpath("//*[@name='_nnc']/@value").extract_first()}

        # Shop Id, e.g., <meta property="og:image" content="https://i.etsystatic.com/33822210/r/il/...">
        shop_id = response.xpath("//*[@property='og:image']/@content").extract_first().split('/')[3]

        formdata = {
            'specs[reviews][]': 'Etsy\Web\ListingPage\Reviews\ApiSpec',
            'specs[reviews][1][listing_id]': product_id,
            'specs[reviews][1][shop_id]': shop_id,
            'specs[reviews][1][render_complete]': 'true',
            'specs[reviews][1][active_tab]': 'same_listing_reviews',
            'specs[reviews][1][should_lazy_load_images]': 'false',
            # the initial page of reviews
            'specs[reviews][1][page]': "1"

        }

        # add needed values to data to re-use them
        data = {'itemLoader':l, 'product_id':product_id, 'ajax_url': ajax_url, 
                'headers':headers, 'cookies':cookies, 'formdata':formdata}

        yield scrapy.FormRequest(ajax_url, headers=headers, cookies=cookies,
                                meta=data, formdata=formdata,
                                callback=self.parse_ajax_response)
        # ============== End: Product Reviews ============== 
  

    # Parse the Ajax response (Json) and extract the product reviews
    def parse_ajax_response(self, response):
        meta = response.meta
        formdata = meta["formdata"]
        current_page_num = formdata['specs[reviews][1][page]']

        # test
        product_id = meta["product_id"]
        print(f"parse_ajax_response for page product: {product_id}, review page number: {current_page_num}")
        
        # Get the itemLoader object from parser_products
        l = meta['itemLoader']

        if 'reviewers' in meta.keys(): # Non 1st page of reviews
            reviewers =meta['reviewers']
            reviewer_ratings = meta['reviewer_ratings']
        else: # 1st page of reviews
            reviewers = []
            reviewer_ratings = []

        # Loads the Json data
        j = json.loads(response.text)
        html = j["output"]["reviews"]
        # Create the Selector
        sel = scrapy.Selector(text=html)

        # Get all reviews, it contains the current item reviews and other items reviews of the same store
        all_reviews = sel.xpath("//div[@data-appears-component-name='listing_page_reviews']//div[re:match(@data-review-region, '\w+')]",
                                namespaces={"re": "http://exslt.org/regular-expressions"})

        # current page # item reviews
        item_reviews_cnt = 0

        # Process each review
        for r in all_reviews:
            # Get the review's product id
            review_product_id = r.xpath(".//a[@data-review-link='']/@href").extract_first().split('/')[2]

            # Only return the item review, not all store reviews
            if product_id == review_product_id:
                item_reviews_cnt += 1

                reviewer_profile_link = r.xpath(".//a[@data-review-username='']/@href").extract_first()
                if reviewer_profile_link:
                    try:
                        # Get the user token of that reviewer
                        reviewer = reviewer_profile_link.split('?')[0].split("/")[-1]
                    except:
                        reviewer = "unknown"
                else:
                    # reviewer as "Reviewed by Inactive"
                    reviewer = "inactive"

                reviewer_rating = r.xpath('.//input[@name="rating"]/@value').extract_first()

                reviewers.append(reviewer)
                reviewer_ratings.append(reviewer_rating)


        # If all reviews (each page has 4 reviews) are for that product, go to next page to find more
        if item_reviews_cnt == self.REVIEWS_CNT_PER_PAGE:
            updated_formdata = meta["formdata"]
            updated_formdata['specs[reviews][1][page]'] = str(int(current_page_num)+1)
            updated_data = meta
            updated_data["formdata"] = updated_formdata
            updated_data["reviewers"] = reviewers
            updated_data["reviewer_ratings"] = reviewer_ratings

            yield scrapy.FormRequest(meta["ajax_url"], headers=meta["headers"], 
                                    cookies=meta["cookies"],
                                    meta=updated_data, formdata=updated_formdata,
                                    callback=self.parse_ajax_response)

        # Until current page # item reviews < 4, stop, no need to go to next page
        else:
            # add reviewers and reviewer_ratings
            l.add_value('users', reviewers)
            l.add_value('ratings', reviewer_ratings)
            l.add_value('reviews_count', len(reviewer_ratings))

            yield l.load_item()
