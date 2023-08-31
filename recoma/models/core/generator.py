from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any

from recoma.utils.class_utils import RegistrableFromDict


@dataclass
class GeneratorParams:
    temperature: float = 0
    max_tokens: int = 100
    top_p: float = 1
    frequency_penalty: float = 0
    presence_penalty: float = 0
    # needed to ensure new list is created for each param
    stop: list[str] = field(default_factory=lambda: ["\n"])
    num_sequences: int = 1
    best_of: int = 1
    topk_logprobs: int = 0


@dataclass
class GenerationOutputs:
    outputs: list[str]
    scores: list[float] = field(default_factory=lambda: [])
    metadata: list[dict[str, Any]] = field(default_factory=lambda: [])


class LMGenerator(RegistrableFromDict):
    """"
    Base LM Generator class. All text-to-text generators should inherit this base registrable class
    and implement the generate method
    """
    def __init__(self, **kwargs):
        self.generator_params = GeneratorParams(**kwargs)

    @abstractmethod
    def generate(self, input_str: str) -> GenerationOutputs:
        """
        All implementations must implement this generate function that takes input text and returns
        string as output
        """
        raise NotImplementedError
