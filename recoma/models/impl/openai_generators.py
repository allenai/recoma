import json
import logging
import os
from typing import Any

import openai
from diskcache import Cache
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    before_sleep_log
)  # for exponential backoff

from recoma.models.core.generator import LMGenerator, GenerationOutputs

logger = logging.getLogger(__name__)

cache = Cache(os.path.expanduser("~/.cache/gpt3calls"))


@cache.memoize()
def cached_openai_call(  # kwargs doesn't work with caching
        prompt, engine, temperature, max_tokens, top_p,
        frequency_penalty, presence_penalty, stop,
        n, best_of, logprobs,
):
    return openai.Completion.create(
        prompt=prompt, engine=engine, temperature=temperature, max_tokens=max_tokens,
        top_p=top_p, frequency_penalty=frequency_penalty, presence_penalty=presence_penalty,
        stop=stop, n=n, best_of=best_of, logprobs=logprobs
    )


def generator_params_to_args(generator_params, is_chat_model=False):
    kwargs = {
        "temperature": generator_params.temperature,
        "max_tokens": generator_params.max_tokens,
        "top_p": generator_params.top_p,
        "n": generator_params.num_sequences,
        "logprobs": generator_params.topk_logprobs,
        "frequency_penalty": generator_params.frequency_penalty,
        "presence_penalty": generator_params.presence_penalty,
        "stop": generator_params.stop
    }
    # only add this parameter if needed. Does not accept None and passing default=1 will still
    # trigger a check for n < best_of
    if generator_params.best_of is not None:
        kwargs["best_of"] = generator_params.best_of

    # remove args that don't apply to chat models
    if is_chat_model:
        del kwargs["best_of"]
        del kwargs["logprobs"]
    return kwargs


@LMGenerator.register("openai_completion")
class GPT3CompletionGenerator(LMGenerator):

    def __init__(self, engine: str, use_cache=True, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.use_cache = use_cache

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(20),
           before_sleep=before_sleep_log(logger, logging.DEBUG))
    def completion_with_backoff(self, function, **kwargs) -> dict[Any, Any]:
        return function(**kwargs)

    def generate(self, input_str):
        # GPT3 can't handle trailing white-space
        prompt = input_str.rstrip()
        if self.use_cache and self.generator_params.temperature == 0:
            function = cached_openai_call
        else:
            function = openai.Completion.create

        generator_args = generator_params_to_args(self.generator_params)
        generator_args["prompt"] = prompt
        generator_args["engine"] = self.engine
        response: dict[Any, Any] = self.completion_with_backoff(
            function=function, **generator_args)

        generation_outputs = GenerationOutputs(outputs=[], scores=[])

        for index, choice in enumerate(response["choices"]):
            if "logprobs" in choice and "token_logprobs" in choice["logprobs"]:
                # get probs of the tokens used in text (i.e. till the stop token)
                probs = []
                for prob, tok in zip(choice["logprobs"]["token_logprobs"],
                                     choice["logprobs"]["tokens"]):
                    if tok not in self.generator_params.stop and tok != "<|endoftext|>":
                        probs.append(prob)
                    else:
                        # include the probability of the stop character too. This will also
                        # ensure that an empty string (i.e. first predicted character being a stop
                        # character) also has a reasonable probability measure
                        probs.append(prob)
                        break
                # average the logits and negate to make them +ve scores where lower is better
                # set a high +ve score if no predictions
                score = -sum(probs) / len(probs) if len(probs) else 100.0
                generation_outputs.outputs.append(choice["text"].lstrip())
                generation_outputs.scores.append(score)
            else:
                # no score
                generation_outputs.outputs.append(choice["text"].lstrip())

        return generation_outputs


@cache.memoize()
def cached_openai_chat_call(  # kwargs doesn't work with caching
        model, messages, temperature, max_tokens, top_p,
        frequency_penalty, presence_penalty, stop, n
):
    return openai.ChatCompletion.create(model=model, messages=messages,
                                        temperature=temperature,
                                        max_tokens=max_tokens,
                                        top_p=top_p,
                                        n=n,
                                        stop=stop,
                                        frequency_penalty=frequency_penalty,
                                        presence_penalty=presence_penalty)


@LMGenerator.register("openai_chat")
class GPT3ChatGenerator(LMGenerator):

    def __init__(self, engine: str, use_cache=False, **kwargs):
        super().__init__(**kwargs)
        self.engine = engine
        self.use_cache = use_cache

    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(10),
           before_sleep=before_sleep_log(logger, logging.DEBUG))
    def completion_with_backoff(self, function, **kwargs) -> dict[Any, Any]:
        return function(**kwargs)

    def generate(self, input_str):
        # TODO Find a better way to handle JSON inputs
        if "\"role\": \"user\"" in input_str:
            messages_json = json.loads(input_str)
        else:
            messages_json = [
                {"role": "user", "content": input_str}
            ]
        if self.use_cache and self.generator_params.temperature == 0:
            function = cached_openai_chat_call
        else:
            function = openai.ChatCompletion.create

        generator_args = generator_params_to_args(self.generator_params, is_chat_model=True)
        generator_args["messages"] = messages_json
        generator_args["model"] = self.engine
        response: dict[Any, Any] = self.completion_with_backoff(
            function=function, **generator_args)

        generation_outputs = GenerationOutputs(outputs=[], scores=[])

        for index, choice in enumerate(response["choices"]):
            text_response = choice["message"]["content"].lstrip()
            # no scores in chat mode
            generation_outputs.outputs.append(text_response)

        return generation_outputs
