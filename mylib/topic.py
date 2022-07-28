from collections import Counter
from dataclasses import dataclass

import spacy

nlp = spacy.load('ja_ginza')


@dataclass
class Topic:
    topic_id: int
    condition: str  # e.g. "foo bar;baz" = (foo AND bar) OR (baz)
    clip_id_list: list

    def matches(self, text):
        for item in self.condition.split(';'):
            is_match = True
            for phrase in item.split():
                if phrase not in text:
                    is_match = False
            if is_match:
                return True
        return False


@dataclass
class Clip:
    clip_id: int
    title: str
    phrase_list: list  # list of noun phrases
    topic_id_list: list

    @staticmethod
    def of(clip_id, title):
        return Clip(
            clip_id=clip_id,
            title=title,
            phrase_list=extract_phrase_list(title),
            topic_id_list=list()
        )


def extract_phrase_list(text):
    with nlp.select_pipes(enable=['parser']):
        doc = nlp(text)

    phrase_list = []
    buffer = ''
    for i, token in enumerate(doc):
        if token.pos_ in ['NOUN', 'PROPN']:
            buffer += token.text
            continue
        if buffer:
            phrase_list.append(buffer)
            buffer = ''
    if buffer:
        phrase_list.append(buffer)

    return phrase_list


class TopicGenerator:
    """
    Helper class to define topics manually
    """

    def __init__(self, clip_list):
        self.clip_map = dict()
        for clip in clip_list:
            self.clip_map[clip.clip_id] = clip

        self.condition_set = set()
        self.topic_map = dict()
        self.next_topic_id = 1

    def generate(self, condition):
        topic = Topic(topic_id=self.next_topic_id, condition=condition, clip_id_list=list())
        self.next_topic_id += 1
        return topic

    def add(self, condition):
        if condition not in self.condition_set:
            self.condition_set.update((condition,))
            topic = self.generate(condition)
            self.set(topic)

    def set(self, topic):
        self.topic_map[topic.topic_id] = topic
        self._index(topic.topic_id)

    def get(self, topic_id):
        return self.topic_map[topic_id]

    def suggest(self, topic_id='default', len_thresh=4):
        """
        suggest candidate topics
        """

        clip_id_list = []
        if topic_id == 'default':  # use clips without topic
            for clip_id, clip in self.clip_map.items():
                if not clip.topic_id_list:
                    clip_id_list.append(clip_id)
        elif topic_id == 'all':  # use all clips
            clip_id_list = self.clip_map.keys()
        else:  # use clips belong to the topic_id
            clip_id_list = self.topic_map[int(topic_id)].clip_id_list

        counter = Counter()
        for clip_id in clip_id_list:
            clip = self.clip_map[clip_id]
            for phrase in clip.phrase_list:
                if len(phrase) >= len_thresh:
                    counter[phrase] += 1
        return counter

    def _index(self, topic_id):
        topic = self.topic_map[topic_id]
        for clip in self.clip_map.values():
            if topic.matches(clip.title):
                clip.topic_id_list.append(topic.topic_id)
                topic.clip_id_list.append(clip.clip_id)
