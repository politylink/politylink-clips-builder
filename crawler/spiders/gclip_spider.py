import json
from logging import getLogger
from pathlib import Path
from urllib.parse import urlparse

import scrapy

LOGGER = getLogger(__name__)


class GclipSpider(scrapy.Spider):
    name = 'gclip'
    start_urls = ['https://gclip1.grips.ac.jp/video/usage/session/208/house/sangiin']

    def parse(self, response, **kwargs):
        urls = []
        ul = response.xpath('//ul[@class="list-group"]')
        for li in ul.xpath('./li')[1:]:  # skip header
            url = li.xpath('.//a[@target="_blank"]/@href').get()
            urls.append(url)
        LOGGER.info(f'scraped {len(urls)} urls')

        for url in urls:
            yield response.follow(url, callback=self.parse_video)

    def parse_video(self, response):
        record = {}

        record['gclip_url'] = response.url
        record['video_url'] = response.xpath('//video/source/@src').get()
        a_minutes = response.xpath('//a[@target="_minutes"]')
        if a_minutes:
            record['minutes_url'] = a_minutes.xpath('./@href').get()

        speech_list = []
        table = response.xpath('//table[@id="keywordsTable"]')
        for row in table.xpath('.//div[@class="row"]'):
            p = row.xpath('.//p')
            if p:
                values = json.loads(row.xpath('.//input/@value').get())
                speech_list.append({
                    'speech': p.xpath('./text()').get(),
                    'start_msec': values['start_msec'],
                    'end_msec': values['end_msec']
                })
        record['speech_list'] = speech_list

        gclip_id = Path(urlparse(response.url).path).stem
        fp = f'./out/gclip/{gclip_id}.json'
        with open(fp, 'w') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        LOGGER.info(f'saved {fp}')
