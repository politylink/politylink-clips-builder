from logging import getLogger
from urllib.parse import urljoin

import scrapy

from canonicalize import clean_text

LOGGER = getLogger(__name__)


class SangiinShitsugiSpider(scrapy.Spider):
    name = 'shitsugi'
    start_urls = ['https://www.sangiin.go.jp/japanese/kaigijoho/shitsugi/208/shitsugi_ind.html']

    def parse(self, response, **kwargs):
        LOGGER.info(response.url)

        urls = []
        for a in response.xpath('//div[@id="ContentsBox"]//a'):
            href = urljoin(response.url, a.xpath('./@href').get())
            urls.append(href)
        LOGGER.info(f'scraped {len(urls)} committee urls')

        for url in urls:
            yield response.follow(url, callback=self.parse_committee)

    def parse_committee(self, response):
        LOGGER.info(response.url)

        urls = []
        for a in response.xpath('//div[@id="list-style"]//a'):
            href = urljoin(response.url, a.xpath('./@href').get())
            urls.append(href)
        LOGGER.info(f'scraped {len(urls)} shitsugi urls')

        for url in urls:
            yield response.follow(url, callback=self.parse_shitsugi)

    def parse_shitsugi(self, response):
        LOGGER.info(response.url)

        shitsugi_list = []
        for li in response.xpath('//ul[@class="exp_list_n"]/li'):
            name = li.xpath('./text()').get()
            topic_list = []
            for li2 in li.xpath('./ul/li'):
                topic = ''.join(li2.xpath('.//text()').getall())
                topic_list.append(topic)
            if topic_list:  # ignore 参考人
                shitsugi_list.append({
                    'name': clean_text(name),
                    'topic_list': [clean_text(topic) for topic in topic_list]
                })

        record = {
            'url': response.url,
            'title': clean_text(response.xpath('//h2/text()').get()),
            'subtitle': clean_text(response.xpath('//h3/text()').get()),
            'shitsugi_list': shitsugi_list
        }
        yield record



