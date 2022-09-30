# Scraping Etsy

The code was forked from [cpatrickalves/scraping-etsy](https://github.com/cpatrickalves/scraping-etsy), it's a set of Spiders to gather product's data from [Etsy](https://www.etsy.com), building on top of  [Scrapy](https://scrapy.org/) (Scraping and Web Crawling Framework).

I've made the following modifications to the original code:
- Added `total_page_count` and `start_page` to command.
- Removed `reviews_option`, now the Spider will get all usernames and corresponding user ratings in reviews section of each product page,  and save them as `users` and `ratings` respectively.
- Commented out some unneeded attributes, such as `product_options`, `image_urls`, and `description`.


## Prerequisites

To run the Spiders, download Python 3 from [Python.org](https://www.python.org/). 
After install, you need to install some Python packages:
```
pip install -r requirements.txt
```


## Usage

### Spider: search_products.py

This Spider access the Etsy website and search for products based on a given search string.

Supported parameters:
* *search* - Set the search string.
* *total_page_count* - Set the total number of pages to be scraped. The default value is 1.
* *start_page* - Set the inital page to be scraped. The default value is 1.

For example, to scrapy the first 2 pages of 'animal succulent planter', go to the project's folder and run:
```
scrapy crawl search_products -a search='animal succulent planter' -a total_page_count=2 -a start_page=1 -o sample-search-products.csv
```
where -o parameter is the output csv file path.

If you only need the products URLS, the scraping can be faster, just add `-a urls_only=true` to the command.

### How user ratings are scraped

The *users* and *ratings* data are obtained by Ajax requests to get all reviews in the product's page (simulate clicking next page to see more reviews).


## Sample CSV File

Check [sample-search-products.csv](https://github.com/eeliuqin/etsy-scraper/blob/master/outputs/sample-search-products.csv)


## Scraping speed

In *setting.py*, you can configure the delay for requests for the same website:
```
DOWNLOAD_DELAY = 0.5
```
The default value is 0, increase it to avoid hitting servers too hard.

Besides, You can change the maximum number of concurrent (i.e. simultaneous) requests that will be performed to any single domain:
```
CONCURRENT_REQUESTS_PER_DOMAIN = 4
```
The default value is 8, set it to a lower value to make the spider more polite, thus reducing the risk of being blocked.
