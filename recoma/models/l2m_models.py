import re
from typing import List

from recoma.models.base_models import BaseModel
from recoma.models.generator import GenerationOutputs
from recoma.models.prompted_model import PromptedLMModel
from recoma.search.state import SearchState


@BaseModel.register("l2m_control")
class LeastToMostController(BaseModel):

    def __init__(self, l2m_decomp_model: str, l2m_qa_model: str, **kwargs):
        super().__init__(**kwargs)
        self.l2m_decomp_model = l2m_decomp_model
        self.l2m_qa_model = l2m_qa_model

    def __call__(self, state: SearchState):
        new_state = state.clone(deep=True)
        current_node = new_state.get_open_node()
        children = new_state.get_children(current_node)
        if len(children) == 0:
            # Decompose
            new_state.add_next_step(next_step_input=current_node.input_str,
                                    next_step_model=self.l2m_decomp_model,
                                    current_step_node=current_node)
        else:
            # QA
            questions = children[0].data["questions"]
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
                    new_input = children[-1].input_str + " " + children[-1].output
                else:
                    new_input = current_node.input_str
                new_state_input_str = new_input + "\n" + "Q: " + curr_question + "\n" + \
                                      "A:"
                new_state_input_str_for_display = "..." + \
                                                  "Q: " + curr_question + "\n" + "A:"
                new_state.add_next_step(next_step_input=new_state_input_str,
                                        next_step_input_for_display=new_state_input_str_for_display,
                                        next_step_model=self.l2m_qa_model,
                                        current_step_node=current_node)

        return [new_state]


@BaseModel.register("l2m_decomp")
class LeastToMostDecomposer(PromptedLMModel):

    def __init__(self,
                 step_regex="To answer the question \"(.*)\", we need to know: (.*)",
                 ques_regex="\"(.*?)\"[,.]",
                 **kwargs):
        super().__init__(**kwargs)
        self.step_regex = re.compile(step_regex)
        self.ques_regex = ques_regex

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

    def build_new_states(self, state: SearchState,
                         generation_outputs: GenerationOutputs) -> List[SearchState]:
        new_states = []
        for gen_idx, gen_output in enumerate(generation_outputs.outputs):
            questions = self.parse_decomposition(gen_output)
            new_state = state.clone(deep=True)
            current_node = new_state.get_open_node()
            current_node.data["questions"] = questions
            current_node.close(gen_output)
            new_states.append(new_state)
        return new_states

# @BaseModel.register("l2m_qa")
# class LeastToMostQAModel(PromptedLMModel):
#
#     def __init__(self, **kwargs):
#         super().__init__(**kwargs)
#
#     def build_new_states(self, state: SearchState, generation_outputs: GenerationOutputs):
#         new_states = []
#         for idx, output_str in enumerate(generation_outputs.outputs):
#             new_state = state.clone(deep=True)
#             current_node = new_state.get_open_node()
#             steps = current_node.data["questions"]
#             if generation_outputs.scores:
#                 new_state.update_score(generation_outputs.scores[idx])
#             current_node.close(output=output_str)
#             # more questions to answer
#             if len(steps) > 1:
#                 new_steps = steps[1:]
#                 new_state_input_str = current_node.input_str + " " + output_str + "\n" + \
#                                       "Q: " + steps[0] + "\n" + \
#                                       "A:"
#                 new_state.add_next_step(next_step_input=new_state_input_str,
#                                         next_step_model=self.next_model,
#                                         current_step_node=current_node,
#                                         metadata={"questions": new_steps})
#             new_states.append(new_state)
#
#         return new_states
