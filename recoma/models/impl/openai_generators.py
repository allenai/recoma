import json
import logging
import os
from litellm import completion_cost

from openai.types.chat.chat_completion import ChatCompletion
from diskcache import Cache
from tenacity import (before_sleep_log, retry,  # for exponential backoff
                      stop_after_attempt, wait_random_exponential)

from recoma.models.core.generator import GenerationOutputs, LMGenerator
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)

cache = Cache(os.path.expanduser("~/.cache/gpt3calls"))
cache_hit = True

@cache.memoize(ignore=("client"))
def cached_openai_chat_call(
        client, model, messages, temperature, max_tokens, top_p, logprobs, top_logprobs,
        frequency_penalty, presence_penalty, stop, n, seed, response_format
):
    global cache_hit
    cache_hit = False
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

        global cache_hit
        if self.use_cache and self.generator_params.temperature == 0 and "o1" not in self.model:
            function = cached_openai_chat_call
            generator_args["client"] = self.client
            cache_hit = True
        else:
            cache_hit = False
            function = self.client.chat.completions.create

        if "o1" in self.model:
            # Change argeument to max_completion_tokens, set temperature to 1.0, and remove stop
            generator_args["max_completion_tokens"] = generator_args.pop("max_tokens")
            generator_args["temperature"] = 1.0
            generator_args.pop("stop")

        response: ChatCompletion = self.completion_with_backoff(function=function, **generator_args)
        try:
            cost = completion_cost(response)
            state.update_counter("openai.{}.cost".format(self.model), cost)
        except:
            # Unknown model
            pass
        if cache_hit:
            state.update_counter("openai.{}.cache_hit".format(self.model), 1)
        generation_outputs = GenerationOutputs(outputs=[], scores=[])
        state.update_counter("openai.{}.calls".format(self.model), 1)
        for usage_key, count in response.usage.__dict__.items():
            if isinstance(count, int) or isinstance(count, float):
                state.update_counter("openai.{}.{}".format(
                    self.model, usage_key), count)

        for index, choice in enumerate(response.choices):
            text_response = choice.message.content.lstrip() if choice.message.content else ""
            # no scores in chat mode
            generation_outputs.outputs.append(text_response)

        return generation_outputs
