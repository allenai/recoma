import re
from dataclasses import dataclass
from typing import List

from recoma.alfworld.alf_utils import set_observation, get_task_success_from_state, extract_task

from recoma.models import PromptedLMModel
from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState


@dataclass
class Plan:
    steps: List[str]
    logic: str


@BaseModel.register("alf_planner")
class AlfWorldPlanner(PromptedLMModel):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.comment_char = "#"
        self.step_regex = re.compile("Step [0-9]+: (.*)")
        self.logic_marker = "Logic: "

    def parse_plan(self, gen_output):
        output_lines = [line.strip() for line in gen_output.split("\n")]
        filtered_lines = [line for line in output_lines
                          if (not line.startswith(self.comment_char)
                              and line)]
        steps = []
        logic = "AND"
        for line in filtered_lines:
            re_match = self.step_regex.match(line)
            if re_match:
                steps.append(re_match.group(1))
            elif line.startswith(self.logic_marker):
                logic = line[len(self.logic_marker):]
            else:
                raise ValueError("Cannot parse line:{} in the generated plan!".format(line))
        return Plan(steps=steps, logic=logic)

    def build_next_input(self, original_question: str, new_goal: str,
                         last_outputs: List[str] = []):
        modified_question = re.sub("Your task is to: .*\\.",
                                   "Your task is to: {}".format(new_goal),
                                   original_question)
        for output in last_outputs:
            modified_question += "\nCompleted tasks: " + output

        return modified_question

    def build_new_states(self, state: SearchState,
                         generation_outputs: GenerationOutputs) -> List[SearchState]:
        new_states = []
        for gen_idx, gen_output in enumerate(generation_outputs.outputs):
            parsed_plan = self.parse_plan(gen_output)
            new_state = state.clone(deep=True)
            current_node = new_state.get_open_node()
            current_node.data["plan"] = parsed_plan.__dict__
            first_step = parsed_plan.steps[0]
            next_step_input = self.build_next_input(original_question=state.example.question,
                                                    new_goal=first_step)
            new_state.add_next_step(next_step_input=next_step_input,
                                    next_step_input_for_display=extract_task(next_step_input),
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
            if get_task_success_from_state(new_state, last_child) and \
                    current_node.data["plan"]["logic"] == "OR":
                # task succeeded with OR condition
                current_node.close(last_child.output)
                return [new_state]
            elif get_task_success_from_state(new_state, last_child) or \
                    current_node.data["plan"]["logic"] == "OR":
                # task succeeded with AND condition or failed with OR condition
                steps = current_node.data["plan"]["steps"]
                if len(steps) == len(children):
                    # All steps processed
                    current_node.close(last_child.output)
                    return [new_state]
                else:
                    # create a node for the next step in the plan
                    next_step = steps[len(children)]
                    last_outputs = [child.output for child in children]
                    next_step_input = self.build_next_input(
                        original_question=state.example.question,
                        new_goal=next_step,
                        last_outputs=last_outputs)
                    new_state.add_next_step(next_step_input=next_step_input,
                                            next_step_input_for_display=extract_task(
                                                next_step_input),
                                            next_step_model=self.next_model,
                                            current_step_node=current_node)
                    return [new_state]
            else:
                # task failed with AND condition
                set_observation(current_node, "Task failed!")
                current_node.close(last_child.output)
                return [new_state]
        else:
            return super().__call__(state)