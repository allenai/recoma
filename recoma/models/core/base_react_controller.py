from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from recoma.models.core.base_model import BaseModel
from recoma.search.state import SearchNode, SearchState


class BaseReactController(ABC, BaseModel):
    """
    React Controller that stores the entire conversation in a structured format
    """
    (THOUGHT, ACTION, OBSERVATION, STEP_TYPES) = list(range(4))

    def __init__(self, action_model, observation_model,
                 max_steps=100, add_roles=False, max_output_length=100000, **kwargs):
        super().__init__(**kwargs)
        self.action_model = action_model
        self.observation_model = observation_model
        self.max_steps = max_steps
        self.add_roles = add_roles
        self.max_output_length = max_output_length

    @abstractmethod
    def summarize_history(self, history: List[Any]) -> str:
        """Summarize the history of the conversation"""
        pass

    @abstractmethod
    def next_step_and_observation_input(self, state: SearchState,
                                        last_child: SearchNode) -> Tuple[int, str]:
        """
        This method returns the next step and observation input for the controller.
        """
        pass

    @abstractmethod
    def next_step_and_action_input(self, state: SearchState,
                                   last_child: SearchNode) -> Tuple[int, str]:
        """
        This function determines the next step and action input based on the current state and the
        last child node.
        """
        pass

    @abstractmethod
    def terminate_with_output(self, state: SearchState, last_child: SearchNode) -> Optional[str]:
        """
        This function determines if the controller should terminate with output. Set to None
        if the controller should not terminate.
        """
        pass

    @abstractmethod
    def append_message_to_history(self, current_history: List[Any], last_child: SearchNode) -> None:
        """
        Append the message from the last child to the current history
        """
        pass

    def get_children(self, state: SearchState):
        """
        Utility function to get the children of the current node
        """
        current_node = state.get_open_node()
        if current_node is None:
            raise ValueError("Model called without any open node!!")

        children = state.children(current_node.identifier)
        return children

    def get_react_node(self, state: SearchState) -> SearchNode:
        """
        Utility function to get the top-level react node
        """
        current_node = state.get_open_node()
        if current_node is None:
            raise ValueError("Model called without any open node!!")
        return current_node

    def get_history(self, current_node: SearchNode) -> List[Any]:
        """
        Utility function to get the history of the conversation
        """
        if "history" not in current_node.data:
            current_node.data["history"] = []
        return current_node.data["history"]

    def get_step(self, last_step: SearchNode) -> int:
        """
        Utility function to get the step type of the last child node
        """
        return last_step.data["react.step"] if last_step is not None else None

    def set_step(self, last_step: SearchNode, step: int) -> None:
        """
        Utility function to set the step type of the last child node
        """
        last_step.data["react.step"] = step

    def next_step_and_input(self, state: SearchState, last_child: SearchNode) -> Tuple[int, str]:
        """
        This function determines the next step type and input based on the current state and the
        last child node.
        """
        # Observation always follows an action step only
        if last_child is not None and self.get_step(last_child) == self.ACTION:
            return self.next_step_and_observation_input(state, last_child)
        else:
            return self.next_step_and_action_input(state, last_child)

    def __call__(self, state: SearchState) -> List[SearchState]:
        new_state = state.clone(deep=True)
        current_node = self.get_react_node(new_state)
        children = self.get_children(new_state)
        last_child = children[-1] if children else None

        if last_child is not None:
            self.append_message_to_history(
                self.get_history(current_node), last_child)
        output_str = self.terminate_with_output(new_state, last_child)
        if output_str is not None:
            current_node.close(output_str)
            current_node.data["summary"] = self.summarize_history(
                self.get_history(current_node))
            return [new_state]

        (next_step, next_input_str) = self.next_step_and_input(new_state, last_child)
        next_model = self.observation_model if next_step == self.OBSERVATION else self.action_model
        new_node = new_state.add_next_step(next_step_input=next_input_str,
                                           next_step_model=next_model,
                                           current_step_node=current_node,
                                           metadata={})

        self.set_step(new_node, next_step)
        return [new_state]
