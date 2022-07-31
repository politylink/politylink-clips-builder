from dataclasses import dataclass, field
from typing import Optional

from dataclasses_json import dataclass_json, LetterCase, config


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speaker:
    name: str
    info: str = ''


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Speech:
    speaker: Speaker
    speech: str


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Member:
    member_id: int
    name: str
    group: str
    block: str
    summary: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    ref_url: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))
    image_url: Optional[str] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Topic:
    topic_id: int
    title: str
    category_id: int


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class Category:
    category_id: int
    title: str
    desc: str


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
    member: Member
    topic_ids: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class ClipPage:
    clip: Clip
    speeches: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    clips: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
    topics: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class MemberPage:
    member: Member
    topics: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class TopicPage:
    topic: Topic
    topics: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class CategoryPage:
    category: Category
    topics: Optional[list] = field(default=None, metadata=config(exclude=lambda x: x is None))
