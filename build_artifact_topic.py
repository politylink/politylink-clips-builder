import json
import logging
from pathlib import Path

import pandas as pd

from mylib.artifact import Topic, TopicPage

LOGGER = logging.getLogger(__name__)


def main(topic_fp, artifact_direc):
    topic_df = pd.read_csv(topic_fp)
    LOGGER.info(f'loaded {len(topic_df)} topics')

    for _, row in topic_df.iterrows():
        topic_id = row['topic_id']
        topic = Topic(
            topic_id=topic_id,
            title=row['title'],
            category_id=row['category_id']
        )
        topic_page = TopicPage(
            topic=topic
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
        artifact_direc='./out/artifact/topic'
    )
