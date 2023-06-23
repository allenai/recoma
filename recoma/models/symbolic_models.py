import logging
import re

from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.search.state import SearchNode

logger = logging.getLogger(__name__)


@BaseModel.register("regex_ext")
class RegexExtractor(BaseModel):

    def __init__(self, regex, **kwargs):
        super().__init__(**kwargs)
        self.regex = re.compile(regex)

    def generate_output(self, state):
        open_node = state.get_open_node()
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

    def __init__(self, regex="\[([^\]]+)\] (.*)", **kwargs):
        super().__init__(**kwargs)
        self.regex = re.compile(regex)

    def __call__(self, state):
        open_node = state.get_open_node()
        children = state.children(open_node.identifier)
        # print(children)
        # Route question to appropriate model
        if children is None or len(children) == 0:
            input_str = open_node.input_str
            m = self.regex.match(input_str)
            if not m:
                logger.error("RouterModel did not find a match for input regex in {}".format(
                    input_str))
                return []
            next_model = m.group(1)
            subq = m.group(2)
            new_state = state.clone(deep=True)
            # create new open open node since new state has been created
            open_node = new_state.get_open_node()
            open_node._tag = "*[" + open_node.target + "] " + input_str
            new_state.add_node(node=SearchNode(input_str=subq,
                                               target_model=next_model,
                                               metadata={}),
                               parent=open_node)
            return [new_state]
        else:
            # Question routed, recover answer
            assert len(children) == 1, "More than 1 child for router model. Tree:\n" + \
                                       state.to_str_tree()
            answer_from_child = children[0].output
            new_state = state.clone(deep=True)
            # create new open node since new state has been created
            open_node = new_state.get_open_node()
            open_node._tag = "[" + open_node.target + "] " + open_node.input_str
            open_node.close(output=answer_from_child)
            return [new_state]
