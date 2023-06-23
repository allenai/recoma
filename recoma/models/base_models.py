from typing import Optional
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchNode, SearchState
from recoma.utils.class_utils import RegistrableFromDict


class BaseModel(RegistrableFromDict):

    def __init__(self, next_model: Optional[str] =None):
        self.next_model = next_model

    def __call__(self, state: SearchState):
        generation_outputs = self.generate_output(state)
        new_states = self.build_new_states(state, generation_outputs)
        return new_states

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        raise NotImplementedError

    def build_new_states(self, state: SearchState, generation_outputs: GenerationOutputs):
        new_states = []
        for idx, output_str in enumerate(generation_outputs.outputs):
            new_state = state.clone(deep=True)
            open_node = new_state.get_open_node()
            open_node.close(output=output_str)
            if generation_outputs.scores:
                new_state.update_score(generation_outputs.scores[idx])
            if self.next_model is not None:
                new_state.add_node(node=SearchNode(input_str=output_str,
                                                   target_model=self.next_model,
                                                   metadata={}),
                                   parent=open_node)
            new_states.append(new_state)

        return new_states


# No need to register this class as it should only be used as a superclass for other models
class PromptedModel(BaseModel):
    def __init__(self, prompt_file: str, **kwargs):
        super().__init__(**kwargs)
        if prompt_file:
            with open(prompt_file, "r") as input_fp:
                self.prompt = "".join(input_fp.readlines())
        else:
            self.prompt = ""


