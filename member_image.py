import logging
import time
from pathlib import Path

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

from PIL import Image
import io


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def crop_max_square(pil_img):
    return crop_center(pil_img, min(pil_img.size), min(pil_img.size))


def main(member_fp, image_direc):
    member_df = pd.read_csv(member_fp)
    LOGGER.info(f'found {len(member_df)} members to process')

    for _, row in member_df.iterrows():
        member_id = row['member_id']
        out_fp = Path(image_direc) / f'{member_id}.jpg'

        if out_fp.exists():
            LOGGER.info(f'found {out_fp}')
            continue

        response = requests.get(row['image_url'])
        image = Image.open(io.BytesIO(response.content))
        image = crop_max_square(image)
        image = image.resize((100, 100))
        image.save(out_fp)
        LOGGER.info(f'saved {out_fp}')
        time.sleep(0.5)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        member_fp='./out/member.csv',
        image_direc='./out/image/member'
    )
