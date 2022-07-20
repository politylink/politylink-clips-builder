from logging import getLogger
from urllib.parse import urljoin

import scrapy

LOGGER = getLogger(__name__)


class MemberSpider(scrapy.Spider):
    name = 'member'

    def __init__(self, diet, *args, **kwargs):
        super(MemberSpider, self).__init__(*args, **kwargs)
        self.start_urls = [self.build_start_url(diet)]

    @staticmethod
    def build_start_url(diet_number):
        return f'https://www.sangiin.go.jp/japanese/joho1/kousei/giin/{diet_number}/giin.htm'

    def parse(self, response, **kwargs):
        table = response.xpath('//table[@summary="議員一覧（50音順）"]')[0]
        for row in table.xpath('./tr')[1:]:  # skip header
            cells = row.xpath('./td')
            assert len(cells) == 6

            record = {
                'name': get_text(cells[0]),
                'yomi': get_text(cells[1]),
                'group': get_text(cells[2]),
                'block': get_text(cells[3]),
                'tenure': get_text(cells[4]),
                'url': urljoin(response.url, cells[0].xpath('./a/@href').get())
            }
            yield record


def get_text(cell):
    text = cell.xpath('.//text()').get().strip()
    return ' '.join(text.split())
