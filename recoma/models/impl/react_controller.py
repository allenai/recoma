import copy
import logging
import re
from dataclasses import dataclass
from typing import List

from recoma.models.core.base_model import BaseModel
from recoma.models.core.base_react_controller import BaseReactController

logger = logging.getLogger(__name__)


@dataclass
class Message:
    message_type: int
    message_str: str


@BaseModel.register("simple_react")
class SimpleReactController(BaseReactController):
    """
    React Controller that stores the entire conversation in a structured format
    """

    def __init__(self, action_prefix="Action:", thought_prefix="Thought:",
                 obs_prefix="Observation:", eoq_re="Finish\\[(.*)\\]", **kwargs):
        super().__init__(**kwargs)
        self.action_prefix = action_prefix
        self.thought_prefix = thought_prefix
        self.obs_prefix = obs_prefix
        self.eoq_re = eoq_re

    def next_step_and_action_input(self, state, last_step):
        last_step_type = self.get_step(last_step)
        print(last_step_type)
        if last_step is None or last_step_type == self.OBSERVATION:
            suffix = "Thought:"
            next_step = self.THOUGHT
        elif last_step_type == self.THOUGHT:
            suffix = "Action:"
            next_step = self.ACTION
        else:
            raise ValueError(
                "Unknown last step for action input: {}".format(last_step_type))

        current_node = self.get_react_node(state)
        history = self.get_history(current_node)
        output_str = current_node.input_str + "\n" + \
            self.build_message_thread(history) + suffix

        # remove old messages to fit within max_output_length. Could be made more efficient
        new_history = copy.deepcopy(history)
        while len(output_str) > self.max_output_length:
            new_history = new_history[1:]
            output_str = current_node.input_str + "\n[NOT SHOWN FOR BREVITY]\n" + \
                self.build_message_thread(new_history) + suffix
        return next_step, output_str

    def summarize_history(self, history):
        return self.build_message_thread(history)

    def next_step_and_observation_input(self, state, last_step):
        return self.OBSERVATION, last_step.output

    def append_message_to_history(self, current_history, last_child):
        last_step = self.get_step(last_child)
        current_history.append(
            Message(message_type=last_step, message_str=last_child.output))

    def build_message_thread(self, history):
        output_str = ""
        for message in history:
            if message.message_type == self.THOUGHT:
                if self.add_roles:
                    output_str += "ASSISTANT:\n"
                output_str += self.thought_prefix + " " + message.message_str + "\n"
            elif message.message_type == self.ACTION:
                if self.add_roles:
                    output_str += "ASSISTANT:\n"
                output_str += self.action_prefix + " " + message.message_str + "\n"
            elif message.message_type == self.OBSERVATION:
                if self.add_roles:
                    output_str += "USER:\n"
                output_str += self.obs_prefix + " " + message.message_str + "\n"
            else:
                raise ValueError("Unknown message type: {}".format(message))
        return output_str

    def terminate_with_output(self, state, last_child):
        if last_child is None:
            return None
        last_thought = last_child.output
        children = self.get_children(state)
        re_match = re.match(self.eoq_re, last_thought)
        if re_match:
            answer = re_match.group(1)
            return answer
        elif len(children) >= self.max_steps:
            # Hit max limit!
            return "MAX STEPS REACHED!"
        return None
