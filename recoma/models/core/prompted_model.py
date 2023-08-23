import logging
from typing import Any

from jinja2 import Template
from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import LMGenerator, GenerationOutputs

from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


# No need to register this class as it should only be used as a superclass for other models
class PromptedModel(BaseModel):
    def __init__(self, prompt_file: str, **kwargs):
        super().__init__(**kwargs)
        if prompt_file:
            with open(prompt_file, "r") as input_fp:
                self.prompt = "".join(input_fp.readlines())
        else:
            self.prompt = ""


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
        logger.debug("Input: ..." + lm_input[-200:])
        logger.debug("Output: " + output.outputs[0])
        open_node.add_input_output_prompt(lm_input, output)
        return output
