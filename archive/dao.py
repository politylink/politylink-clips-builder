import copy
import pickle
import re
from dataclasses import dataclass
from pathlib import Path

import requests
import spacy
from politylink.nlp.keyphrase import KeyPhraseExtractor
from spacy.tokens import Doc, DocBin
from tqdm import tqdm

ANNOTATIONS = ['〔[^〔〕]+〕', '─', '―']

nlp = spacy.load('ja_ginza')
key_phrase_extractor = KeyPhraseExtractor()


@dataclass
class Minutes:
    ndl_id: str
    name: str
    date: str
    speech_list: list

    @staticmethod
    def of(meeting_record):
        speech_list = list()
        for speech_record in tqdm(meeting_record['speechRecord']):
            speech_list.append(Speech.of(speech_record))

        return Minutes(
            ndl_id=meeting_record['issueID'],
            name=meeting_record['nameOfHouse'] + meeting_record['nameOfMeeting'],
            date=meeting_record['date'],
            speech_list=speech_list
        )

    def dump(self, path: Path):
        minutes_dump = copy.deepcopy(self)

        # need to separate Spacy Docs to avoid pickling whole vocabulary
        # https://spacy.io/usage/saving-loading#docs
        doc_bin = DocBin()
        for speech in minutes_dump.speech_list:
            doc_bin.add(speech.doc)
            speech.doc = None

        with open(path.with_suffix('.pkl'), 'wb') as f:
            pickle.dump(minutes_dump, f)
        doc_bin.to_disk(path.with_suffix('.scapy'))

    @staticmethod
    def load(path: Path):
        with open(path.with_suffix('.pkl'), 'rb') as f:
            minutes = pickle.load(f)

        doc_bin = DocBin().from_disk(path.with_suffix('.scapy'))
        docs = list(doc_bin.get_docs(nlp.vocab))
        assert len(docs) == len(minutes.speech_list)

        for speech, doc in zip(minutes.speech_list, docs):
            speech.doc = doc
        return minutes

    @staticmethod
    def exists(path: Path):
        for suffix in ['.pkl', '.scapy']:
            if not path.with_suffix(suffix).exists():
                return False
        return True


@dataclass
class Speech:
    order: int
    speaker: str
    doc: Doc
    key_phrase_list: list

    @staticmethod
    def of(speech_record):
        text = clean_speech_text(speech_record['speech'])
        with nlp.select_pipes(enable=['parser']):
            doc = nlp(text)
        key_phrase_list = key_phrase_extractor.extract(doc, n=3)

        return Speech(
            order=int(speech_record['speechOrder']),
            speaker=speech_record['speaker'],
            doc=doc,
            key_phrase_list=key_phrase_list
        )


def clean_speech_text(text):
    cleaned = ''.join(text.split()[1:])  # drop name
    return re.sub('|'.join(ANNOTATIONS), '', cleaned)  # remove all annotations


class MinutesDao:
    cache_directory = Path('../data/minutes')

    def get(self, ndl_id, cache=True):
        path = self.cache_directory / ndl_id
        if cache and Minutes.exists(path):
            return Minutes.load(path)
        minutes = self._fetch(ndl_id)
        minutes.dump(path)
        return minutes

    def _fetch(self, ndl_id):
        url = 'https://kokkai.ndl.go.jp/api/meeting?issueID={}&recordPacking=JSON'.format(ndl_id)
        response = requests.get(url)
        data = response.json()
        meeting_record = data['meetingRecord'][0]
        return Minutes.of(meeting_record)
