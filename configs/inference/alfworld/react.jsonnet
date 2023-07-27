local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "alf_init": {
            "type": "alf_loader",
            "host": "localhost",
            "port": 5001,
            "path": "play",
            "next_model": "react_control"
        },
        "react_control": {
            "type": "react_controller",
            "react_model": "react",
            "action_model": "alfapi"
        },
        "react": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/alfworld/react.txt",
            "generator_params": generator_params,
        },
        "alfapi": {
            "type": "alf_action",
            "host": "localhost",
            "port": 5001,
            "path": "play"
        },
    },
    "search": {
        "type": "best_first",
        "start_model": "alf_init",
        "answerer": {
            "type": "root"
        }
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

