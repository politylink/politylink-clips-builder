import logging

import numpy as np
import pandas as pd
import spacy
from tqdm import tqdm

from build_artifact_clip import build_speech_list
from mylib.canonicalize import normalize_text
from mylib.utils import to_token_set, TokenFinder

nlp = spacy.load('ja_ginza')

LOGGER = logging.getLogger(__name__)


def main(clip_fp, minutes_match_fp, clip_match_fp):
    clip_df = pd.read_csv(clip_fp)
    m_match_df = pd.read_csv(minutes_match_fp, dtype={'speech_id': 'Int64'})
    clip_df = pd.merge(clip_df, m_match_df[['clip_id', 'minutes_id', 'speech_id']], on='clip_id')

    LOGGER.info(f'tokenizing {len(clip_df)} clips')
    clip2tokens = dict()
    for _, clip in tqdm(clip_df.iterrows()):
        clip_id = clip['clip_id']
        title = clip['title']

        with nlp.select_pipes(enable=['parser']):
            doc = nlp(title)
        clip2tokens[clip_id] = to_token_set(doc)

    all_tokens = set()
    for s in clip2tokens.values():
        all_tokens.update(s)

    LOGGER.info(f'indexing {len(clip_df)} speeches')
    token_finder = TokenFinder(all_tokens)
    for _, clip in tqdm(clip_df.iterrows()):
        speech_list = build_speech_list(clip['minutes_id'], clip['speech_id'], speech_count=2, speech_thresh=10000)
        text = ''.join(map(lambda x: x.speech, speech_list))
        text = normalize_text(text)
        token_finder.index(clip['clip_id'], text)

    size = clip_df['clip_id'].max() + 1
    dist_mat = np.zeros((size, size))

    LOGGER.info(f'calculating similarity scores')
    for src_id in tqdm(clip_df['clip_id']):
        src_set = clip2tokens[src_id]
        for trg_id in clip_df['clip_id']:
            trg_set = token_finder.find(id_=trg_id)
            score = (len(src_set & trg_set) / len(src_set))
            dist_mat[src_id][trg_id] = score

    records = []
    for clip_id in tqdm(clip_df['clip_id']):
        clip_id_list = np.argsort(dist_mat[clip_id])[-5:][::-1]
        score_list = map(lambda x: dist_mat[clip_id][x], clip_id_list)

        records.append({
            'clip_id': clip_id,
            'clip_id_list': ';'.join(map(str, clip_id_list)),
            'score_list': ';'.join(map(lambda x: '{:.2f}'.format(x), score_list))
        })

    c_match_df = pd.DataFrame(records)
    c_match_df.to_csv(clip_match_fp, index=False)
    LOGGER.info(f'saved {len(c_match_df)} records to {clip_match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        minutes_match_fp='./out/clip_minutes.csv',
        clip_match_fp='./out/clip_clip.csv'
    )
