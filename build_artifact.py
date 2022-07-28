import json
import logging
from logging import getLogger
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from mylib.utils import to_time_str, load_minutes_record
from mylib.artifact import Speaker, Speech, Clip, ClipPage

LOGGER = getLogger(__name__)


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


def main(clip_fp, member_fp,
         minutes_match_fp, member_match_fp, gclip_match_fp, clip_match_fp, category_match_fp,
         artifact_direc):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')

    member_df = pd.read_csv(member_fp)
    member_match_df = pd.read_csv(member_match_fp)
    minutes_match_df = pd.read_csv(minutes_match_fp)
    gclip_match_df = pd.read_csv(gclip_match_fp)
    clip_match_df = pd.read_csv(clip_match_fp)
    category_match_fp = pd.read_csv(category_match_fp)

    clip_df = pd.merge(clip_df, member_match_df[['clip_id', 'member_id']], on='clip_id')
    clip_df = pd.merge(clip_df, minutes_match_df[['clip_id', 'minutes_id', 'speech_id']], on='clip_id')
    clip_df = pd.merge(clip_df, gclip_match_df[['clip_id', 'gclip_id', 'start_msec']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_match_df[['clip_id', 'clip_id_list']], on='clip_id')
    clip_df = pd.merge(clip_df, category_match_fp[['clip_id', 'category_id']], on='clip_id')
    clip_df = pd.merge(clip_df, member_df[['member_id', 'group', 'block']], on='member_id')
    LOGGER.info(f'enriched {len(clip_df)} clips')

    clip_page_map = dict()
    for _, row in tqdm(clip_df.iterrows()):
        minutes_url = 'https://kokkai.ndl.go.jp/txt/{0}/{1}'.format(row['minutes_id'], row['speech_id'])
        video_url = 'https://gclip1.grips.ac.jp/video/video/{0}?t={1}'.format(
            row['gclip_id'], to_time_str(row['start_msec']))

        speaker = Speaker(name=row['name'], group=row['group'], block=row['block'], member_id=row['member_id'])
        clip = Clip(
            clip_id=row['clip_id'],
            title=row['title'],
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
    LOGGER.info(f'built {len(clip_page_map)} clip pages')

    for _, row in clip_df.iterrows():
        clip_id = row['clip_id']
        clip_page = clip_page_map[clip_id]

        similar_clips = []
        similar_id_list = map(int, row['clip_id_list'].split(';'))
        for similar_id in similar_id_list:
            if similar_id != clip_id and similar_id in clip_page_map:
                similar_clips.append(clip_page_map[similar_id].clip)

        clip_page.clips = similar_clips
    LOGGER.info(f'enriched {len(clip_page_map)} with similar clips')

    for clip_id, clip_page in clip_page_map.items():
        artifact_fp = Path(artifact_direc) / '{}.json'.format(clip_id)
        with open(artifact_fp, 'w') as f:
            json.dump(clip_page.to_dict(), f, ensure_ascii=False, indent=2)
        LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(clip_page_map)} artifacts in {artifact_direc}')


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
        artifact_direc='./out/artifact/clip'
    )
