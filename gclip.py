import glob
import json
import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd

LOGGER = logging.getLogger(__name__)


def main(json_direc, csv_fp):
    json_fps = glob.glob(str(Path(json_direc) / '*.json'))

    records = []
    for fp in json_fps:
        with open(fp, 'r') as f:
            data = json.load(f)

        record = {
            'gclip_id': Path(urlparse(data['gclip_url']).path).stem,
            'video_id': re.search(r'(\d+).mp4', data['video_url']).group(1)
        }
        if 'minutes_url' in data:
            record['minutes_id'] = Path(urlparse(data['minutes_url']).path).stem
        records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(csv_fp, index=False)
    LOGGER.info(f'saved {len(df)} records to {csv_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        json_direc='./out/gclip',
        csv_fp='./out/gclip.csv',
    )
