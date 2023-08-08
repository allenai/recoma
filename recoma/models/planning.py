import re
from typing import List

from recoma.models import PromptedLMModel
from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState


@BaseModel.register("planner_lm")
class PlannerLMModel(PromptedLMModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_char = "#"
        self.step_regex = re.compile("Step [0-9]+: (.*)")

    def parse_plan(self, gen_output):
        output_lines = [line.strip() for line in gen_output.split("\n")]
        filtered_lines = [line for line in output_lines
                          if (not line.startswith(self.comment_char)
                              and line)]
        steps = []
        for line in filtered_lines:
            re_match = self.step_regex.match(line)
            if re_match:
                steps.append(re_match.group(1))
            else:
                raise ValueError("Cannot parse line:{} in the generated plan!".format(line))
        return steps

    def build_new_states(self, state: SearchState,
                         generation_outputs: GenerationOutputs) -> List[SearchState]:
        new_states = []
        for gen_idx, gen_output in enumerate(generation_outputs.outputs):
            steps = self.parse_plan(gen_output)
            new_state = state.clone(deep=True)
            current_node = new_state.get_open_node()
            current_node.data["plan"] = steps
            first_step = steps[0]
            new_state.add_next_step(next_step_input=first_step,
                                    next_step_model=self.next_model,
                                    current_step_node=current_node)
            new_states.append(new_state)
        return new_states

    def __call__(self, state: SearchState) -> List[SearchState]:
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        children = new_state.get_children(current_node)
        if children:
            last_child = children[-1]
            # task succeeded
            steps = current_node.data["plan"]
            if len(steps) == len(children):
                # All steps processed
                current_node.close(last_child.output)
                return [new_state]
            else:
                # create a node for the next step in the plan
                next_step = steps[len(children)]
                new_state.add_next_step(next_step_input=next_step,
                                        next_step_model=self.next_model,
                                        current_step_node=current_node)
                return [new_state]
        else:
            return super().__call__(state)