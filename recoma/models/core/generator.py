import json
import re
from abc import abstractmethod
from ast import List
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from recoma.search.state import SearchState
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
    logprobs: bool = False
    top_logprobs: Optional[int] = None
    seed: Optional[int] = None
    json_format: bool = False


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

    def __init__(self, drop_params=[], **kwargs):
        self.drop_params = drop_params
        self.generator_params = GeneratorParams(**kwargs)

    @abstractmethod
    def generate(self, input_str: str, current_state: SearchState) -> GenerationOutputs:
        """
        All implementations must implement this generate function that takes input text and current
        search state. Returns GenerationOutputs as output.
        """
        raise NotImplementedError

    def extract_role_messages(self, input_str):
        # TODO Find a better way to handle JSON inputs
        if "\"role\": \"user\"" in input_str:
            messages_json = json.loads(input_str)
        elif "ASSISTANT:\n" in input_str:
            messages_json = []
            last_start = 0
            for m in re.finditer("(USER|ASSISTANT|SYSTEM):\n", input_str, flags=re.IGNORECASE):
                last_end = m.span()[0]
                if len(messages_json) == 0:
                    if last_end != 0:
                        raise ValueError("Start of the prompt has no assigned role: {}".format(
                            input_str[:last_end]))
                else:
                    messages_json[-1]["content"] = input_str[last_start:last_end]
                mesg_type = m.group(1).lower()
                messages_json.append({"role": mesg_type, "content": None})
                last_start = m.span()[1]
            messages_json[-1]["content"] = input_str[last_start:]
        else:
            messages_json = [
                {"role": "user", "content": input_str}
            ]
        return messages_json

    def generator_params_to_args(self, generator_params: GeneratorParams):
        kwargs = {
            "temperature": generator_params.temperature,
            "max_tokens": generator_params.max_tokens,
            "top_p": generator_params.top_p,
            "n": generator_params.num_sequences,
            "logprobs": generator_params.logprobs,
            "top_logprobs": generator_params.top_logprobs,
            "frequency_penalty": generator_params.frequency_penalty,
            "presence_penalty": generator_params.presence_penalty,
            "stop": generator_params.stop,
            "seed": generator_params.seed
        }
        if generator_params.json_format:
            kwargs["response_format"] = { "type": "json_object" }
        else:
            kwargs["response_format"] = { "type": "text" }

        for param in self.drop_params:
            kwargs.pop(param, None)
        return kwargs