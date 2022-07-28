from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import dataclass_json, LetterCase, config


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speaker:
    name: str
    info: str = ''
    group: str = ''
    block: str = ''
    member_id: int = -1


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speech:
    speaker: Speaker
    speech: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Clip:
    clip_id: int
    title: str
    date: str
    house: str
    meeting: str
    minutes_url: str
    video_url: str
    category_id: int
    topic_ids: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    speaker: Optional[Speaker] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ClipPage:
    clip: Clip
    speeches: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    speakers: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    clips: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Member:
    member_id: int
    name: str
    url: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Topic:
    topic_id: int
    title: str
    category_id: int
    clip_count: str
