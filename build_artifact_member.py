import json
import logging
from pathlib import Path

import pandas as pd

from mylib.artifact import Member, MemberPage

LOGGER = logging.getLogger(__name__)


def main(member_fp, artifact_direc):
    member_df = pd.read_csv(member_fp)
    LOGGER.info(f'loaded {len(member_df)} members')

    for _, row in member_df.iterrows():
        member_id = row['member_id']
        member = Member(
            member_id=member_id,
            name=row['name'],
            group=row['group'],
            block=row['block'],
            summary=row['summary'],
            ref_url=row['ref_url'],
            image_url=row['image_url']
        )
        member_page = MemberPage(
            member=member
        )
        artifact_fp = Path(artifact_direc) / '{}.json'.format(member_id)
        with open(artifact_fp, 'w') as f:
            json.dump(member_page.to_dict(), f, ensure_ascii=False, indent=2)
            LOGGER.debug(f'saved {artifact_fp}')
    LOGGER.info(f'published {len(member_df)} artifacts in {artifact_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        member_fp='./out/member.csv',
        artifact_direc='./out/artifact/member'
    )
