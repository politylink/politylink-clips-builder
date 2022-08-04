#!/bin/zsh
set -eu

python clip_topic_match.py
python clip_category_match.py
python topic.py
python clip_minutes_match.py
python clip_member_match.py
python clip_gclip_match.py
python member_topic_match.py
python topic_topic_match.py
python build_artifact_clip.py
python build_artifact_member.py
python build_artifact_topic.py
python build_artifact_category.py
python build_artifact_home.py