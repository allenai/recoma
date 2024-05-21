import logging
from typing import Any

from jinja2 import Template

from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import LMGenerator, GenerationOutputs
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


@BaseModel.register("prompted_lm")
class PromptedLMModel(BaseModel):
    """
    Simplest form of a Prompted LM Model. Prompt is read from the prompt_file in the constructor.
    LMGenerator is constructed using the generator_params dictionary. When called, the prompt is
    grounded using question, input_str, and paras from the current open node. Prompt is assumed to
    be a Jinja template. The LMGenerator is then used to generate the output text and set as the
    output field for the current node and closed.
    """

    def __init__(self, prompt_file: str, generator_params, **kwargs):
        super().__init__(**kwargs)
        if prompt_file:
            with open(prompt_file, "r") as input_fp:
                self.prompt = "".join(input_fp.readlines())
        else:
            self.prompt = ""
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
        template_params = {
            "input_str": input_str
        }
        for field in state.example.fields():
            template_params[field] = state.example.get_field(field)
        return template_params

    def generate_output(self, state) -> GenerationOutputs:
        """
        Generate the output string using this prompted LM by first building the LM input prompt and
        calling the generator to produce the output
        :return: generator outputs
        """
        open_node = state.get_open_node()
        if open_node is None:
            raise ValueError("Model called without any open node!!")
        lm_input = self.build_lm_input(self.prompt, open_node.input_str, state)
        output = self.generator.generate(lm_input, state)
        logger.debug("Input: ..." + lm_input[-200:])
        logger.debug("Output: " + output.outputs[0])
        open_node.add_input_output_prompt(lm_input, output)
        return output
