import json
import logging

import pandas as pd

from mylib.artifact import HomePage

LOGGER = logging.getLogger(__name__)


def load_clip_page_artifact(clip_id):
    artifact_fp = f'./out/artifact/clip/{clip_id}.json'
    with open(artifact_fp, 'r') as f:
        data = json.load(f)
    return data


def load_category_page_artifact(category_id):
    artifact_fp = f'./out/artifact/category/{category_id}.json'
    with open(artifact_fp, 'r') as f:
        data = json.load(f)
    return data


def main(clip_fp, category_fp, clip_category_fp, artifact_fp):
    clip_df = pd.read_csv(clip_fp)
    category_df = pd.read_csv(category_fp)

    clip_category_df = pd.read_csv(clip_category_fp)
    clip_df = pd.merge(clip_df, clip_category_df, on='clip_id')
    clip_df = clip_df.sort_values(by=['date', 'clip_id'], ascending=[False, True])

    # select the most recent clip for each meeting
    headline_df = clip_df.drop_duplicates(subset='meeting', keep='first')
    headline_id_list = list(headline_df['clip_id'].head(10))
    headline_id_set = set(headline_id_list)
    clips = []
    for clip_id in headline_id_list:
        clip_page = load_clip_page_artifact(clip_id)
        clips.append(clip_page['clip'])

    category_pages = []
    for category_id in category_df['category_id']:
        category_page = load_category_page_artifact(category_id)

        category_clips = []
        sub_df = clip_df[clip_df['category_id'] == category_id]
        for clip_id in sub_df['clip_id']:
            if len(category_clips) >= 5:
                break
            if clip_id in headline_id_set:  # avoid using the same clip multiple times
                continue
            clip_page = load_clip_page_artifact(clip_id)
            category_clips.append(clip_page['clip'])

        category_page['clips'] = category_clips
        category_pages.append(category_page)

    home_page = HomePage(
        clips=clips,
        categories=category_pages
    )
    with open(artifact_fp, 'w') as f:
        json.dump(home_page.to_dict(), f, ensure_ascii=False, indent=2)
        LOGGER.info(f'saved {artifact_fp}')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(
        clip_fp='./out/clip.csv',
        category_fp='./data/category.csv',
        clip_category_fp='./out/clip_category.csv',
        artifact_fp='./out/artifact/home.json'
    )
