import logging
import re
from typing import List

from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import GenerationOutputs
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


@BaseModel.register("regex_ext")
class RegexExtractor(BaseModel):
    """
    Regular Expression based model that extracts a sub-string from the input and passes it on as
    the output.
    """

    def __init__(self, regex, **kwargs):
        """
        :param regex: Regular expression that extracts the sub-string from the input (looks for
        a match for the first group in the regex)
        """
        super().__init__(**kwargs)
        self.regex = re.compile(regex)

    def generate_output(self, state):
        open_node = state.get_open_node()
        if open_node is None:
            raise ValueError("Model called without any open node!!")
        input_str = open_node.input_str
        m = self.regex.match(input_str)
        if m:
            return GenerationOutputs(outputs=[m.group(1)])
        else:
            logger.error("Answer Extractor did not find a match for input regex in {}".format(
                input_str))
            return GenerationOutputs(outputs=[""])


@BaseModel.register("router")
class RouterModel(BaseModel):
    """
    Model that routes the input string to the appropriate model by extracting the model name using
    the input regex. The first matching group is used to extract the model name and the second one
    is used to extract the input for the next model. The default regex follows the DecomP format:
      [model_name] input_question
    """

    def __init__(self, regex: str = "\[([^\]]+)\] (.*)", **kwargs):
        super().__init__(**kwargs)
        self.regex = re.compile(regex)

    def __call__(self, state: SearchState) -> List[SearchState]:
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        if current_node is None:
            raise ValueError("Model called without any open node!!")
        children = new_state.get_children(current_node)
        # Route question to appropriate model
        if len(children) == 0:
            input_str = current_node.input_str
            m = self.regex.match(input_str)
            if not m:
                logger.error("RouterModel did not find a match for input regex in {}".format(
                    input_str))
                return []
            next_model = m.group(1)
            subq = m.group(2)
            new_state.add_next_step(next_step_input=subq,
                                    next_step_model=next_model,
                                    current_step_node=current_node)
            return [new_state]
        else:
            # Question routed, recover answer
            assert len(children) == 1, "More than 1 child for router model. Tree:\n" + \
                                       state.to_str_tree()
            answer_from_child = children[0].output
            current_node.close(output=answer_from_child)
            return [new_state]
