import json
from experiments.webshop.webshop_utils import set_webshop_url, env

from recoma.models.core.base_model import BaseModel
from recoma.models.core.generator import GenerationOutputs
from recoma.search.answerfromstate import AnswerFromState
from recoma.search.state import SearchState


@BaseModel.register("webshop_loader")
class WebShopGameLoaderModel(BaseModel):


    def __init__(self, host: str, port: int, path: str = "", **kwargs):
        super().__init__(**kwargs)
        url = "http://{}:{}".format(host, port)
        if path:
            url += "/{}".format(path)
        set_webshop_url(url)

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        obs, reward, done = env.step(state.example.qid, "reset")
        print(obs, reward, done)
        # json_data = json.loads(obs)
        # question = json_data["obs"]
        state.example.question = obs
        return GenerationOutputs(outputs=[obs])


@BaseModel.register("webshop_action")
class WebShopActionModel(BaseModel):

    def generate_output(self, state: SearchState) -> GenerationOutputs:
        current_node = state.get_open_node()
        if current_node is None:
            raise ValueError("WebShopActionModel called without any open node!!")
        obs, reward, done = env.step(state.example.qid, current_node.input_str.strip())
        #json_data = json.loads(obs)
        output_observation = obs
        return GenerationOutputs(outputs=[output_observation], metadata=[{"reward": reward}])


# @AnswerFromState.register("webshop_answerer")
# class WebShopAnswerer(AnswerFromState):

#     def __init__(self, n_tail: int = -1):
#         super().__init__()
#         self.n_tail = n_tail

#     def generate_answer(self, state: SearchState):
#         return state.get_depth_nth_node(self.n_tail).output