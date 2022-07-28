import logging

import pandas as pd
import spacy

from mylib.canonicalize import normalize_text
from mylib.utils import load_minutes_record, TokenFinder, to_token_set

nlp = spacy.load('ja_ginza')

LOGGER = logging.getLogger(__name__)


def find_best_speech(speaker_name, clip_title, minutes_record):
    """
    find speech that best matches with clip title
    """

    with nlp.select_pipes(enable=['parser']):
        doc = nlp(clip_title)
    clip_tokens = to_token_set(doc)
    token_finder = TokenFinder(clip_tokens)

    result = []
    for speech_record in minutes_record['speechRecord']:
        speaker = speech_record['speaker']
        if speaker == speaker_name:
            text = normalize_text(speech_record['speech'])
            speech_id = speech_record['speechOrder']
            token_finder.index(speech_id, text)
            common_tokens = token_finder.find(id_=speech_id)
            score = len(common_tokens) / len(clip_tokens)
            result.append((speech_id, score))

    if not result:
        raise ValueError('minutes_id={} does not have speech from {}'.format(minutes_record['issueID'], speaker_name))

    return max(result, key=lambda x: x[1])


def main(clip_fp, minutes_fp, match_fp):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')

    minutes_df = pd.read_csv(minutes_fp)
    clip_df = pd.merge(clip_df, minutes_df[['minutes_id', 'session', 'meeting', 'issue']],
                       how='left', on=['session', 'meeting', 'issue'])

    is_missed = clip_df['minutes_id'].isnull()
    if is_missed.sum():
        LOGGER.warning('failed to merge minutes: ' + str(set(clip_df[is_missed]['url'])))

    # validate minutes match by comparing date
    date_df = pd.merge(clip_df, minutes_df[['minutes_id', 'date']], on='minutes_id')
    miss_df = date_df[date_df['date_x'] != date_df['date_y']][['url', 'minutes_id', 'date_x', 'date_y']] \
        .drop_duplicates()
    if len(miss_df):
        LOGGER.warning('date mismatch found: ' + str(miss_df.to_dict(orient='records')))

    records = []
    for minutes_id, df in clip_df.groupby('minutes_id'):
        LOGGER.info(f'found {len(df)} clips for {minutes_id}')
        minutes_record = load_minutes_record(minutes_id)
        for _, clip in df.iterrows():
            try:
                speech_id, score = find_best_speech(clip['name'], clip['title'], minutes_record)
                records.append({
                    'clip_id': clip['clip_id'],
                    'minutes_id': clip['minutes_id'],
                    'speech_id': speech_id,
                    'score': score
                })
            except Exception:
                LOGGER.exception(f'failed to find match for clip_id={clip["clip_id"]}')

    out_df = pd.DataFrame(records)
    out_df = out_df.sort_values(by='clip_id')
    out_df.to_csv(match_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        minutes_fp='./out/minutes.csv',
        match_fp='./out/clip_minutes.csv'
    )
