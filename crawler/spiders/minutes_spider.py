import json
from logging import getLogger

import scrapy

LOGGER = getLogger(__name__)


class MinutesSpider(scrapy.Spider):
    name = 'minutes'

    def __init__(self, first_date, last_date, pos=1, *args, **kwargs):
        super(MinutesSpider, self).__init__(*args, **kwargs)
        self.first_date = first_date
        self.last_date = last_date
        self.next_pos = int(pos)

    def build_next_url(self):
        return 'https://kokkai.ndl.go.jp/api/meeting?from={0}&until={1}&startRecord={2}&maximumRecords=5&nameOfHouse={3}&recordPacking=JSON'.format(
            self.first_date, self.last_date, self.next_pos, '参議院')

    def start_requests(self):
        yield scrapy.Request(self.build_next_url(), self.parse)

    def parse(self, response, **kwargs):
        LOGGER.info(f'requested {response.url}')
        response_body = json.loads(response.body)

        for meeting_record in response_body['meetingRecord']:
            ndl_id = meeting_record['issueID']
            fp = f'./out/minutes/{ndl_id}.json'
            with open(fp, 'w') as f:
                json.dump(meeting_record, f, ensure_ascii=False)
            LOGGER.info(f'saved {fp}')

        self.next_pos = response_body['nextRecordPosition']
        if self.next_pos is not None:
            yield response.follow(self.build_next_url(), callback=self.parse)
