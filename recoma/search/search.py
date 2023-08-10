import heapq
import logging
from dataclasses import dataclass

from recoma.datasets.reader import Example
from recoma.search.answerfromstate import TailOutputAnswerer, AnswerFromState
from recoma.search.state import SearchState
from recoma.utils.class_utils import RegistrableFromDict

logger = logging.getLogger(__name__)


@dataclass
class ExamplePrediction:
    example: Example
    prediction: str
    final_state: SearchState = None


class SearchAlgo(RegistrableFromDict):
    def __init__(self, controller, start_model, answerer=None, max_search_iters=100,
                 output_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.controller = controller
        self.answerer = TailOutputAnswerer() if answerer is None \
            else AnswerFromState.from_dict(answerer)
        self.start_model = start_model
        self.max_search_iters = max_search_iters
        self.output_dir = output_dir

    def predict(self, example: Example) -> ExamplePrediction:
        return NotImplementedError


def clean_name(qid):
    return qid.replace("/", "_").replace("\\", "_").replace(".", "_")


@SearchAlgo.register("best_first")
class BestFirstSearch(SearchAlgo):

    def predict(self, example):

        init_state = SearchState(example=example)
        # add root node
        init_state.add_next_step(next_step_input=example.question,
                                 next_step_model=self.start_model,
                                 current_step_node=None)
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
            if self.output_dir:
                with open(clean_name(example.qid) + ".html", "w") as fp:
                    fp.write(current_state.to_html_tree())
            if not current_state.has_open_node():
                # found a solution
                answer = self.answerer.generate_answer(current_state)
                logger.info(example.question + "\t" + answer)
                return ExamplePrediction(example=example,
                                         prediction=answer,
                                         final_state=current_state)
            else:
                logger.debug("Exploring ====> " + current_state.get_open_node().tag)

            # generate new states
            for new_state in self.controller.execute(current_state):
                # push onto heap
                heapq.heappush(heap, new_state)
            iters += 1

        return ExamplePrediction(example=example,
                                 prediction="SEARCH FAILED",
                                 final_state=heapq.heappop(heap))
