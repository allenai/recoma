import logging
import os
from typing import Any
import json
import litellm
from diskcache import Cache
from litellm import completion, completion_cost
from tenacity import (before_sleep_log, retry,  # for exponential backoff
                      stop_after_attempt, wait_random_exponential)

from recoma.models.core.generator import GenerationOutputs, LMGenerator

logger = logging.getLogger(__name__)

litellm.drop_params = True

cache = Cache(os.path.expanduser("~/.cache/litellmcalls"))


cache_hit = True

@cache.memoize()
def cached_litellm_call(
        model, messages, temperature, max_tokens, top_p, logprobs, top_logprobs,
        frequency_penalty, presence_penalty, stop, n, seed, response_format
):
    global cache_hit
    cache_hit = False
    return completion(model=model, messages=messages,
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


@LMGenerator.register("lite_llm")
class LiteLLMGenerator(LMGenerator):

    def __init__(self, model: str, use_cache: bool=False, **kwargs):
        super().__init__(**kwargs)
        self.use_cache = use_cache
        self.model = model

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(10),
           before_sleep=before_sleep_log(logger, logging.DEBUG))
    def completion_with_backoff(self, function, **kwargs) -> dict[Any, Any]:
        return function(**kwargs)

    def generate(self, input_str, state):
        messages_json = self.extract_role_messages(input_str)
        formatted_messages = json.dumps(messages_json, indent=2)
        logger.debug("Messages:\n{}\n...\n{}".format(formatted_messages[:200], formatted_messages[-200:]))
        generator_args = self.generator_params_to_args(self.generator_params)
        generator_args["messages"] = messages_json
        generator_args["model"] = self.model
        global cache_hit
        if self.use_cache and self.generator_params.temperature == 0:
            cache_hit = True
            function = cached_litellm_call
        else:
            cache_hit = False
            function = completion

        response = self.completion_with_backoff(function=function, **generator_args)

        try:
            cost = completion_cost(response)
            state.update_counter("litellm.{}.cost".format(self.model), cost)
        except:
            # Unknown model
            pass
        if cache_hit:
            state.update_counter("litellm.{}.cache_hit".format(self.model), 1)
        state.update_counter("litellm.{}.calls".format(self.model), 1)

        for usage_key in ["completion_tokens", "prompt_tokens", "total_tokens"]:
            if hasattr(response.usage, usage_key):
                count = getattr(response.usage, usage_key)
                state.update_counter("litellm.{}.{}".format(self.model, usage_key), count)

        generation_outputs = GenerationOutputs(outputs=[], scores=[])
        for index, choice in enumerate(response["choices"]):
            text_response = choice["message"]["content"]
            # print(formatted_messages)
            # print(text_response)
            # _ = input("Wait")
            # For some reason, the stop token does not always work!
            for stop_t in self.generator_params.stop:
                if stop_t in text_response:
                    stop_idx = text_response.index(stop_t)
                    text_response = text_response[:stop_idx]

            generation_outputs.outputs.append(text_response.lstrip())
        # JSON Formatted message, add to node
        if len(messages_json) > 1:
            open_node = state.get_open_node()
            open_node.add_input_output_prompt(formatted_messages, generation_outputs)

        return generation_outputs
