import json
import logging
import shutil
from pathlib import Path

import pandas as pd

from mylib.artifact import Member, MemberPage
from mylib.utils import load_topic_map

LOGGER = logging.getLogger(__name__)


def main(member_fp, topic_fp, member_topic_fp, artifact_direc):
    member_df = pd.read_csv(member_fp)
    member_topic_df = pd.read_csv(member_topic_fp)
    member_df = pd.merge(member_df, member_topic_df[['member_id', 'topic_id_list']], on='member_id', how='left') \
        .fillna({'topic_id_list': ''})
    topic_map = load_topic_map(topic_fp)
    LOGGER.info(f'loaded {len(member_df)} members')

    shutil.rmtree(artifact_direc, ignore_errors=True)
    Path(artifact_direc).mkdir(parents=True)
    for _, row in member_df.iterrows():
        member_id = row['member_id']
        member = Member(
            member_id=member_id,
            name=row['name'],
            group=row['group'],
            block=row['block'],
            summary=row['summary'],
            ref_url=row['ref_url']
        )
        member_page = MemberPage(
            member=member
        )
        if row['topic_id_list']:
            topic_id_list = list(map(int, row['topic_id_list'].split(';')))
            member_page.topics = [topic_map[topic_id] for topic_id in topic_id_list]

        artifact_fp = Path(artifact_direc) / '{}.json'.format(member_id)
        with open(artifact_fp, 'w') as f:
            json.dump(member_page.to_dict(), f, ensure_ascii=False, indent=2)
            LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(member_df)} artifacts in {artifact_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        member_fp='./out/member.csv',
        topic_fp='./out/topic.csv',
        member_topic_fp='./out/member_topic.csv',
        artifact_direc='./out/artifact/member'
    )
