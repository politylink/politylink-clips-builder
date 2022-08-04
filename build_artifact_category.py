import json
import logging
import shutil
from pathlib import Path

import pandas as pd

from mylib.artifact import Category, CategoryPage
from mylib.utils import load_topic_map

LOGGER = logging.getLogger(__name__)

IGNORE_TOPIC_ID_SET = {2, 3, 5}  # manually exclude some topic_ids to ensure diversity


def main(category_fp, topic_fp, artifact_direc):
    category_df = pd.read_csv(category_fp)
    topic_df = pd.read_csv(topic_fp)
    topic_df = topic_df[~(topic_df['topic_id'].isin(IGNORE_TOPIC_ID_SET))]
    topic_map = load_topic_map(topic_fp)
    LOGGER.info(f'loaded {len(category_df)} categories')

    shutil.rmtree(artifact_direc, ignore_errors=True)
    Path(artifact_direc).mkdir(parents=True)
    for _, row in category_df.iterrows():
        category_id = row['category_id']
        category = Category(
            category_id=category_id,
            title=row['title'],
            desc=row['desc']
        )
        df = topic_df[topic_df['category_id'] == category_id].sort_values(by='clip_count', ascending=False)
        topics = [topic_map[topic_id] for topic_id in df['topic_id'].head(5)]
        category_page = CategoryPage(
            category=category,
            topics=topics
        )

        artifact_fp = Path(artifact_direc) / '{}.json'.format(category_id)
        with open(artifact_fp, 'w') as f:
            json.dump(category_page.to_dict(), f, ensure_ascii=False, indent=2)
            LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(category_df)} artifacts in {artifact_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        category_fp='./data/category.csv',
        topic_fp='./out/topic.csv',
        artifact_direc='./out/artifact/category'
    )
