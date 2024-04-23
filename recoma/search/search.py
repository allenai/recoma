from curses import meta
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
    def __init__(self, model_list, start_model, renderers=None,
                 answerer=None, max_search_iters=100,
                 max_search_depth=100, output_dir=None, **kwargs):
        super().__init__(**kwargs)
        self.model_list = model_list
        self.answerer: AnswerFromState = TailOutputAnswerer() if answerer is None \
            else AnswerFromState.from_dict(answerer)
        self.start_model = start_model
        self.max_search_iters = max_search_iters
        self.max_search_depth = max_search_depth
        self.output_dir = output_dir
        self.renderers = renderers

    def execute(self, current_state: SearchState):
        open_node = current_state.get_open_node()
        if open_node is not None:
            target_model = open_node.target_model()
            if target_model not in self.model_list:
                logger.error("Can not handle next state: " + str(target_model))
                return []
            try:
                output_states = self.model_list[target_model](current_state)
                return output_states
            except RecursionError:
                return []
        else:
            raise ValueError("No open nodes in current state:" + str(current_state))

    def predict(self, example: Example) -> ExamplePrediction:
        raise NotImplementedError


def clean_name(qid):
    return qid.replace("/", "_").replace("\\", "_").replace(".", "_")


@SearchAlgo.register("best_first")
class BestFirstSearch(SearchAlgo):

    def predict(self, example):
        init_state = SearchState(example=example, data={})
        # add root node
        init_state.add_next_step(next_step_input=example.question,
                                 next_step_input_for_display=example.question,
                                 next_step_model=self.start_model,
                                 current_step_node=None)
        heap = []

        # push it to heap
        heapq.heappush(heap, init_state)

        # start the search
        iters = 0
        while iters < self.max_search_iters:
            # pop from heap
            current_state = heapq.heappop(heap)
            logger.debug("\n" + current_state.to_str_tree())
            if self.output_dir and self.renderers:
                for renderer in self.renderers:
                    filename = self.output_dir + "/" + clean_name(example.qid) + \
                        renderer.special_suffix + "." +  renderer.output_format
                    with open(filename, "w") as fp:
                        fp.write(renderer.output(current_state))
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
            for new_state in self.execute(current_state):
                # push onto heap if max depth not reached
                if new_state.depth() <= self.max_search_depth:
                    heapq.heappush(heap, new_state)
                else:
                    logger.warning("!HIT MAX DEPTH!: {}".format(example.qid))
            # Rather than failing at the beginning of the loop, fail at the end here and return the
            # current state
            if len(heap) == 0:
                answer = self.answerer.generate_answer(current_state)
                logger.warning("!EMPTY HEAP!: {}".format(example.qid))
                return ExamplePrediction(example=example, prediction=answer, final_state=current_state)
            iters += 1
        logger.warning("!SEARCH FAILED!: {}".format(example.qid))
        best_state = heapq.heappop(heap)
        answer = self.answerer.generate_answer(best_state)
        return ExamplePrediction(example=example,
                                 prediction=answer,
                                 final_state=best_state)
