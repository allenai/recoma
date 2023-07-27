local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "react_control": {
            "type": "react_controller",
            "react_model": "react",
            "action_model": "router"
        },
        "react": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/react.txt",
            "generator_params": generator_params,
        },
        "textqa": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/textqa.txt",
            "generator_params": generator_params
        },
        "basic_math": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/drop/basic_math.txt",
            "generator_params": generator_params
        },
        "router": {
            "type": "router"
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "react_control",
        "answerer": {
            "type": "root"
        }
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

