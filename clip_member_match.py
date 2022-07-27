import logging

import pandas as pd

LOGGER = logging.getLogger(__name__)


def main(clip_fp, member_fp, match_fp):
    clip_df = pd.read_csv(clip_fp)
    LOGGER.info(f'loaded {len(clip_df)} clips')

    member_df = pd.read_csv(member_fp, dtype={'member_id': 'Int64'})
    member_df['key'] = member_df['name'].map(lambda x: ''.join(x.split()))
    clip_df = pd.merge(
        clip_df[['clip_id', 'name']].rename(columns={'name': 'key'}),
        member_df[['member_id', 'key']],
        how='left', on='key'
    )

    is_missed = clip_df['member_id'].isnull()
    if is_missed.sum():
        LOGGER.warning('failed to merge members for {} rows: {}'.format(
            is_missed.sum(), set(clip_df[is_missed]['key'])))

    out_df = clip_df[['clip_id', 'member_id']].dropna()
    out_df.to_csv(match_fp, index=False)
    LOGGER.info(f'saved {len(out_df)} records to {match_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        member_fp='./out/member.csv',
        match_fp='./out/clip_member.csv'
    )
