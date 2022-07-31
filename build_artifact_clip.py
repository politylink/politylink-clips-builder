import json
import logging
from logging import getLogger
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from mylib.artifact import Speaker, Speech, Clip, ClipPage, Member, Topic
from mylib.utils import to_time_str, load_minutes_record, load_topic_map

LOGGER = getLogger(__name__)


def format_speech_text(text, thresh):
    text = ''.join(text.split()[1:])
    if len(text) > thresh:
        text = text[:thresh] + '...'
    return text


def build_speech(speech_record, thresh):
    speaker = Speaker(
        name=speech_record['speaker'],
        info=speech_record['speakerPosition'] or speech_record['speakerGroup']
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


def main(clip_fp, member_fp, topic_fp,
         clip_minutes_fp, clip_member_fp, clip_gclip_fp, clip_clip_fp, clip_category_fp, clip_topic_fp,
         artifact_direc):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')

    member_df = pd.read_csv(member_fp)
    clip_member_df = pd.read_csv(clip_member_fp)
    clip_minutes_df = pd.read_csv(clip_minutes_fp)
    clip_gclip_df = pd.read_csv(clip_gclip_fp)
    clip_clip_df = pd.read_csv(clip_clip_fp)
    clip_category_df = pd.read_csv(clip_category_fp)
    clip_topic_df = pd.read_csv(clip_topic_fp)

    clip_df = pd.merge(clip_df, clip_member_df[['clip_id', 'member_id']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_minutes_df[['clip_id', 'minutes_id', 'speech_id']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_gclip_df[['clip_id', 'gclip_id', 'start_msec']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_clip_df[['clip_id', 'clip_id_list']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_category_df[['clip_id', 'category_id']], on='clip_id')
    clip_df = pd.merge(clip_df, clip_topic_df[['clip_id', 'topic_id_list']], on='clip_id', how='left')\
        .fillna({'topic_id_list': ''})
    clip_df = pd.merge(clip_df, member_df[['member_id', 'group', 'block', 'image_url']], on='member_id')
    LOGGER.info(f'enriched {len(clip_df)} clips')

    topic_map = load_topic_map(topic_fp)

    clip_page_map = dict()
    for _, row in tqdm(clip_df.iterrows()):
        minutes_url = 'https://kokkai.ndl.go.jp/txt/{0}/{1}'.format(row['minutes_id'], row['speech_id'])
        video_url = 'https://gclip1.grips.ac.jp/video/video/{0}?t={1}'.format(
            row['gclip_id'], to_time_str(row['start_msec']))

        member = Member(
            member_id=row['member_id'],
            name=row['name'],
            group=row['group'],
            block=row['block'],
            image_url=row['image_url']
        )
        clip = Clip(
            clip_id=row['clip_id'],
            title=row['title'],
            date=row['date'],
            house='参議院',
            meeting=row['meeting'],
            minutes_url=minutes_url,
            video_url=video_url,
            category_id=row['category_id'],
            member=member
        )

        if row['topic_id_list']:
            clip.topic_ids = list(map(int, row['topic_id_list'].split(';')))
        speeches = build_speech_list(row['minutes_id'], row['speech_id'])
        clip_page = ClipPage(
            clip=clip,
            speeches=speeches,
        )
        if clip.topic_ids:
            clip_page.topics = [topic_map[topic_id] for topic_id in clip.topic_ids]
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
        topic_fp='./out/topic.csv',
        clip_minutes_fp='./out/clip_minutes.csv',
        clip_gclip_fp='./out/clip_gclip.csv',
        clip_clip_fp='./out/clip_clip.csv',
        clip_member_fp='./out/clip_member.csv',
        clip_category_fp='./out/clip_category.csv',
        clip_topic_fp='./out/clip_topic.csv',
        artifact_direc='./out/artifact/clip'
    )
