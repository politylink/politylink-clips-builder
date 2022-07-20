from logging import getLogger
from urllib.parse import urljoin

import scrapy

LOGGER = getLogger(__name__)


class SangiinShitsugiSpider(scrapy.Spider):
    name = 'shitsugi'
    start_urls = ['https://www.sangiin.go.jp/japanese/kaigijoho/shitsugi/208/shitsugi_ind.html']

    def parse(self, response, **kwargs):
        LOGGER.info(response.url)
        contents = response.xpath('//div[@id="ContentsBox"]')
        urls = []
        for a in contents.xpath('.//a'):
            href = a.xpath('./@href').get()
            urls.append(href)
        LOGGER.info(f'scraped {len(urls)} committee urls')

        for url in urls:
            yield response.follow(url, callback=self.parse_committee)

    def parse_committee(self, response):
        LOGGER.info(response.url)
        contents = response.xpath('//div[@id="list-style"]')

        urls = []
        for a in contents.xpath('.//a'):
            href = urljoin(response.url, a.xpath('./@href').get())
            urls.append(href)
        LOGGER.info(f'scraped {len(urls)} shitsugi urls')

        for url in urls:
            yield response.follow(url, callback=self.parse_shitsugi)

    def parse_shitsugi(self, response):
        LOGGER.info(response.url)

        contents = response.xpath('//ul[@class="exp_list_n"]')
        shitsugi_list = []
        for li in contents.xpath('./li'):
            name = li.xpath('./text()').get()
            topics = li.xpath('./ul/li/text()').getall()
            if topics:  # ignore 参考人
                shitsugi_list.append({
                    'name': clean_text(name),
                    'topics': [clean_text(topic) for topic in topics]
                })

        record = {
            'url': response.url,
            'title': clean_text(response.xpath('//h2/text()').get()),
            'subtitle': clean_text(response.xpath('//h3/text()').get()),
            'shitsugi': shitsugi_list
        }
        yield record


def clean_text(text):
    return ' '.join(text.strip().split())
