import json
import logging
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Optional

import pandas as pd
from dataclasses_json import dataclass_json, LetterCase, config
from tqdm import tqdm

from utils import to_time_str, load_minutes_record

LOGGER = getLogger(__name__)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speaker:
    name: str
    info: str = ''
    group: str = ''
    block: str = ''


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speech:
    speaker: Speaker
    speech: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Clip:
    clip_id: int
    title: str
    date: str
    house: str
    meeting: str
    minutes_url: str
    video_url: str
    category_id: int
    speaker: Optional[Speaker] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ClipPage:
    clip: Clip
    speeches: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    speakers: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    clips: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


def format_speech_text(text, thresh):
    text = ''.join(text.split()[1:])
    if len(text) > thresh:
        text = text[:thresh] + '...'
    return text


def build_speech(speech_record, thresh):
    speaker = Speaker(
        name=speech_record['speaker'],
        info=speech_record['speakerPosition'] or speech_record['speakerGroup'],
        group=speech_record['speakerGroup']
    )
    speech_text = format_speech_text(speech_record['speech'], thresh)
    return Speech(
        speaker=speaker,
        speech=speech_text
    )


def build_speech_list(minutes_id, speech_id, speech_count=2, speech_thresh=300):
    minutes_record = load_minutes_record(minutes_id)

    speech_list = []
    for idx in range(speech_id, speech_id + speech_count):
        if idx < len(minutes_record['speechRecord']):
            speech_list.append(build_speech(minutes_record['speechRecord'][idx], speech_thresh))
    return speech_list


def build_speaker(name, group, block):
    return Speaker(
        name=name,
        info=f'{group}・{block}',
        group=group,
        block=block
    )


def main(clip_fp, member_fp, minutes_match_fp, member_match_fp, gclip_match_fp, clip_match_fp, category_match_fp,
         artifact_direc):
    clip_df = pd.read_csv(clip_fp)
    member_df = pd.read_csv(member_fp)
    member_match_df = pd.read_csv(member_match_fp, dtype={'member_id': 'Int64'}).dropna()
    minutes_match_df = pd.read_csv(minutes_match_fp, dtype={'speech_id': 'Int64'}).dropna()
    gclip_match_df = pd.read_csv(gclip_match_fp, dtype={'gclip_id': 'Int64'}).dropna()
    clip_match_df = pd.read_csv(clip_match_fp, dtype={'member_id': 'Int64'}).dropna()
    category_match_fp = pd.read_csv(category_match_fp, dtype={'category_id': 'Int64'}).dropna()

    clip_df = pd.merge(clip_df, member_match_df[['clip_id', 'member_id']], on='clip_id')
    clip_df = pd.merge(clip_df, minutes_match_df[['clip_id', 'minutes_id', 'speech_id']], on='clip_id')
    clip_df = pd.merge(clip_df, gclip_match_df[['clip_id', 'gclip_id', 'start_msec']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_match_df[['clip_id', 'clip_id_list']], on='clip_id')
    clip_df = pd.merge(clip_df, category_match_fp[['clip_id', 'category_id']], on='clip_id')
    clip_df = pd.merge(clip_df, member_df[['member_id', 'group', 'block']], on='member_id')

    clip_page_map = dict()
    for _, row in tqdm(clip_df.iterrows()):
        minutes_url = 'https://kokkai.ndl.go.jp/txt/{0}/{1}'.format(row['minutes_id'], row['speech_id'])
        video_url = 'https://gclip1.grips.ac.jp/video/video/{0}?t={1}'.format(
            row['gclip_id'], to_time_str(row['start_msec']))

        speaker = build_speaker(name=row['name'], group=row['group'], block=row['block'])
        clip = Clip(
            clip_id=row['clip_id'],
            title=row['topic'],
            date=row['date'],
            house='参議院',
            meeting=row['meeting'],
            minutes_url=minutes_url,
            video_url=video_url,
            category_id=row['category_id'],
            speaker=speaker
        )
        speeches = build_speech_list(row['minutes_id'], row['speech_id'])

        clip_page = ClipPage(
            clip=clip,
            speeches=speeches,
            speakers=[speaker]
        )
        clip_page_map[row['clip_id']] = clip_page

    for _, row in clip_df.iterrows():
        clip_id = row['clip_id']
        clip_page = clip_page_map[clip_id]

        similar_id_list = map(int, row['clip_id_list'].split(';'))
        similar_id_list = filter(lambda x: x != clip_id, similar_id_list)
        similar_clips = list(map(lambda x: clip_page_map[x].clip, similar_id_list))

        clip_page.clips = similar_clips

    for clip_id, clip_page in clip_page_map.items():
        artifact_fp = Path(artifact_direc) / '{}.json'.format(clip_id)
        with open(artifact_fp, 'w') as f:
            json.dump(clip_page.to_dict(), f, ensure_ascii=False, indent=2)
        LOGGER.debug(f'saved {artifact_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        member_fp='./out/member.csv',
        minutes_match_fp='./out/clip_minutes.csv',
        gclip_match_fp='./out/clip_gclip.csv',
        clip_match_fp='./out/clip_clip.csv',
        member_match_fp='./out/clip_member.csv',
        category_match_fp='./out/clip_category.csv',
        artifact_direc='./out/artifact'
    )
