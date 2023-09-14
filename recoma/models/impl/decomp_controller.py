from recoma.models.core.base_model import BaseModel
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
        if current_node is None:
            raise ValueError("Model called without any open node!!")
        children = new_state.get_children(current_node)
        if len(children) % 2 == 0:
            # decompose
            input_str = current_node.input_str + "\n"
            for child_idx in range(int(len(children) / 2)):
                decomp_node = children[child_idx * 2]
                qa_node = children[child_idx * 2 + 1]
                subqf = "Q{}".format(child_idx + 1) if self.use_number_format else "QS"
                subaf = "#{}".format(child_idx + 1) if self.use_number_format else "A"
                # question
                input_str += subqf + ": " + decomp_node.output + "\n"
                # answer
                input_str += subaf + ": " + qa_node.output + "\n"
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
                # QA starts from the 2nd node and alternated between decomp and QA
                var_assignments = self.build_var_assignments(children[1::2])
                new_question = self.update_question_with_vars(last_question, var_assignments)
                new_state.add_next_step(next_step_input=new_question,
                                        next_step_model=self.qa_model,
                                        current_step_node=current_node)
        return [new_state]

    @staticmethod
    def build_var_assignments(qa_children):
        var_assignments = {}
        for idx, child in enumerate(qa_children):
            suba = child.output
            var_assignments["#" + str(idx + 1)] = suba
        return var_assignments

    @staticmethod
    def update_question_with_vars(input_str: str, var_assignments: dict[str, str]):
        for var_id, var_val in var_assignments.items():
            input_str = input_str.replace(var_id, var_val)
        return input_str
