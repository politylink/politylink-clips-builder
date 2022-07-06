import itertools
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

import pandas as pd
import requests
import spacy
from gensim.corpora import Dictionary
from gensim.models import TfidfModel
from politylink.graphql.client import GraphQLClient
from politylink.graphql.schema import Query, _BillFilter
from politylink.nlp.keyphrase import KeyPhraseExtractor
from politylink.nlp.utils import load_stopwords, STOPWORDS_SLOTHLIB_PATH
from sgqlc.operation import Operation
from spacy.lang.ja import stop_words
from spacy.tokens import Token

POS_TAGS = {'NOUN', 'PROPN', 'ADJ', 'ADV'}
ANNOTATIONS = ['〔[^〔〕]+〕', '─', '―']

STOPWORDS = {'さよう', 'やはり', 'ふう', 'まず', 'ことに', 'ただいま', 'しっかり', 'まあ', 'いわゆる', 'まさに', 'やっぱり'}
STOPWORDS.update(load_stopwords(STOPWORDS_SLOTHLIB_PATH))
STOPWORDS.update(stop_words.STOP_WORDS)

client = GraphQLClient('https://graphql.politylink.jp/')
nlp = spacy.load('ja_ginza')
key_phrase_extractor = KeyPhraseExtractor()


def fetch_bill(bill_id):
    op = Operation(Query)
    b = op.bill(filter=_BillFilter({'id': bill_id}))
    b.name()
    m = b.be_discussed_by_minutes()
    m.name()
    m.start_date_time()
    m.ndl_min_id()

    res = client.endpoint(op.__to_graphql__(auto_select_depth=1))
    bills = getattr(op + res, 'bill')
    return bills[0]


def fetch_minutes(ndl_min_id):
    url = 'https://kokkai.ndl.go.jp/api/meeting?issueID={}&recordPacking=JSON'.format(ndl_min_id)
    response = requests.get(url)
    return response.json()





@dataclass
class Speech:
    order: int
    doc: any
    speaker: str
    key_phrases: list

    @staticmethod
    def of(record):
        order = int(record['speechOrder'])
        text = clean_speech_text(record['speech'])
        doc = nlp(text)
        speaker = record['speaker']
        key_phrases = key_phrase_extractor.extract(doc, n=3)
        return Speech(order, doc, speaker, key_phrases)


Token.set_extension("is_compound", default=False, force=True)


def set_is_compound(doc):
    for token in doc:
        if token.dep_ == 'compound':
            first = min(token.i, token.head.i)
            last = max(token.i, token.head.i)
            for i in range(first, last + 1):
                doc[i]._.is_compound = True
    return doc


def extract_terms(doc, compound=False):
    if compound:
        set_is_compound(doc)

    terms = []
    buffer = ''
    for token in doc:
        if compound and token._.is_compound:
            buffer += token.text
        else:
            if buffer:  # flush buffer
                terms.append(buffer)
                buffer = ''
            if token.pos_ in POS_TAGS:  # flush token
                terms.append(token.text)
    if buffer:
        terms.append(buffer)

    terms = list(filter(lambda x: x not in STOPWORDS, terms))
    return terms


def calc_tf(speech_list, n=10):
    terms = list(itertools.chain(*map(lambda x: x.terms, speech_list)))
    counter = Counter(terms)
    return counter.most_common(n)


def to_speech_dict(speech_list):
    speech_dict = defaultdict(list)
    for speech in speech_list:
        speech_dict[speech.speaker].append(speech)
    return speech_dict


question_patterns = [
    'いただきたい',
    '願います',
    'よろしい',
    'いかが',
    'ですか',
    'でしょうか',
    'ますか',
    'お伺い',
    '伺いたい',
    'お願い',
    'ほしい',
    'ください'
]


def is_question(text):
    for p in question_patterns:
        if p in text:
            return True
    return False


def iter_docs(minutes_list):
    for minutes in minutes_list:
        for speech in minutes.speech_list:
            yield speech.doc


def calculate_lemma2idf(docs):
    lemmas_list = []
    for doc in docs:
        lemmas = [token.lemma_ for token in doc]
        lemmas_list.append(lemmas)
    dictionary = Dictionary(lemmas_list)
    corpus = [dictionary.doc2bow(lemmas) for lemmas in lemmas_list]
    model = TfidfModel(corpus)
    idfs = {}
    for key, val in model.idfs.items():
        idfs[dictionary[key]] = val
    return idfs


def merge_node(g, n, weight):
    if n in g.nodes:
        weight += g.nodes[n]['weight']
    g.add_node(n, weight=weight)


def merge_edge(g, n1, n2, weight):
    if (n1, n2) in g.edges:
        weight += g.edges[(n1, n2)]['weight']
    g.add_edge(n1, n2, weight=weight)


def to_node_df(g, weight_min=1):
    records = []
    for n, attr in g.nodes.data():
        weight = attr['weight']
        if weight >= weight_min:
            records.append({
                'id': n,
                'weight': weight
            })
    df = pd.DataFrame(records, columns=['id', 'weight'])
    return df


def to_edge_df(g, weight_min=1):
    records = []
    for n1, n2, attr in g.edges.data():
        weight = attr['weight']
        if weight >= weight_min:
            records.append({
                'source': n1,
                'target': n2,
                'weight': weight
            })
    df = pd.DataFrame(records, columns=['source', 'target', 'weight'])
    return df


def export_graph(g, node_fp, edge_fp, node_weight_min=1, edge_weight_min=1):
    node_df = to_node_df(g, node_weight_min)
    edge_df = to_edge_df(g, edge_weight_min)
    node_df.to_csv(node_fp, index=False)
    edge_df.to_csv(edge_fp, index=False)
