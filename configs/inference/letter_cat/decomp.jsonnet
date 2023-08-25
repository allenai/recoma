local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "decomp_control": {
            "type": "decomp_control",
            "use_number_format": false,
            "decomp_model": "decomp",
            "qa_model": "router",
        },
        "decomp": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/decomp_noloop.txt",
            "generator_params": generator_params,
        },
        "split": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/task_primitives/split.txt",
            "generator_params": generator_params
        },
        "str_position": {
            "type": "decomp_control",
            "use_number_format": false,
            "decomp_model": "str_decomp",
            "qa_model": "router",
        },
        "str_decomp": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/task_primitives/str_position.txt",
            "generator_params": generator_params
        },
        "arr_position": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/task_primitives/arr_position.txt",
            "generator_params": generator_params
        },
        "merge": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/task_primitives/merge.txt",
            "generator_params": generator_params
        },
        "router": {
            "type": "router"
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "decomp_control",
        "answerer": {
            "type": "root"
        }
    },
    "reader": {
      "type": "drop",
      "add_paras": true
    }
}

