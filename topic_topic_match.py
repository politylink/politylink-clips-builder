import logging
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import pairwise_distances

from mylib.utils import flatten_id_list

LOGGER = logging.getLogger(__name__)


def main(clip_fp, topic_fp, clip_topic_fp, topic_topic_fp):
    clip_df = pd.read_csv(clip_fp)
    topic_df = pd.read_csv(topic_fp)
    clip_topic_df = pd.read_csv(clip_topic_fp)
    clip_topic_df = flatten_id_list(clip_topic_df, 'topic_id_list', 'topic_id')
    clip_topic_df = pd.merge(clip_topic_df, clip_df[['clip_id', 'meeting']])

    # 所属委員会の分布のコサイン類似度からトピック間の距離を算出する
    topic_id_list = list(topic_df['topic_id'])
    meeting_list = list(set(clip_df['meeting']))
    feature_mat = np.zeros((len(topic_id_list), len(meeting_list)))
    for i, topic_id in enumerate(topic_id_list):
        df = clip_topic_df[clip_topic_df['topic_id'] == topic_id]
        value_count_map = defaultdict(int)
        value_count_map.update(df['meeting'].value_counts().to_dict())
        for j, meeting in enumerate(meeting_list):
            feature_mat[i][j] = value_count_map[meeting]
    dist_mat = 1 - pairwise_distances(feature_mat, metric='cosine')

    records = []
    for i, topic_id in enumerate(topic_id_list):
        j_list = np.argsort(dist_mat[i])[-5:][::-1]
        sim_id_list = [topic_id_list[j] for j in j_list]
        score_list = map(lambda j: dist_mat[i][j], j_list)
        records.append({
            'topic_id': topic_id,
            'topic_id_list': ';'.join(map(str, sim_id_list)),
            'score_list': ';'.join(map(lambda x: '{:.2f}'.format(x), score_list))
        })

    out_df = pd.DataFrame(records)
    out_df.to_csv(topic_topic_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {topic_topic_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        topic_fp='./out/topic.csv',
        clip_topic_fp='./out/clip_topic.csv',
        topic_topic_fp='./out/topic_topic.csv'
    )
