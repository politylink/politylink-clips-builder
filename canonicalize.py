import re
import unicodedata
from logging import getLogger

ALIAS_TO_NAME = {  # 質疑項目　-> 国会会議録
    '礒﨑哲史': '礒崎哲史',
    '高野光二郞': '高野光二郎',
    '髙良鉄美': '高良鉄美'
}
LOGGER = getLogger(__name__)


def canonicalize_name(name):
    if name in ALIAS_TO_NAME:
        return ALIAS_TO_NAME[name]
    return name


def extract_issue(text):
    """
    in: 令和４年２月２日（水）\u3000第１回
    out: 1
    """

    issue_p = r'第(\d+)[回|号]'
    m = re.search(issue_p, text)
    return int(m.group(1))


def clean_text(text):
    return ' '.join(text.strip().split())


def normalize_text(text):
    return unicodedata.normalize('NFKC', text)
