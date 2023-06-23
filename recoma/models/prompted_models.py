from typing import Any

from jinja2 import Template

from recoma.models.base_models import BaseModel, PromptedModel
from recoma.models.generator import LMGenerator, GenerationOutputs
from recoma.search.state import SearchState, SearchNode


@BaseModel.register("prompted_lm")
class PromptedLMModel(PromptedModel):

    def __init__(self, generator_params, **kwargs):
        super().__init__(**kwargs)
        self.generator = LMGenerator.from_dict(generator_params)

    def build_lm_input(self, prompt: str, input_str: str, state: SearchState) -> str:
        template = Template(prompt)
        template_params = self.populate_template_dictionary(input_str, state)
        return template.render(template_params)

    def populate_template_dictionary(self, input_str: str, state: SearchState) -> dict[str, Any]:
        return {
            "input_str": input_str,
            "paras": state.example.paras,
            "question": state.example.question
        }

    def generate_output(self, state) -> GenerationOutputs:
        open_node = state.get_open_node()
        lm_input = self.build_lm_input(self.prompt, open_node.input_str, state)
        output = self.generator.generate(lm_input)
        open_node.add_input_output_prompt(lm_input, output)
        return output


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
            open_node = new_state.get_open_node()
            if generation_outputs.scores:
                new_state.update_score(generation_outputs.scores[idx])
            if output_str == self.eoq_string:
                answer = state.children(open_node.identifier)[-1].output
                open_node.close(output=answer)
            else:
                var_assignments = self.build_var_assignments(state=new_state, open_node=open_node)
                # print(var_assignments)
                new_state_input_str = self.update_question_with_vars(output_str, var_assignments)
                # print(new_state_input_str, output_str)
                new_state.add_node(node=SearchNode(input_str=new_state_input_str,
                                                   target_model=self.next_model,
                                                   metadata={}),
                                   parent=open_node)
            new_states.append(new_state)

        return new_states
