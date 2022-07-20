import logging

import pandas as pd
import spacy

from cluster import TokenFinder
from utils import load_minutes_record

nlp = spacy.load('ja_ginza')

LOGGER = logging.getLogger(__name__)


def to_token_set(doc):
    pos_set = {'ADJ', 'ADV', 'NOUN', 'PROPN'}
    return set([token.lemma_ for token in doc if token.pos_ in pos_set])


def find_best_speech(clip, minutes_record):
    name = clip['name']

    topic = nlp(clip['topic'])
    topic_tokens = to_token_set(topic)
    token_finder = TokenFinder(topic_tokens)

    result = []
    for speech_record in minutes_record['speechRecord']:
        text = speech_record['speech']
        speaker = speech_record['speaker']
        speech_id = speech_record['speechOrder']
        if speaker == name:
            token_finder.index(speech_id, text)
            common_tokens = token_finder.find(id_=speech_id)
            score = len(common_tokens) / len(topic_tokens)
            result.append((speech_id, score))

    if not result:
        raise ValueError('minutes_id={} does not have speech from {}'.format(minutes_record['issueID'], name))

    return max(result, key=lambda x: x[1])


def main(clip_fp, match_fp):
    clip_df = pd.read_csv(clip_fp)

    records = []
    for minutes_id, df in clip_df.groupby('minutes_id'):
        LOGGER.info(f'found {len(df)} clips for {minutes_id}')
        minutes_record = load_minutes_record(minutes_id)
        for _, clip in df.iterrows():
            try:
                speech_id, score = find_best_speech(clip, minutes_record)
                records.append({
                    'clip_id': clip['clip_id'],
                    'minutes_id': clip['minutes_id'],
                    'speech_id': speech_id,
                    'score': score
                })
            except Exception:
                LOGGER.exception(f'failed to find match for clip_id={clip["clip_id"]}')

    match_df = pd.DataFrame(records)
    match_df.to_csv(match_fp, index=False)
    LOGGER.info(f'saved {match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        match_fp='./out/clip_minutes_match.csv'
    )
