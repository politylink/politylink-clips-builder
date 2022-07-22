from collections import defaultdict
from dataclasses import dataclass

import ahocorasick
import numpy as np

from archive.dao import Speech


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


def iter_key_tokens(speech: Speech):
    for key_phrase in speech.key_phrase_list:
        for token in key_phrase.split():
            yield token


def calc_dist(s1: Speech, s2: Speech):
    """
    キーフレーズに含まれるトークンのうち、共通しない割合を距離として定義する
    """

    num_token = 0
    num_match = 0

    for self, other in [(s1, s2), (s2, s1)]:
        for token in iter_key_tokens(self):
            num_token += 1
            if token in other.doc.text.lower():
                num_match += 1

    if num_token == 0:
        return 1

    return 1 - num_match / num_token


def calc_dist_fast(i: int, j: int, tokens_i: list, tokens_j: list, token_finder: TokenFinder):
    """
    トークンの座標を事前計算しておくことで calc_distを高速化したもの
    """

    num_token = 0
    num_match = 0

    for tokens, other in [(tokens_i, j), (tokens_j, i)]:
        for token in tokens:
            num_token += 1
            if token_finder.find(token, other):
                num_match += 1

    if num_token == 0:
        return 1

    return 1 - num_match / num_token


def calc_dist_mat(speech_list):
    key_tokens = set()
    for speech in speech_list:
        key_tokens.update(iter_key_tokens(speech))

    token_finder = TokenFinder(key_tokens)
    for i, speech in enumerate(speech_list):
        token_finder.index(i, speech.doc.text.lower())  # key tokens are all lower case

    num_speech = len(speech_list)
    dist_mat = np.ones((num_speech, num_speech))
    for i, si in enumerate(speech_list):
        for j, sj in enumerate(speech_list):
            dist = calc_dist_fast(i, j, list(iter_key_tokens(si)), list(iter_key_tokens(sj)), token_finder)
            dist_mat[i][j] = dist
            dist_mat[j][i] = dist

    # ignore speech without key phrases
    for i, speech in enumerate(speech_list):
        if not speech.key_phrase_list:
            dist_mat[i, :] = 1
            dist_mat[:, i] = 1

    return dist_mat


@dataclass
class Cluster:
    centroid: int
    core_list: list
    sub_list: list


def find_cluster(dist_mat, core_thresh=0.5, sub_thresh=0.75) -> Cluster:
    """
    コアサイズが最大のクラスタを探す
    """

    clusters = []
    num_speech = dist_mat.shape[0]
    for i in range(num_speech):
        cluster = Cluster(centroid=i, core_list=list(), sub_list=list())
        for j in range(num_speech):
            dist = dist_mat[i][j]
            if dist <= core_thresh:
                cluster.core_list.append(j)
            if dist <= sub_thresh:
                cluster.sub_list.append(j)
        clusters.append(cluster)

    return max(clusters, key=lambda x: len(x.core_list))


def find_clusters(speech_list, n=10, min_core_size=3):
    """
    貪欲にクラスタを選んでいく
    """

    dist_mat = calc_dist_mat(speech_list)

    clusters = []
    for _ in range(n):
        cluster = find_cluster(dist_mat)
        if len(cluster.core_list) < min_core_size:
            break
        clusters.append(cluster)

        # ignore neighbors from the next iteration
        for i in cluster.sub_list:
            dist_mat[i, :] = 1
            dist_mat[:, i] = 1

    return clusters
