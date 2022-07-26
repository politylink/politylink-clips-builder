import glob
import json
import logging
from pathlib import Path

import pandas as pd

from canonicalize import extract_issue

LOGGER = logging.getLogger(__name__)


def main(json_direc, csv_fp):
    json_fps = glob.glob(str(Path(json_direc) / '*.json'))

    records = []
    for fp in json_fps:
        with open(fp, 'r') as f:
            data = json.load(f)

        record = {
            'minutes_id': data['issueID'],
            'session': data['session'],
            'house': data['nameOfHouse'],
            'meeting': data['nameOfMeeting'],
            'issue': extract_issue(data['issue']),
            'date': data['date']
        }
        records.append(record)

    df = pd.DataFrame(records)
    df.to_csv(csv_fp, index=False)
    LOGGER.info(f'saved {len(df)} records to {csv_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        json_direc='./out/minutes',
        csv_fp='./out/minutes.csv',
    )
