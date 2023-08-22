from recoma.models.base_model import BaseModel

from recoma.search.state import SearchState


@BaseModel.register("decomp_control")
class DecompController(BaseModel):

    def __init__(self, decomp_model: str, qa_model: str,
                 use_number_format=False, eoq_string="[EOQ]", **kwargs):
        super().__init__(**kwargs)
        self.use_number_format = use_number_format
        self.eoq_string = eoq_string
        self.decomp_model = decomp_model
        self.qa_model = qa_model

    def __call__(self, state: SearchState):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        children = new_state.get_children(current_node)
        if len(children) % 2 == 0:
            # decompose
            input_str = current_node.input_str + "\n"
            for child_idx in range(int(len(children) / 2)):
                answer_node = children[child_idx * 2 + 1]
                subqf = "Q{}".format(child_idx + 1) if self.use_number_format else "QS"
                subaf = "#{}".format(child_idx + 1) if self.use_number_format else "A"
                input_str += subqf + ": " + answer_node.input_str + "\n"
                input_str += subaf + ": " + answer_node.output + "\n"
            input_str += "Q{}: ".format(int(len(children) / 2) + 1) if self.use_number_format \
                else "QS: "
            new_state.add_next_step(next_step_input=input_str,
                                    next_step_model=self.decomp_model,
                                    current_step_node=current_node)
        else:
            # qa
            last_question = children[-1].output
            if last_question == self.eoq_string:
                answer = children[-2].output
                current_node.close(output=answer)
                if self.next_model:
                    new_state.add_next_step(next_step_input=answer,
                                            next_step_model=self.next_model,
                                            current_step_node=current_node)
            else:
                new_state.add_next_step(next_step_input=last_question,
                                        next_step_model=self.qa_model,
                                        current_step_node=current_node)
        return [new_state]