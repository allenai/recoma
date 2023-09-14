import logging
import re

from recoma.models.core.base_model import BaseModel

logger = logging.getLogger(__name__)


@BaseModel.register("react_controller")
class ReactController(BaseModel):
    (THOUGHT, ACTION, OBSERVATION, NUM_STEPS) = list(range(4))

    def __init__(self, react_model, action_model,
                 action_prefix="Action:", thought_prefix="Thought:",
                 obs_prefix="Observation:", eoq_re="Finish\\[(.*)\\]", max_steps=50, **kwargs):
        super().__init__(**kwargs)
        self.action_prefix = action_prefix
        self.thought_prefix = thought_prefix
        self.obs_prefix = obs_prefix
        self.eoq_re = eoq_re
        self.react_model = react_model
        self.action_model = action_model
        self.max_steps = max_steps

    def next_step(self, curr_step):
        return (curr_step + 1) % self.NUM_STEPS

    def get_step_prefix(self, step):
        if step == self.THOUGHT:
            return self.thought_prefix
        elif step == self.ACTION:
            return self.action_prefix
        elif step == self.OBSERVATION:
            return self.obs_prefix
        else:
            raise ValueError("Invalid step: {}".format(step))

    def __call__(self, state):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        if current_node is None:
            raise ValueError("Model called without any open node!!")
        children = new_state.children(current_node.identifier)

        # Start with thought
        if children is None or len(children) == 0:
            start_step = self.THOUGHT
            # first step use the question as input string
            input_str = current_node.input_str
            next_input_str = input_str + "\n" + self.get_step_prefix(start_step)
            new_state.add_next_step(next_step_input=next_input_str,
                                    next_step_model=self.react_model,
                                    current_step_node=current_node,
                                    next_step_input_for_display=self.get_step_prefix(start_step),
                                    metadata={"react": {"step": start_step}})
            return [new_state]
        else:
            last_child = children[-1]
            last_step = last_child.data["react"]["step"]
            # If the previous step was a thought step
            if last_step == self.THOUGHT:
                # If the task is complete OR max_steps hit, return the answer
                last_thought = last_child.output
                re_match = re.match(self.eoq_re, last_thought)
                if re_match:
                    answer = re_match.group(1)
                    current_node.close(output=answer)
                elif len(children) >= self.max_steps:
                    # Hit max limit!
                    answer = ""
                    current_node.close(output=answer)
                else:
                    # Otherwise, add an open node for action generation
                    next_input_str = last_child.input_str + " " + last_child.output + \
                                     "\n" + self.get_step_prefix(self.ACTION)
                    new_state.add_next_step(next_step_input=next_input_str,
                                            next_step_model=self.react_model,
                                            next_step_input_for_display=self.get_step_prefix(
                                                self.ACTION),
                                            current_step_node=current_node,
                                            metadata={"react": {"step": self.ACTION}})
            # If the previous step was an action step
            elif last_step == self.ACTION:
                last_action = last_child.output
                # Add an open node to generate observation using the action_model
                new_state.add_next_step(next_step_input=last_action,
                                        next_step_model=self.action_model,
                                        next_step_input_for_display=self.get_step_prefix(
                                            self.OBSERVATION),
                                        metadata={"react": {"step": self.OBSERVATION}},
                                        current_step_node=current_node)

            elif last_step == self.OBSERVATION:
                next_step = self.THOUGHT
                prev_action_node = children[-2]
                # Need to first collect the "Action: <output>" string from the prev_action_node
                next_input_str = prev_action_node.input_str + " " + prev_action_node.output + \
                                 "\n" + self.get_step_prefix(self.OBSERVATION) + " " + \
                                 last_child.output + "\n" + self.get_step_prefix(next_step)
                new_state.add_next_step(next_step_input=next_input_str,
                                        next_step_model=self.react_model,
                                        next_step_input_for_display=self.get_step_prefix(next_step),
                                        metadata={"react": {"step": next_step}},
                                        current_step_node=current_node)
            else:
                raise ValueError("Unknown last_step: " + last_step)
            return [new_state]