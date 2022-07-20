import logging

import pandas as pd
import spacy

from utils import load_minutes_record, load_gclip_record

nlp = spacy.load('ja_ginza')

LOGGER = logging.getLogger(__name__)


def find_best_gclip_speech(minutes_speech, gclip_record, qsize=10):
    text = ''.join(minutes_speech['speech'].split()[1:])
    for i in range(0, len(text) - qsize, qsize):
        query = text[i: i + qsize]

        match = []
        for gclip_speech in gclip_record['speech_list']:
            if query in gclip_speech['speech']:
                match.append(gclip_speech)

        if len(match) == 1:
            return match[0]

    raise ValueError(f'failed to find gclip match: {minutes_speech}')


def main(gclip_fp, minutes_match_fp, gclip_match_fp):
    gclip_df = pd.read_csv(gclip_fp)
    m_match_df = pd.read_csv(minutes_match_fp)
    m_match_df = pd.merge(m_match_df, gclip_df, on='minutes_id', how='left')
    assert m_match_df['gclip_id'].isnull().sum() == 0

    records = []
    for minutes_id, df in m_match_df.groupby('minutes_id'):
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
                'start_msec': gclip_speech['start_msec'],
                'speech': gclip_speech['speech']
            })

    g_match_df = pd.DataFrame(records)
    g_match_df.to_csv(gclip_match_fp, index=False)
    LOGGER.info(f'saved {gclip_match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        gclip_fp='./out/gclip.csv',
        minutes_match_fp='./out/clip_minutes.csv',
        gclip_match_fp='./out/clip_gclip.csv'
    )
