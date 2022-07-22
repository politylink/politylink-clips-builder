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


def build_speech_list(minutes_id, speech_id, speech_count=2,  speech_thresh=300):
    minutes_record = load_minutes_record(minutes_id)

    speech_list = []
    for idx in range(speech_id, speech_id + speech_count):
        if idx < len(minutes_record['speechRecord']):
            speech_list.append(build_speech(minutes_record['speechRecord'][idx], speech_thresh))
    return speech_list


def build_clip_list():
    return [
        {
            "clipId": 2712,
            "title": "ＳＡＦの安定供給に係るサプライチェーンの構築に向けた取組状況",
            "date": "2022/6/2",
            "house": "参議院",
            "meeting": "国土交通委員会",
            "speaker": {
                "name": "朝日 健太郎",
                "info": "自民・東京",
            }
        },
        {
            "clipId": 2719,
            "title": "国産ＳＡＦの研究開発及び製造に係る今後の見通し",
            "date": "2022/6/2",
            "house": "参議院",
            "meeting": "国土交通委員会",
            "speaker": {
                "name": "竹内 真二",
                "info": "公明・比例",
            }
        }
    ]


def build_speaker(name, group, block):
    return Speaker(
        name=name,
        info=f'{group}・{block}',
        group=group,
        block=block
    )


def main(clip_fp, minutes_match_fp, gclip_match_fp, member_fp, artifact_direc):
    clip_df = pd.read_csv(clip_fp)
    minutes_match_df = pd.read_csv(minutes_match_fp)
    gclip_match_df = pd.read_csv(gclip_match_fp)
    member_df = pd.read_csv(member_fp)
    clip_df = pd.merge(clip_df, minutes_match_df[['clip_id', 'speech_id']], on='clip_id')
    clip_df = pd.merge(clip_df, gclip_match_df[['clip_id', 'gclip_id', 'start_msec']], on='clip_id')
    clip_df = pd.merge(clip_df, member_df[['member_id', 'group', 'block']])

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
            speaker=speaker
        )
        speeches = build_speech_list(row['minutes_id'], row['speech_id'])
        clips = build_clip_list()

        clip_page = ClipPage(
            clip=clip,
            speeches=speeches,
            speakers=[speaker],
            clips=clips
        )

        artifact_fp = Path(artifact_direc) / '{}.json'.format(row['clip_id'])
        with open(artifact_fp, 'w') as f:
            json.dump(clip_page.to_dict(), f, ensure_ascii=False, indent=2)
        LOGGER.debug(f'saved {artifact_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        minutes_match_fp='./out/clip_minutes.csv',
        gclip_match_fp='./out/clip_gclip.csv',
        member_fp='./out/member.csv',
        artifact_direc='./out/artifact'
    )
