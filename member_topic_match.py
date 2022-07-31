import logging

import pandas as pd

from mylib.utils import flatten_id_list

LOGGER = logging.getLogger(__name__)


def main(clip_member_fp, clip_topic_fp, member_topic_fp):
    clip_member_df = pd.read_csv(clip_member_fp)
    clip_topic_df = pd.read_csv(clip_topic_fp)
    clip_topic_df = flatten_id_list(clip_topic_df, 'topic_id_list', 'topic_id')
    joined_df = pd.merge(clip_member_df, clip_topic_df, on='clip_id')

    records = []
    for member_id, group_df in joined_df.groupby('member_id'):
        group_df = group_df.sort_values(by='topic_id')
        value_counts = group_df['topic_id'].value_counts()
        topic_id_list = value_counts.index
        clip_count_list = value_counts.values
        records.append({
            'member_id': member_id,
            'topic_id_list': ';'.join(map(str, topic_id_list)),
            'clip_count_list': ';'.join(map(str, clip_count_list))
        })
    out_df = pd.DataFrame(records)
    out_df = out_df.sort_values(by='member_id')
    out_df.to_csv(member_topic_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {member_topic_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_topic_fp='./out/clip_topic.csv',
        clip_member_fp='./out/clip_member.csv',
        member_topic_fp='./out/member_topic.csv'
    )
