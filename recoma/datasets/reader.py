import abc
import random
from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Iterable


from recoma.utils.class_utils import RegistrableFromDict


class Example(abc.ABC):

    @staticmethod
    @abstractmethod
    def fields():
        raise NotImplementedError

    def get_field(self, field):
        return getattr(self, field)

    @property
    @abstractmethod
    def unique_id(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def task(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def label(self):
        raise NotImplementedError


@dataclass
class QAExample(Example):
    qid: str
    question: str
    gold_answer: Optional[str]
    paras: List[str]

    @staticmethod
    def fields():
        return ["qid", "question", "gold_answer", "paras"]

    @property
    def unique_id(self):
        return self.qid

    @property
    def task(self):
        return self.question

    @property
    def label(self):
        return self.gold_answer

    def __str__(self) -> str:
        return f"QAExample(qid={self.qid}, \
                 question={self.question}, \
                 gold_answer={self.gold_answer}, \
                 paras={self.paras})"


class DatasetReader(RegistrableFromDict):
    """
    Base Dataset Reader class
    """
    def __init__(self, top_k=None, sample_p=None):
        """
        Construct base DatasetReader class
        :param top_k: If set, only read the first top_k examples
        :param sample_p: If set (and top_k is not set), randomly select examples with sample_p
        probability
        """
        self.top_k = top_k
        self.sample_p = sample_p

    @abstractmethod
    def read_examples(self, file: Optional[str] = None) -> Iterable[Example]:
        """
        All implementations should implement this method to convert files into a stream of Examples
        :param file: input file to read from
        :return: streaming Example objects
        """
        raise NotImplementedError

    def get_examples(self, file: Optional[str] = None) -> Iterable[Example]:
        """
        Get examples from the input file by first reading them from file and then applying
        filters as defined in the constructor (e.g. top_k, sample_p)
        :param file: input file to read from
        :return: streaming Example objects (subject to conditions in constructor)
        """
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
            yield from self.read_examples(file)
