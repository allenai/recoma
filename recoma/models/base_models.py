from typing import Optional, List

from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState
from recoma.utils.class_utils import RegistrableFromDict


class BaseModel(RegistrableFromDict):

    def __init__(self, next_model: Optional[str] = None):
        self.next_model = next_model

    def __call__(self, state: SearchState):
        generation_outputs = self.generate_output(state)
        new_states = self.build_new_states(state, generation_outputs)
        return new_states

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        return None

    def build_new_states(self, state: SearchState,
                         generation_outputs: GenerationOutputs) -> List[SearchState]:
        """
        Build new state from the input search state. Generally, if the output is being consumed by
        the next model, create a new open node as the child of the current open node and assign the
        new child node to the next model. If the current model has some additional processing after
        the child node is done (e.g. iterative decomposition), keep the current node open otherwise
        close it. If there is no next model, just close the node.
        :param state: input state
        :param generation_outputs: output generations based on the input_str (generated using the
        :func:`recoma.BaseModel.generate_output` function)
        :return: a list of new states that can be explored further using search
        """
        new_states = []
        for idx, output_str in enumerate(generation_outputs.outputs):
            new_state = state.clone(deep=True)
            current_node = new_state.get_open_node()
            current_node.close(output=output_str)
            if generation_outputs.metadata:
                current_node.data.update(generation_outputs.metadata[idx])
            if generation_outputs.scores:
                new_state.update_score(generation_outputs.scores[idx])
            if self.next_model is not None:
                new_state.add_next_step(next_step_input=output_str,
                                        next_step_model=self.next_model,
                                        current_step_node=current_node)
            new_states.append(new_state)

        return new_states
