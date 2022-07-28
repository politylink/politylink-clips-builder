import json
import logging
from pathlib import Path

import pandas as pd

from mylib.artifact import Topic

LOGGER = logging.getLogger(__name__)


def main(topic_fp, topic_match_fp, category_match_fp, artifact_direc):
    topic_df = pd.read_csv(topic_fp)
    topic_match_df = pd.read_csv(topic_match_fp).dropna()
    category_match_df = pd.read_csv(category_match_fp)

    # flatten topic_match_df
    topic_match_df['topic_id_list'] = topic_match_df['topic_id_list'].apply(lambda x: x.split(';'))
    topic_match_df = topic_match_df.explode('topic_id_list').rename(columns={'topic_id_list': 'topic_id'})
    topic_match_df['topic_id'] = topic_match_df['topic_id'].astype(int)

    # assign most frequent category_id to topic
    join_df = pd.merge(topic_match_df[['clip_id', 'topic_id']],
                       category_match_df[['clip_id', 'category_id']],
                       on='clip_id')
    agg_df = join_df.groupby('topic_id').agg(category_id=('category_id', lambda x: x.mode().iloc[0]),
                                             clip_count=('category_id', 'count')).reset_index()
    topic_df = pd.merge(topic_df, agg_df, on='topic_id')

    for _, row in topic_df.iterrows():
        topic_id = row['topic_id']
        title = row['condition'].split(';')[0]
        topic = Topic(topic_id=topic_id, title=title, category_id=row['category_id'], clip_count=row['clip_count'])
        artifact_fp = Path(artifact_direc) / '{}.json'.format(topic_id)
        with open(artifact_fp, 'w') as f:
            json.dump(topic.to_dict(), f, ensure_ascii=False, indent=2)
            LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(topic_df)} artifacts in {artifact_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        topic_fp='./data/topic.csv',
        topic_match_fp='./out/clip_topic.csv',
        category_match_fp='./out/clip_category.csv',
        artifact_direc='./out/artifact/topic'
    )
