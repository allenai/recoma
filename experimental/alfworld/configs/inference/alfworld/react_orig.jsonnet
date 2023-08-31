local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "alf_init": {
            "type": "alf_loader",
            "host": "localhost",
            "port": 5001,
            "path": "play",
            "next_model": "alf_react"
        },
        "alf_react": {
            "type": "alf_react",
            "react_model": "react_act",
            "action_model": "alf_obs",
            "eoq_string": "[EOQ]",
            "max_steps": 100
        },
        "react_act": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/alfworld/react_orig_heat_examine.txt",
            "generator_params": generator_params,
        },
        "alf_obs": {
            "type": "alf_action",
            "host": "localhost",
            "port": 5001,
            "path": "play"
        },
    },
    "search": {
        "type": "best_first",
        "max_search_iters": 200,
        "start_model": "alf_init",
        "answerer": {
            "type": "alf_reward"
        }
    },
    "reader": {
      "type": "alf"
    }
}

