import logging
from abc import abstractmethod

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
            logger.warning("!HIT MAX DEPTH!: {}".format(
                current_state.example.unique_id))
            return True
        return False


@EarlyStoppingCondition.register("max_search_iters")
class MaxSearchIterations(EarlyStoppingCondition):
    def __init__(self, max_search_iters=100, **kwargs):
        super().__init__(**kwargs)
        self.max_search_iters = max_search_iters

    def should_stop(self, current_state: SearchState, num_iters: int, heap: list[SearchState]):
        return num_iters > self.max_search_iters
