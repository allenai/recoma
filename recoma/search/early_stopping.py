from collections import Counter
import logging
from abc import abstractmethod
import re

from recoma.search.state import SearchState
from recoma.utils.class_utils import RegistrableFromDict

logger = logging.getLogger(__name__)


class EarlyStoppingCondition(RegistrableFromDict):

    @abstractmethod
    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        raise NotImplementedError


@EarlyStoppingCondition.register("max_search_depth")
class MaxSearchDepth(EarlyStoppingCondition):
    def __init__(self, max_search_depth=100, **kwargs):
        super().__init__(**kwargs)
        self.max_search_depth = max_search_depth

    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        if current_state.depth() > self.max_search_depth:
            logger.warning("Hit max search depth: {} >= {}".format(current_state.depth(),
                                                                   self.max_search_depth))
            return True
        return False


@EarlyStoppingCondition.register("max_search_iters")
class MaxSearchIterations(EarlyStoppingCondition):
    def __init__(self, max_search_iters=100, **kwargs):
        super().__init__(**kwargs)
        self.max_search_iters = max_search_iters

    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        if num_iters >= self.max_search_iters:
            logger.warning("Hit max search iterations: {} >= {}".format(num_iters,
                                                                        self.max_search_iters))
            return True
        return False

@EarlyStoppingCondition.register("max_llm_calls")
class MaximumLLMCalls(EarlyStoppingCondition):
    def __init__(self, max_llm_calls=200, **kwargs):
        super().__init__(**kwargs)
        self.max_llm_calls = max_llm_calls

    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        counter = Counter()
        for key, value in current_state.data.items():
            m = re.match("openai.(.*).calls", key)
            if m:
                counter[m.group(1)] += value
            m = re.match("litellm.(.*).calls", key)
            if m:
                counter[m.group(1)] += value
        num_calls = sum(counter.values())
        if num_calls >= self.max_llm_calls:
            logger.warning("Hit max calls: {} >= {}".format(num_calls, self.max_llm_calls))
            return True
        return False

@EarlyStoppingCondition.register("max_llm_cost")
class MaximumLLMCost(EarlyStoppingCondition):
    def __init__(self, max_llm_cost=2.00, **kwargs):
        super().__init__(**kwargs)
        self.max_llm_cost = max_llm_cost

    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        counter = Counter()
        for key, value in current_state.data.items():
            m = re.match("openai.(.*).cost", key)
            if m:
                counter[m.group(1)] += value
            m = re.match("litellm.(.*).cost", key)
            if m:
                counter[m.group(1)] += value
        total_cost = sum(counter.values())
        if total_cost >= self.max_llm_cost:
            logger.warning("Hit max cost: {} >= {}".format(total_cost, self.max_llm_cost))
            return True
        return False
