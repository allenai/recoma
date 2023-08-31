local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "drop_react": {
            "type": "react_controller",
            "react_model": "react_lm",
            "action_model": "qa"
        },
        "react_lm": {
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
        "qa": {
            "type": "router"
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "drop_react",
        "answerer": {
            "type": "root"
        }
    },
    "reader": {
      "type": "drop"
    }
}

