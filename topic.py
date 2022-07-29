import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def main(data_fp, topic_match_fp, category_match_fp, out_fp):
    topic_df = pd.read_csv(data_fp)
    topic_match_df = pd.read_csv(topic_match_fp).dropna()
    category_match_df = pd.read_csv(category_match_fp)

    # flatten topic_match_df: (clip_id, topic_id_list) -> (clip_id, topic_id)
    topic_match_df['topic_id_list'] = topic_match_df['topic_id_list'].apply(lambda x: x.split(';'))
    topic_match_df = topic_match_df.explode('topic_id_list').rename(columns={'topic_id_list': 'topic_id'})
    topic_match_df['topic_id'] = topic_match_df['topic_id'].astype(int)

    # assign most frequent category_id to topic_id
    join_df = pd.merge(topic_match_df[['clip_id', 'topic_id']],
                       category_match_df[['clip_id', 'category_id']],
                       on='clip_id')
    agg_df = join_df.groupby('topic_id').agg(category_id=('category_id', lambda x: x.mode().iloc[0]),
                                             clip_count=('category_id', 'count')).reset_index()
    topic_df = pd.merge(topic_df, agg_df, on='topic_id')

    out_df = topic_df[['topic_id', 'title', 'condition', 'category_id', 'clip_count']]
    out_df.to_csv(out_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {out_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        data_fp='./data/topic.csv',
        topic_match_fp='./out/clip_topic.csv',
        category_match_fp='./out/clip_category.csv',
        out_fp='./out/topic.csv'
    )
