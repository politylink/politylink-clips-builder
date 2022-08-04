import logging

import pandas as pd

from mylib.utils import flatten_id_list

LOGGER = logging.getLogger(__name__)


def main(data_fp, clip_topic_fp, clip_category_fp, out_fp):
    topic_df = pd.read_csv(data_fp)
    clip_topic_df = pd.read_csv(clip_topic_fp)
    clip_topic_df = flatten_id_list(clip_topic_df, 'topic_id_list', 'topic_id')
    clip_category_df = pd.read_csv(clip_category_fp)

    # assign most frequent category_id to topic_id
    join_df = pd.merge(clip_topic_df[['clip_id', 'topic_id']],
                       clip_category_df[['clip_id', 'category_id']],
                       on='clip_id')
    agg_df = join_df.groupby('topic_id').agg(category_id=('category_id', lambda x: x.mode().iloc[0]),
                                             clip_count=('category_id', 'count')).reset_index()
    topic_df = pd.merge(topic_df, agg_df, on='topic_id')

    out_df = topic_df[['topic_id', 'title', 'query', 'category_id', 'clip_count', 'desc']]
    out_df.to_csv(out_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        data_fp='./data/topic.csv',
        clip_topic_fp='./out/clip_topic.csv',
        clip_category_fp='./out/clip_category.csv',
        out_fp='./out/topic.csv'
    )
