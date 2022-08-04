import glob
import logging
from pathlib import Path

from PIL import Image
from tqdm import tqdm

LOGGER = logging.getLogger(__name__)


def main(raw_direc, resize_direc, width=480, height=270):
    image_fps = glob.glob(f'{raw_direc}/*.jpg')
    LOGGER.info(f'found {len(image_fps)} images to resize')

    for image_fp in tqdm(image_fps):
        image_fp = Path(image_fp)
        resize_fp = f'{resize_direc}/{image_fp.name}'
        image = Image.open(image_fp)
        image = image.resize((480, 270))
        image.save(resize_fp)
        LOGGER.debug(resize_fp)
    LOGGER.info(f'saved ${len(image_fps)} images in ${resize_direc}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        raw_direc='./out/image/clip',
        resize_direc='./out/image/clip_480',
    )
