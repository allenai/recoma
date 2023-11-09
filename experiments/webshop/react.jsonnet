local generator_params = import "default_gpt_davinci003.libsonnet";
{
    "models": {
        "webshop_init": {
            "type": "webshop_loader",
            "host": std.extVar("WEBSHOP_HOST"),
            "port": 3000,
            "next_model": "react_control"
        },
        "react_control": {
            "type": "webshop_react",
            "react_model": "react",
            "action_model": "api"
        },
        "react": {
            "type": "prompted_lm",
            "prompt_file": "experiments/webshop/react_prompt.txt",
            "generator_params": generator_params,
        },
        "api": {
            "type": "webshop_action"
        },
    },
    "search": {
        "type": "best_first",
        "start_model": "webshop_init",
        "answerer": {
            "type": "tail",
            "n_tail": -2
        }
    },
    "reader": {
      "type": "webshop",
      "start_num": 100, 
      "end_num": 110
    }
}

