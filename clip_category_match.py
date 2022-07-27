import logging
import unicodedata

import pandas as pd

LOGGER = logging.getLogger(__name__)


def main(clip_fp, category_fp, match_fp):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')

    cat_df = pd.read_csv(category_fp, dtype={'category_id': 'Int64'})
    cat_df['topic'] = cat_df['topic'].apply(lambda x: unicodedata.normalize('NFKC', x))
    cat_df = cat_df[['topic', 'category_id']].drop_duplicates()
    assert cat_df['topic'].is_unique

    clip_df = pd.merge(clip_df[['clip_id', 'topic']], cat_df[['topic', 'category_id']], how='left', on='topic')

    is_missed = clip_df['category_id'].isnull()
    if is_missed.sum():
        LOGGER.warning('failed to assign category_id for {} rows: {}'.format(
            is_missed.sum(), set(clip_df[is_missed]['topic'])))

    out_df = clip_df[['clip_id', 'category_id']].dropna()
    out_df.to_csv(match_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        category_fp='./out/topic_category.csv',
        match_fp='./out/clip_category.csv'
    )
