import json
import logging
from math import log
import os
from calendar import c
from http import client
from typing import Any
from litellm import completion_cost
import openai
from openai.types.chat.chat_completion import ChatCompletion
from diskcache import Cache
from tenacity import (before_sleep_log, retry,  # for exponential backoff
                      stop_after_attempt, wait_random_exponential)

from recoma.models.core.generator import GenerationOutputs, LMGenerator
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)

cache = Cache(os.path.expanduser("~/.cache/gpt3calls"))


@cache.memoize(ignore=("client"))
def cached_openai_chat_call(
        client, model, messages, temperature, max_tokens, top_p, logprobs, top_logprobs,
        frequency_penalty, presence_penalty, stop, n, seed, response_format
):
    return client.chat.completions.create(model=model, messages=messages,
                                          temperature=temperature,
                                          max_tokens=max_tokens,
                                          top_p=top_p,
                                          logprobs=logprobs,
                                          top_logprobs=top_logprobs,
                                          n=n,
                                          stop=stop,
                                          seed=seed,
                                          frequency_penalty=frequency_penalty,
                                          presence_penalty=presence_penalty,
                                          response_format=response_format)


@LMGenerator.register("openai_chat")
class OpenAIChatGenerator(LMGenerator):

    def __init__(self, model: str, use_cache=False, **kwargs):
        super().__init__(**kwargs)
        from openai import OpenAI
        self.client = OpenAI()
        self.model = model
        self.use_cache = use_cache

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(10),
           before_sleep=before_sleep_log(logger, logging.DEBUG))
    def completion_with_backoff(self, function, **kwargs) -> ChatCompletion:
        return function(**kwargs)

    def generate(self, input_str, state: SearchState):
        messages_json = self.extract_role_messages(input_str)
        logger.debug("Messages:\n{}".format(json.dumps(messages_json, indent=2)[:100]))
        generator_args = self.generator_params_to_args(self.generator_params)
        generator_args["messages"] = messages_json
        generator_args["model"] = self.model

        if self.use_cache and self.generator_params.temperature == 0:
            function = cached_openai_chat_call
            generator_args["client"] = self.client
        else:
            function = self.client.chat.completions.create

        response: ChatCompletion = self.completion_with_backoff(function=function, **generator_args)
        try:
            cost = completion_cost(response)
            state.update_counter("openai.{}.cost".format(self.model), cost)
        except:
            # Unknown model
            pass
        generation_outputs = GenerationOutputs(outputs=[], scores=[])
        state.update_counter("openai.{}.calls".format(self.model), 1)
        for usage_key, count in response.usage.__dict__.items():
            state.update_counter("openai.{}.{}".format(
                self.model, usage_key), count)

        for index, choice in enumerate(response.choices):
            text_response = choice.message.content.lstrip() if choice.message.content else ""
            # no scores in chat mode
            generation_outputs.outputs.append(text_response)

        return generation_outputs
