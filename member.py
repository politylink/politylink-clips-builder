import logging

import pandas as pd

from mylib.canonicalize import clean_text

LOGGER = logging.getLogger(__name__)


def main(giin_fp, member_fp):
    columns = {
        '議員氏名': 'name',
        '読み方': 'yomi',
        '会派': 'group',
        '選挙区': 'block',
        '任期満了': 'tenure',
        '議員個人の紹介ページ': 'ref_url',
        '写真URL': 'image_url',
        '経歴': 'summary'
    }
    giin_df = pd.read_csv(giin_fp)
    member_df = giin_df[columns.keys()].rename(columns=columns)
    member_df['name'] = member_df['name'].apply(clean_text)
    member_df.index = member_df.index + 1
    member_df.to_csv(member_fp, index_label='member_id')
    LOGGER.info(f'saved {len(member_df)} records to {member_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        giin_fp='./data/giin.csv',
        member_fp='./out/member.csv',
    )
