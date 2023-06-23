from dataclasses import dataclass
from typing import List, Optional

from recoma.utils.class_utils import RegistrableFromDict


@dataclass
class Example:
    qid: str
    question: str
    gold_answer: Optional[str]
    paras: List[str]


class DatasetReader(RegistrableFromDict):

    def __init__(self, add_paras=False):
        self.add_paras = add_paras

    def read_examples(self, file: str):
        raise NotImplementedError
