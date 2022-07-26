import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

LOGGER = logging.getLogger(__name__)


def main(jsonl_fp, csv_fp):
    records = [json.loads(line) for line in open(jsonl_fp, 'r')]
    df = pd.DataFrame(records)

    df['member_id'] = df['url'].map(lambda x: Path(urlparse(x).path).stem).astype(int)
    df = df[['member_id', 'name', 'yomi', 'group', 'block', 'tenure', 'url']]
    assert df['member_id'].is_unique

    df.to_csv(csv_fp, index=False)
    LOGGER.info(f'saved {len(df)} records to {csv_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        jsonl_fp='./out/member.jl',
        csv_fp='./out/member.csv',
    )
