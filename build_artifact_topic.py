import json
import logging
from pathlib import Path

import pandas as pd

from mylib.artifact import TopicPage, Topic
from mylib.utils import load_topic_map

LOGGER = logging.getLogger(__name__)


def main(topic_fp, topic_topic_fp, artifact_direc):
    topic_df = pd.read_csv(topic_fp).fillna('')
    topic_topic_df = pd.read_csv(topic_topic_fp)
    topic_df = pd.merge(topic_df, topic_topic_df[['topic_id', 'topic_id_list']], on='topic_id')
    topic_map = load_topic_map(topic_fp)
    LOGGER.info(f'loaded {len(topic_df)} topics')

    for _, row in topic_df.iterrows():
        topic_id = row['topic_id']
        topic = Topic(topic_id=topic_id, title=row['title'], category_id=row['category_id'], description=row['desc'])
        topic_id_list = list(map(int, row['topic_id_list'].split(';')))
        topics = [topic_map[id_] for id_ in topic_id_list if id_ != topic_id]
        topic_page = TopicPage(
            topic=topic,
            topics=topics
        )

        artifact_fp = Path(artifact_direc) / '{}.json'.format(topic_id)
        with open(artifact_fp, 'w') as f:
            json.dump(topic_page.to_dict(), f, ensure_ascii=False, indent=2)
            LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(topic_df)} artifacts in {artifact_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        topic_fp='./out/topic.csv',
        topic_topic_fp='./out/topic_topic.csv',
        artifact_direc='./out/artifact/topic'
    )
