import logging
from typing import Any

from jinja2 import Template

from recoma.models.base_models import BaseModel, PromptedModel
from recoma.models.generator import LMGenerator, GenerationOutputs
from recoma.search.state import SearchState, SearchNode

logger = logging.getLogger(__name__)


@BaseModel.register("prompted_lm")
class PromptedLMModel(PromptedModel):

    def __init__(self, generator_params, **kwargs):
        super().__init__(**kwargs)
        self.generator = LMGenerator.from_dict(generator_params)

    def build_lm_input(self, prompt: str, input_str: str, state: SearchState) -> str:
        """
        Generate the language model input given the prompt, input string and search state.
        :return: language model input string
        """
        template = Template(prompt)
        template_params = self.populate_template_dictionary(input_str, state)
        return template.render(template_params)

    def populate_template_dictionary(self, input_str: str, state: SearchState) -> dict[str, Any]:
        """
        Generate a dictionary from var names to objects that will be used to populate the Jinja2
        template prompt
        :param input_str: input string to the model
        :param state: current search state
        :return: var to object mapping for prompt template
        """
        return {
            "input_str": input_str,
            "paras": state.example.paras,
            "question": state.example.question
        }

    def generate_output(self, state) -> GenerationOutputs:
        """
        Generate the output string using this prompted LM by first building the LM input prompt and
        calling the generator to produce the output
        :return: generator outputs
        """
        open_node = state.get_open_node()
        lm_input = self.build_lm_input(self.prompt, open_node.input_str, state)
        output = self.generator.generate(lm_input)
        logger.debug("Input: ..." + lm_input[-100:])
        logger.debug("Output: " + output.outputs[0])
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
