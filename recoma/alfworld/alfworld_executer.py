import logging

from recoma.models.base_models import BaseModel

logger = logging.getLogger(__name__)


@BaseModel.register("alf_executer")
class AlfWorldExecuter(BaseModel):
    (THOUGHT, ACTION, OBSERVATION, NUM_STEPS) = list(range(4))

    def __init__(self, react_model, action_model,
                 action_prefix=">", thought_prefix="think:",
                 obs_prefix="", eoq_string="!",
                 obs_str_for_think="OK.", max_steps=50, **kwargs):
        super().__init__(**kwargs)
        self.action_prefix = action_prefix
        self.thought_prefix = thought_prefix
        self.obs_prefix = obs_prefix
        self.eoq_string = eoq_string
        self.react_model = react_model
        self.action_model = action_model
        self.obs_str_for_think = obs_str_for_think
        self.max_steps = max_steps

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
        children = new_state.get_children(current_node)

        # Start with action
        if children is None or len(children) == 0:
            start_step = self.ACTION
            # first step use the question as input string
            input_str = current_node.input_str
            next_input_str = input_str + "\n" + self.get_step_prefix(start_step)
            # use react model to generate the action
            new_state.add_next_step(next_step_input=next_input_str,
                                    next_step_model=self.react_model,
                                    current_step_node=current_node,
                                    next_step_input_for_display=self.get_step_prefix(start_step),
                                    metadata={"react": {"step": start_step}})
            return [new_state]
        else:
            last_child = children[-1]
            last_step = last_child.data["react"]["step"]
            # If the previous step was an action step
            if last_step == self.ACTION:
                generated_action = last_child.output
                # if action starts with think:, handle it like a think step.
                if generated_action.startswith(self.thought_prefix):
                    if generated_action.endswith(self.eoq_string) or \
                            len(children) >= self.max_steps:
                        answer = last_child.output
                        current_node.close(output=answer)
                    else:
                        # Thought step generated; add OK. as observation
                        obs_node = new_state.add_next_step(next_step_input=generated_action,
                                                           next_step_model="def",
                                                           next_step_input_for_display=
                                                           self.get_step_prefix(self.OBSERVATION),
                                                           metadata=
                                                           {"react": {"step": self.OBSERVATION}},
                                                           current_step_node=current_node
                                                           )
                        obs_node.close(self.obs_str_for_think)

                        # Now create an open node for the next action step
                        next_step = self.ACTION
                        next_input_str = last_child.input_str + " " + generated_action + \
                                         "\n" + self.get_step_prefix(self.OBSERVATION) + " " + \
                                         self.obs_str_for_think + "\n" + \
                                         self.get_step_prefix(next_step)
                        new_state.add_next_step(next_step_input=next_input_str,
                                                next_step_model=self.react_model,
                                                next_step_input_for_display=self.get_step_prefix(
                                                    next_step),
                                                metadata={"react": {"step": next_step}},
                                                current_step_node=current_node)
                else:
                    # Add an open node to generate observation using the action_model
                    new_state.add_next_step(next_step_input=generated_action,
                                            next_step_model=self.action_model,
                                            next_step_input_for_display=self.get_step_prefix(
                                                self.OBSERVATION),
                                            metadata={"react": {"step": self.OBSERVATION}},
                                            current_step_node=current_node)

            elif last_step == self.OBSERVATION:
                if len(children) >= self.max_steps:
                    answer = "Task Failed!"
                    current_node.close(output=answer)
                    return [new_state]
                next_step = self.ACTION
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
