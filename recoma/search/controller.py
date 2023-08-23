import logging
from typing import Dict

from recoma.models.core.base_model import BaseModel
from recoma.search.state import SearchState

logger = logging.getLogger(__name__)


class Controller:
    def __init__(self, model_list: Dict[str, BaseModel]):
        self.model_list = model_list

    def execute(self, current_state: SearchState):
        open_node = current_state.get_open_node()
        if open_node is not None:
            target_model = open_node.target_model()
            if target_model not in self.model_list:
                logger.error("Can not handle next state: " + str(target_model))
                return []
            try:
                output_states = self.model_list[target_model](current_state)
                return output_states
            except RecursionError:
                return []
        else:
            raise ValueError("No open nodes in current state:" + str(current_state))
