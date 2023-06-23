import heapq
import logging
from dataclasses import dataclass

from recoma.search.answerfromstate import TailOutputAnswerer

from recoma.datasets.reader import Example
from recoma.search.state import SearchState
from recoma.utils.class_utils import RegistrableFromDict
from recoma.search.state import SearchNode

logger = logging.getLogger(__name__)


@dataclass
class ExamplePrediction:
    example: Example
    prediction: str
    final_state: SearchState = None


class SearchAlgo(RegistrableFromDict):
    def __init__(self, controller, start_model, answerer=None, max_search_iters=100,
                 **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.answerer = TailOutputAnswerer() if answerer is None else answerer
        self.start_model = start_model
        self.max_search_iters = max_search_iters

    def predict(self, example: Example) -> ExamplePrediction:
        return NotImplementedError


@SearchAlgo.register("best_first")
class BestFirstSearch(SearchAlgo):

    def predict(self, example):

        init_state = SearchState(example=example)
        # add root node
        # print("Adding node!")
        init_state.add_node(SearchNode(input_str=example.question,
                                       target_model=self.start_model,
                                       is_open=True,
                                       output=None,
                                       metadata={}))
        heap = []

        # push it to heap
        heapq.heappush(heap, init_state)

        # start the search
        iters = 0
        while iters < self.max_search_iters:
            if len(heap) == 0:
                logger.debug("[FAILED]: " + str(example))
                return ExamplePrediction(example=example, prediction="")

            # pop from heap
            current_state = heapq.heappop(heap)
            logger.debug("\n" + current_state.to_str_tree())

            if not current_state.has_open_node():
                # found a solution
                return ExamplePrediction(example=example,
                                         prediction=self.answerer.generate_answer(current_state),
                                         final_state=current_state)
            else:
                logger.debug("Exploring ====> " + current_state.get_open_node().tag)

            # generate new states
            for new_state in self.controller.execute(current_state):
                # push onto heap
                heapq.heappush(heap, new_state)
            iters += 1
