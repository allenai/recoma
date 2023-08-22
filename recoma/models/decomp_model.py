from typing import Any

from recoma.models import PromptedLMModel
from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchState, SearchNode


@BaseModel.register("decomp_control")
class DecompController(BaseModel):

    def __init__(self, decomp_model: str, qa_model: str,
                 use_number_format=False, eoq_string="[EOQ]", **kwargs):
        super().__init__(**kwargs)
        self.use_number_format = use_number_format
        self.eoq_string = eoq_string
        self.decomp_model = decomp_model
        self.qa_model = qa_model

    def __call__(self, state: SearchState):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        children = new_state.get_children(current_node)
        if len(children) % 2 == 0:
            # decompose
            input_str = current_node.input_str + "\n"
            for child_idx in range(int(len(children) / 2)):
                answer_node = children[child_idx * 2 + 1]
                subqf = "Q{}".format(child_idx + 1) if self.use_number_format else "QS"
                subaf = "#{}".format(child_idx + 1) if self.use_number_format else "A"
                input_str += subqf + ": " + answer_node.input_str + "\n"
                input_str += subaf + ": " + answer_node.output + "\n"
            input_str += "Q{}: ".format(int(len(children) / 2) + 1) if self.use_number_format \
                else "QS: "
            new_state.add_next_step(next_step_input=input_str,
                                    next_step_model=self.decomp_model,
                                    current_step_node=current_node)
        else:
            # qa
            last_question = children[-1].output
            if last_question == self.eoq_string:
                answer = children[-2].output
                current_node.close(output=answer)
                if self.next_model:
                    new_state.add_next_step(next_step_input=answer,
                                            next_step_model=self.next_model,
                                            current_step_node=current_node)
            else:
                new_state.add_next_step(next_step_input=last_question,
                                        next_step_model=self.qa_model,
                                        current_step_node=current_node)
        return [new_state]


@BaseModel.register("decomp_lm")
class DecompLMModel(PromptedLMModel):

    def __init__(self, use_number_format=False, eoq_string="[EOQ]", **kwargs):
        super().__init__(**kwargs)
        assert self.next_model is not None, "DecompLMModel must have a next model specified!"
        self.use_number_format = use_number_format
        self.eoq_string = eoq_string

    def populate_template_dictionary(self, input_str: str, state: SearchState) -> dict[str, Any]:
        base_dictionary = super().populate_template_dictionary(input_str, state)
        open_node = state.get_open_node()
        children: list[SearchNode] = state.children(open_node.identifier)
        subqs = []
        for idx, child in enumerate(children):
            subq = child.input_str
            suba = child.output
            subqf = "Q{}".format(idx + 1) if self.use_number_format else "QS"
            subaf = "#{}".format(idx + 1) if self.use_number_format else "A"
            subqs.append({
                "subq": subq,
                "suba": suba,
                "subqf": subqf,
                "subaf": subaf
            })

        subqf_final = "Q{}".format(len(children) + 1) if self.use_number_format else "QS"
        base_dictionary["subqas"] = subqs
        base_dictionary["subqf_final"] = subqf_final
        return base_dictionary

    def build_var_assignments(self, state: SearchState, open_node: SearchNode):
        var_assignments = {}
        children: list[SearchNode] = state.children(open_node.identifier)
        for idx, child in enumerate(children):
            suba = child.output
            var_assignments["#" + str(idx + 1)] = suba
        return var_assignments

    def update_question_with_vars(self, input_str: str, var_assignments: dict[str, str]):
        for var_id, var_val in var_assignments.items():
            input_str = input_str.replace(var_id, var_val)
        return input_str

    def build_new_states(self, state: SearchState, generation_outputs: GenerationOutputs):
        new_states = []
        for idx, output_str in enumerate(generation_outputs.outputs):
            new_state = state.clone(deep=True)
            current_node = new_state.get_open_node()
            if generation_outputs.scores:
                new_state.update_score(generation_outputs.scores[idx])
            if output_str == self.eoq_string:
                answer = state.children(current_node.identifier)[-1].output
                current_node.close(output=answer)
            else:
                var_assignments = self.build_var_assignments(state=new_state,
                                                             open_node=current_node)
                new_state_input_str = self.update_question_with_vars(output_str, var_assignments)
                new_state.add_next_step(next_step_input=new_state_input_str,
                                        next_step_model=self.next_model,
                                        current_step_node=current_node)
            new_states.append(new_state)

        return new_states
