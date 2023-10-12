local generator_params = import "default_gpt_davinci003.libsonnet";
{
    "models": {
        "webshop_init": {
            "type": "webshop_loader",
            "host": "aristo-cirrascale-13.reviz.ai2.in",
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
            "type": "root"
        }
    },
    "reader": {
      "type": "webshop"
    }
}

