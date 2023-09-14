from recoma.search.answerfromstate import AnswerFromState
from recoma.search.state import SearchState, SearchNode


@AnswerFromState.register("alf_reward")
class AlfRewardAnswerer(AnswerFromState):

    def __init__(self):
        super().__init__()

    def generate_answer(self, state: SearchState):
        return "SUCCESS" if get_reward(state.get_depth_nth_node(-3).data) else "FAILURE"


def get_observation(json_data):
    return json_data.get("obs")


def get_task_success(json_data):
    obs = get_observation(json_data)
    return obs.endswith("Task completed!") if obs is not None else None


def set_observation(node, observation):
    node.data["obs"] = observation


def get_reward(json_data):
    return json_data.get("reward")


def get_task_success_from_state(state: SearchState, node: SearchNode):
    if node.output:
        return node.output.endswith("Task completed!")
    else:
        children = state.get_children(node)
        if children:
            return get_task_success_from_state(state, children[-1])
    return False


def get_observation_from_state(state: SearchState, node: SearchNode):
    obs_node = get_observation(node.data)
    if obs_node is None:
        children = state.get_children(node)
        if children:
            return get_observation_from_state(state, children[-1])

    return obs_node


def extract_task(full_task_spec):
    task_prefix = "Your task is to: "
    task_idx = full_task_spec.find(task_prefix)
    if task_idx >= 0:
        full_task_spec = full_task_spec[task_idx + len(task_prefix):]
    newline_idx = full_task_spec.find("\n")
    if newline_idx >= 0:
        full_task_spec = full_task_spec[:newline_idx]
    return full_task_spec
