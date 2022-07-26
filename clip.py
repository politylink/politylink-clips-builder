import json
import logging
import re
from logging import getLogger

import pandas as pd
from politylink.utils import DateConverter, to_date_str

from canonicalize import canonicalize_name, extract_issue, normalize_text

LOGGER = getLogger(__name__)


def extract_name(text):
    """
    in: 自見\u3000はなこ\u3000君（自民）
    out: 自見はなこ
    """

    name_p = r'(.+)(君（.+）|委員長)'
    m = re.search(name_p, text)
    if not m:
        LOGGER.warning(f'failed to extract name: {text}')
        return text
    name = m.group(1)
    name = ''.join(name.strip().split())
    return canonicalize_name(name)


def extract_session(text):
    """
    in: 第208回国会\u3000資源エネルギーに関する調査会
    out: 208
    """

    session_p = r'第(\d+)回国会'
    m = re.search(session_p, text)
    return int(m.group(1))


def extract_meeting(text):
    """
    in: 第208回国会\u3000資源エネルギーに関する調査会
    out: 資源エネルギーに関する調査会
    """

    meeting_p = r'([^\s]*(委員会|調査会|審査会|公聴会))'
    m = re.search(meeting_p, text)
    if not m:
        return ''  # expected when processing subtitle
    return m.group(1)


def extract_date(text):
    """
    in: 令和４年２月２日（水）\u3000第１回
    out: 2022-04-02
    """

    try:
        return to_date_str(DateConverter().convert(text))
    except:
        if text == '令和4年月4日（火） 第2回':  # https://www.sangiin.go.jp/japanese/kaigijoho/shitsugi/208/s028_0404.html
            return '2022-04-04'
        LOGGER.warning(f'failed to clean date: {text}')
        return ''


def main(jsonl_fp, csv_fp):
    records = [json.loads(line) for line in open(jsonl_fp, 'r')]

    clips = []
    for record in records:
        session = extract_session(record['title'])
        meeting = extract_meeting(record['title']) + extract_meeting(record['subtitle'])
        date = extract_date(record['subtitle'])
        issue = extract_issue(record['subtitle'])

        for shitsugi in record['shitsugi_list']:
            name = extract_name(shitsugi['name'])
            for topic in shitsugi['topic_list']:
                clips.append({
                    'topic': normalize_text(topic),
                    'name': name,
                    'date': date,
                    'session': session,
                    'house': '参議院',
                    'meeting': meeting,
                    'issue': issue,
                    'url': record['url']
                })

    clip_df = pd.DataFrame(clips)
    clip_df.to_csv(csv_fp, index_label='clip_id')
    LOGGER.info(f'saved {len(clip_df)}　records to {csv_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        jsonl_fp='./out/shitsugi.jl',
        csv_fp='./out/clip.csv'
    )
