import logging

import pandas as pd
from mylib.topic import is_match
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)


def main(clip_fp, topic_fp, match_fp):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')
    topic_df = pd.read_csv(topic_fp)

    # all vs all comparison. maybe we can improve performance with TokenFinder
    records = []
    for _, clip in tqdm(clip_df.iterrows()):
        topic_id_list = []
        for _, topic in topic_df.iterrows():
            if is_match(topic['query'], clip['title']):
                topic_id_list.append(topic['topic_id'])
        records.append({
            'clip_id': clip['clip_id'],
            'topic_id_list': ';'.join(map(str, topic_id_list))
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(match_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        topic_fp='./data/topic.csv',
        match_fp='./out/clip_topic.csv'
    )
