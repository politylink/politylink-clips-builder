import logging
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

LOGGER = logging.getLogger(__name__)


def process(clip):
    thumb_fp = Path('./out/thumb/{}.jpg'.format(clip['clip_id']))
    if thumb_fp.exists():
        LOGGER.info(f'skip {thumb_fp}')
        return

    thumb_msec = clip['start_msec'] + 3000
    ts_id = thumb_msec // 10000
    ts_sec = (thumb_msec % 10000) / 1000
    ts_url = 'https://webtv-vod.live.ipcasting.jp/vod/mp4:{0}.mp4/media_{1}.ts'.format(clip['video_id'], ts_id)
    cmd = 'ffmpeg -y -ss 00:00:{0:05.2f} -i {1} -vframes 1 {2}'.format(ts_sec, ts_url, thumb_fp)
    subprocess.run(cmd.split(), capture_output=True)
    LOGGER.info(f'saved {thumb_fp}')


def main(gclip_fp, g_match_fp):
    gclip_df = pd.read_csv(gclip_fp)
    g_match_df = pd.read_csv(g_match_fp)
    g_match_df = pd.merge(g_match_df, gclip_df, on='gclip_id')
    clips = g_match_df.to_dict(orient='records')
    LOGGER.info(f'found {len(clips)} clips to process')

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process, clips)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        gclip_fp='./out/gclip.csv',
        g_match_fp='./out/clip_gclip.csv'
    )
