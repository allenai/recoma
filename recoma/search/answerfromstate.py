from recoma.search.state import SearchState
from recoma.alfworld.alf_utils import get_reward
from recoma.utils.class_utils import RegistrableFromDict


class AnswerFromState(RegistrableFromDict):
    """
    Class that generates answer from the search state (i.e. execution trace)
    """
    def generate_answer(self, state: SearchState):
        raise NotImplementedError


@AnswerFromState.register("tail")
class TailOutputAnswerer(AnswerFromState):

    def __init__(self, n_tail: int = -1):
        super().__init__()
        self.n_tail = n_tail

    def generate_answer(self, state: SearchState):
        return state.get_depth_nth_node(self.n_tail).output


@AnswerFromState.register("root")
class RootAnswerer(AnswerFromState):

    def __init__(self):
        super().__init__()

    def generate_answer(self, state: SearchState):
        return state[state.root].output


@AnswerFromState.register("alf_reward")
class AlfRewardAnswerer(AnswerFromState):

    def __init__(self):
        super().__init__()

    def generate_answer(self, state: SearchState):
        return "SUCCESS" if get_reward(state.get_depth_nth_node(-2).data) else "FAILURE"
