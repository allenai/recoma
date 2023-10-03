import re

from recoma.models.core.base_model import BaseModel
from recoma.search.state import SearchState


@BaseModel.register("l2m_control")
class LeastToMostController(BaseModel):

    def __init__(self, l2m_decomp_model: str, l2m_qa_model: str,
                 step_regex="To answer the question \"(.*)\", we need to know: (.*)",
                 ques_regex="\"(.*?)\"(?:,|\\.|$)",
                 **kwargs):
        super().__init__(**kwargs)
        self.step_regex = re.compile(step_regex)
        self.ques_regex = ques_regex
        self.l2m_decomp_model = l2m_decomp_model
        self.l2m_qa_model = l2m_qa_model

    def parse_decomposition(self, gen_output):
        re_match = self.step_regex.match(gen_output)
        if re_match:
            final_q = re_match.group(1)
            decomposition = re_match.group(2)
            questions = re.findall(self.ques_regex, decomposition)
            if len(questions) == 0:
                raise ValueError("Cannot find questions in the line: {}!".format(gen_output))
            # Need to add the original question back in here as the final question.
            return questions + [final_q]
        else:
            raise ValueError("Cannot parse line:{} in the generated plan!".format(gen_output))
        return []

    def __call__(self, state: SearchState):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        if current_node is None:
            raise ValueError("Model called without any open node!!")
        children = new_state.get_children(current_node)
        if len(children) == 0:
            # Decompose
            new_state.add_next_step(next_step_input=current_node.input_str,
                                    next_step_model=self.l2m_decomp_model,
                                    current_step_node=current_node)
        else:
            # QA
            # Parse the questions from the generated decomposition and cache in node
            if "questions" not in current_node.data:
                questions = self.parse_decomposition(children[0].output)
                current_node.data["questions"] = questions
            else:
                questions = current_node.data["questions"]
            # all questions processed?
            if len(questions) + 1 == len(children):
                answer = children[-1].output
                current_node.close(answer)
                if self.next_model:
                    new_state.add_next_step(next_step_input=answer,
                                            next_step_model=self.next_model,
                                            current_step_node=current_node)
            else:
                curr_question = questions[len(children) - 1]
                if len(children) > 1:
                    new_input = children[-1].input_str + " " + children[-1].output + "\n\n"
                else:
                    # Adding paras or question should be part of the prompt
                    new_input = ""
                new_state_input_str = new_input + "Q: " + curr_question + "\n" + \
                                      "A:"
                new_state_input_str_for_display = "..." + \
                                                  "Q: " + curr_question + "\n" + "A:"
                new_state.add_next_step(next_step_input=new_state_input_str,
                                        next_step_input_for_display=new_state_input_str_for_display,
                                        next_step_model=self.l2m_qa_model,
                                        current_step_node=current_node)

        return [new_state]