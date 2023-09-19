local generator_params = import "../common/default_gpt_davinci002.libsonnet";
{
    "models": {
        "l2m_letter_cat": {
            "type": "l2m_control",
            "l2m_decomp_model": "l2m_decomp",
            "l2m_qa_model": "l2m_qa",
            "next_model": "answer_ext",
        },
        "l2m_decomp": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/l2m_decomp.txt",
            "generator_params": generator_params
        },
        "l2m_qa": {
            "type": "prompted_lm",
            "prompt_file": "configs/prompts/letter_cat/l2m_qa.txt",
            "generator_params": generator_params + { "max_tokens": 200 },
        },
        "answer_ext": {
            "type": "regex_ext",
            "regex": ".* outputs \"(.*)\"\\.",
        }
    },
    "search": {
        "type": "best_first",
        "start_model": "l2m_letter_cat"
    },
    "reader": {
      "type": "drop"
    }
}