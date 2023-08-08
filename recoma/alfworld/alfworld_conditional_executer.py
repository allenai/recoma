import json
import logging

from recoma.alfworld.alf_utils import set_observation, get_task_success_from_state, extract_task
from recoma.models.api_models import ClientAPIModel
from recoma.models.base_models import BaseModel

logger = logging.getLogger(__name__)


@BaseModel.register("alf_conditional_exec")
class AlfWorldConditionalExecuter(BaseModel):

    def __init__(self, executer_model: str, planner_model: str, alf_client_model: dict, **kwargs):
        super().__init__(**kwargs)
        self.executer_model = executer_model
        self.planner_model = planner_model
        self.alf_client_model = ClientAPIModel(**alf_client_model)

    def save_alf_state(self):
        output = self.alf_client_model.get_request_output(input_params={
            "action": "#SAVE",
            "output_only": "true"
        })
        output_json = json.loads(output)
        logger.debug(output_json["obs"])
        return output_json["info"]

    def load_alf_state(self, save_id):
        output = self.alf_client_model.get_request_output(input_params={
            "action": "#LOAD {}".format(save_id),
            "output_only": "true"
        })
        output_json = json.loads(output)
        logger.debug(output_json["obs"])
        return output_json["info"]

    def __call__(self, state):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        children_nodes = new_state.get_children(current_node)
        if len(children_nodes) == 0:
            # try model not attempted
            save_id = self.save_alf_state()
            current_node.data["save_id"] = save_id
            new_state.add_next_step(next_step_input=current_node.input_str,
                                    next_step_input_for_display=extract_task(
                                        current_node.input_str),
                                    next_step_model=self.executer_model,
                                    current_step_node=current_node)
            return [new_state]
        elif len(children_nodes) == 1:
            # only try model attempted, see if it failed
            executor_node = children_nodes[0]
            if get_task_success_from_state(new_state, executor_node):
                # success! no need to try except model
                _ = input("Task succeeded!")
                current_node.close(executor_node.output)
                return [new_state]
            else:
                _ = input("Task failed!")
                # failure! need to try except model
                # first load from checkpoint
                save_id = current_node.data["save_id"]
                self.load_alf_state(save_id)
                new_state.add_next_step(next_step_input=current_node.input_str,
                                        next_step_input_for_display=extract_task(
                                            current_node.input_str),
                                        next_step_model=self.planner_model,
                                        current_step_node=current_node)
                return [new_state]
        elif len(children_nodes) == 2:
            # except model attempted, check if it succeeded
            planner_node = new_state.get_node(children_nodes[1])
            if get_task_success_from_state(new_state, planner_node):
                current_node.close(planner_node.output)
                return [new_state]
            else:
                set_observation(current_node, "Task failed!")
                current_node.close(planner_node.output)
                return [new_state]
        else:
            raise ValueError("Unexpected number of nodes in try_except model: {}".format(
                len(children_nodes)))
