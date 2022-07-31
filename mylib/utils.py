import json
from collections import defaultdict

import ahocorasick
import pandas as pd

from mylib.artifact import Topic


def load_minutes_record(minutes_id):
    minutes_fp = f'./out/minutes/{minutes_id}.json'
    return load_json(minutes_fp)


def load_gclip_record(gclip_id):
    gclip_fp = f'./out/gclip/{gclip_id}.json'
    return load_json(gclip_fp)


def load_json(fp):
    with open(fp, 'r') as f:
        data = json.load(f)
    return data


def load_minutes_text(minutes_id, speech_id):
    minutes_record = load_minutes_record(minutes_id)
    return minutes_record['speechRecord'][speech_id]['speech']


def load_gclip_text(gclip_id, start_msec):
    gclip_record = load_gclip_record(gclip_id)
    for speech in gclip_record['speech_list']:
        if speech['start_msec'] == start_msec:
            return speech['speech']


def to_time_str(msec):
    s_msec = 1000
    m_msec = 60 * 1000
    h_msec = 60 * 60 * 1000

    s = ''
    if msec >= h_msec:
        hour = msec // h_msec
        msec = msec % h_msec
        s += f'{hour}h'
    if msec >= m_msec:
        minutes = msec // m_msec
        msec = msec % m_msec
        s += f'{minutes}m'
    sec = msec // s_msec
    s += f'{sec}s'
    return s


class TokenFinder:
    def __init__(self, tokens):
        self.automaton = ahocorasick.Automaton()
        for token in tokens:
            self.automaton.add_word(token, token)
        self.automaton.make_automaton()

        self.index_ = defaultdict(lambda: defaultdict(list))  # key1: token, key2: speech id, val: list of (start, end)
        self.token_index = defaultdict(set)  # key: token, val: set of speech ids
        self.speech_index = defaultdict(set)  # key: speech_id, val: set of tokens

    def index(self, id_, text):
        for last, token in self.automaton.iter(text):
            end = last + 1
            start = end - len(token)
            assert text[start:end] == token

            self.index_[token][id_].append((start, end))
            self.token_index[token].update((id_,))
            self.speech_index[id_].update((token,))

    def find(self, token=None, id_=None):
        if token is None and id_ is None:
            raise ValueError('need to specify token or speech id')
        elif token is None:
            return self.speech_index[id_]
        elif id_ is None:
            return self.token_index[token]
        else:
            return self.index_[token][id_]


def to_token_list(doc):
    pos_set = {'ADJ', 'ADV', 'NOUN', 'PROPN'}
    return [token.text for token in doc if token.pos_ in pos_set]


def to_token_set(doc):
    return set(to_token_list(doc))


def flatten_id_list(df, list_column, flat_column):
    df[list_column] = df[list_column].apply(lambda x: x.split(';'))
    df = df.explode(list_column).rename(columns={list_column: flat_column})
    df[flat_column] = df[flat_column].astype(int)
    return df


def load_topic_map(topic_fp):
    topic_df = pd.read_csv(topic_fp)
    topic_map = dict()
    for _, row in topic_df.iterrows():
        topic_id = row['topic_id']
        topic = Topic(topic_id=topic_id, title=row['title'], category_id=row['category_id'])
        topic_map[topic_id] = topic
    return topic_map
