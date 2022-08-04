import glob
import logging
from pathlib import Path

import boto3
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)

"""
requires ~/.aws/credentials
https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html
"""

s3_client = boto3.client('s3')


def main(local_direc, s3_direc):
    local_fps = glob.glob(f'{local_direc}/*.jpg')
    LOGGER.debug(f'found {len(local_fps)} files to publish')

    for local_fp in tqdm(local_fps):
        s3_fp = f'{s3_direc}/{Path(local_fp).name}'
        s3_client.upload_file(str(local_fp), 'politylink', str(s3_fp), ExtraArgs={'ContentType': 'image/jpeg'})
        LOGGER.debug(f'copied {local_fp} to {s3_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        local_direc='./out/image/clip',
        s3_direc='clips/clip/l',
    )
