#!/bin/zsh
set -eu

python clip_topic_match.py
python topic.py
python member_topic_match.py
python topic_topic_match.py
python build_artifact_clip.py
python build_artifact_member.py
python build_artifact_topic.py
