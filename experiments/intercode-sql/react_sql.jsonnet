local generator_params = {
    "type": "openai_chat",
    "engine": "gpt-3.5-turbo-0613",
    "max_tokens": 100,
    "temperature": 0,
    "top_p": 1,
    "stop": ["\n"]
};
{
    "models": {
        "init": {
            "type": "intercode_init",
            "next_model": "intercode_decomp"
        },
        "intercode_decomp": {
            "type": "decomp_control",
            "decomp_model": "decomp",
            "qa_model": "intercode_env",
       },
        "decomp": {
            "type": "prompted_lm",
            "prompt_file": "decomp.txt",
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
      "type": "alf"
    }
}