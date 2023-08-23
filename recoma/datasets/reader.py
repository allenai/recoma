import random
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

    def __init__(self, add_paras=False, top_k=None, sample_p=None):
        self.add_paras = add_paras
        self.top_k = top_k
        self.sample_p = sample_p

    def read_examples(self, file: str):
        raise NotImplementedError

    def get_examples(self, file: str):
        if self.top_k:
            counter = 0
            for example in self.read_examples(file):
                if counter < self.top_k:
                    counter += 1
                    yield example
                else:
                    break
        elif self.sample_p:
            for example in self.read_examples(file):
                if random.random() < self.sample_p:
                    yield example
        else:
            yield self.read_examples(file)
