import logging

import pandas as pd
import spacy

from mylib.utils import load_minutes_record, load_gclip_record

nlp = spacy.load('ja_ginza')

LOGGER = logging.getLogger(__name__)


def find_best_gclip_speech(minutes_speech, gclip_record, qsize=10):
    text = ''.join(minutes_speech['speech'].split()[1:])  # remove name
    for i in range(0, len(text) - qsize, qsize):
        query = text[i: i + qsize]

        match = []
        for gclip_speech in gclip_record['speech_list']:
            if query in gclip_speech['speech']:
                match.append(gclip_speech)

        if len(match) == 1:  # found unique match
            return match[0]

    raise ValueError(f'failed to find gclip match: {minutes_speech}')


def main(clip_fp, clip_minutes_fp, gclip_fp, clip_gclip_fp):
    clip_df = pd.read_csv(clip_fp)
    clip_minutes_df = pd.read_csv(clip_minutes_fp, dtype={'speech_id': 'Int64'})
    gclip_df = pd.read_csv(gclip_fp, dtype={'gclip_id': 'Int64'})

    clip_df = pd.merge(clip_df, clip_minutes_df[['clip_id', 'minutes_id', 'speech_id']], on='clip_id', how='left')
    clip_df = pd.merge(clip_df, gclip_df[['minutes_id', 'gclip_id']], on='minutes_id', how='left')

    is_missed = clip_df['gclip_id'].isnull()
    if is_missed.sum():
        LOGGER.warning('failed to assign gclip_id: ' + str(set(clip_df[is_missed]['minutes_id'])))

    records = []
    for minutes_id, df in clip_df.groupby('minutes_id'):
        gclip_id = df['gclip_id'].iloc[0]
        LOGGER.info(f'found {len(df)} clips for {gclip_id}')

        minutes_record = load_minutes_record(minutes_id)
        gclip_record = load_gclip_record(gclip_id)

        for _, clip in df.iterrows():
            minutes_speech = minutes_record['speechRecord'][clip['speech_id']]
            gclip_speech = find_best_gclip_speech(minutes_speech, gclip_record)

            records.append({
                'clip_id': clip['clip_id'],
                'gclip_id': gclip_id,
                'start_msec': gclip_speech['start_msec']
            })

    out_df = pd.DataFrame(records)
    out_df = out_df.sort_values(by='clip_id')
    out_df.to_csv(clip_gclip_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {clip_gclip_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        clip_minutes_fp='./out/clip_minutes.csv',
        gclip_fp='./out/gclip.csv',
        clip_gclip_fp='./out/clip_gclip.csv'
    )
