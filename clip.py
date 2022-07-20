import json
import logging
import re
from logging import getLogger

import pandas as pd
from politylink.utils import DateConverter, to_date_str

ALIAS_TO_NAME = {  # 質疑項目　-> 国会会議録
    '礒﨑哲史': '礒崎哲史',
    '高野光二郞': '高野光二郎',
    '髙良鉄美': '高良鉄美'
}
LOGGER = getLogger(__name__)


def canonicalize_name(name):
    if name in ALIAS_TO_NAME:
        return ALIAS_TO_NAME[name]
    return name


def clean_name(text):
    """
    in: 自見\u3000はなこ\u3000君（自民）
    out: 自見はなこ
    """

    name_p = r'(.+)(君（.+）|委員長)'
    m = re.search(name_p, text)
    if not m:
        LOGGER.warning(f'failed to clean name: {text}')
        return text
    name = m.group(1)
    name = ''.join(name.strip().split())
    return canonicalize_name(name)


def clean_session(text):
    """
    in: 第208回国会\u3000資源エネルギーに関する調査会
    out: 208
    """

    session_p = r'第(\d+)回国会'
    m = re.search(session_p, text)
    return int(m.group(1))


def clean_meeting(text):
    """
    in: 第208回国会\u3000資源エネルギーに関する調査会
    out: 資源エネルギーに関する調査会
    """

    meeting_p = r'([^\s]*(委員会|調査会|審査会|公聴会))'
    m = re.search(meeting_p, text)
    if m:
        return m.group(1)
    return ''


def clean_date(text):
    """
    in: 令和４年２月２日（水）\u3000第１回
    out: 2022-04-02
    """

    converter = DateConverter()
    try:
        return to_date_str(converter.convert(text))
    except:
        LOGGER.warning(f'failed to clean date: {text}')
        return ''


def clean_issue(text):
    """
    in: 令和４年２月２日（水）\u3000第１回
    out: 1
    """

    issue_p = r'第(\d+)[回|号]'
    m = re.search(issue_p, text)
    return int(m.group(1))


def main(shitsugi_fp, member_fp, minutes_fp, clip_fp):
    records = [json.loads(line) for line in open(shitsugi_fp, 'r')]
    member_df = pd.read_csv(member_fp)
    minutes_df = pd.read_csv(minutes_fp)
    minutes_df['issue'] = minutes_df['issue'].map(clean_issue)

    clips = []
    for record in records:
        session = clean_session(record['title'])
        meeting = clean_meeting(record['title']) + clean_meeting(record['subtitle'])
        date = clean_date(record['subtitle'])
        issue = clean_issue(record['subtitle'])

        for shitsugi in record['shitsugi']:
            name = clean_name(shitsugi['name'])
            for topic in shitsugi['topics']:
                clips.append({
                    'session': session,
                    'meeting': meeting,
                    'date': date,
                    'issue': issue,
                    'name': name,
                    'topic': topic,
                    'url': record['url']
                })

    clip_df = pd.DataFrame(clips)
    clip_df = pd.merge(clip_df, member_df[['member_id', 'key']].rename(columns={'key': 'name'}), how='left', on='name')
    clip_df['member_id'] = clip_df['member_id'].fillna(-1).astype(int)
    clip_df = pd.merge(clip_df, minutes_df[['minutes_id', 'session', 'meeting', 'issue']], how='left',
                       on=['session', 'meeting', 'issue'])

    mask_invalid_member = clip_df['member_id'] == -1
    mask_invalid_minutes = clip_df['minutes_id'].isnull()
    if mask_invalid_member.sum():
        LOGGER.warning('failed to merge members: ' + str(set(clip_df[mask_invalid_member]['name'])))
    if mask_invalid_minutes.sum():
        LOGGER.warning('failed to merge minutes: ' + str(set(clip_df[mask_invalid_minutes]['url'])))

    # validate minutes match by comparing date
    date_df = pd.merge(clip_df, minutes_df[['minutes_id', 'date']], on='minutes_id')
    miss_df = date_df[date_df['date_x'] != date_df['date_y']][['url', 'minutes_id', 'date_x', 'date_y']] \
        .drop_duplicates()
    if len(miss_df):
        LOGGER.warning('date mismatch found: ' + str(miss_df.to_dict(orient='records')))

    clip_df.to_csv(clip_fp, index_label='clip_id')
    LOGGER.info(f'saved {clip_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        shitsugi_fp='./out/shitsugi.jl',
        member_fp='./out/member.csv',
        minutes_fp='./out/minutes.csv',
        clip_fp='./out/clip.csv'
    )
