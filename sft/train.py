import sys
from pathlib import Path
import warnings
sys.path.append(str(Path(__file__).parent.parent))

import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer
from peft import LoraConfig, prepare_model_for_kbit_training

from sft.dataset_builder import build_and_split_dataset


def main(
    model_name: str = "Qwen/Qwen3-4B-Instruct-2507",
    output_dir: str = "./sft-checkpoint",
):
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        dtype=torch.bfloat16,
        quantization_config=bnb_config
    )
    model = prepare_model_for_kbit_training(model)
    print(f"Loaded {model_name} for QLoRa training.\n")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    train_examples, val_examples = build_and_split_dataset()
    train_ds = Dataset.from_list([
        {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)} for ex in train_examples
    ])
    val_ds = Dataset.from_list([
        {"text": tokenizer.apply_chat_template(ex["messages"], tokenize=False)} for ex in val_examples
    ])

    peft_config = LoraConfig(
        r=32, 
        lora_alpha=64,
        lora_dropout=0.05, 
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear")

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=5,
        weight_decay=0.0,
        learning_rate=2e-3,
        lr_scheduler_type="constant",
        per_device_train_batch_size=4,
        gradient_accumulation_steps=2,
        eval_strategy="steps",
        save_strategy="steps",
        bf16=torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        logging_steps=10,
        max_length=1024,
        packing=False,
        save_steps=10,
        save_total_limit=1,
        report_to="none",
        completion_only_loss=True
    )

    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        peft_config=peft_config,
    )

    print("Start training ...\n")
    trainer.train()
    trainer.save_model(output_dir)
    print(f"SFT complete. Checkpoint saved to {output_dir}\n")

if __name__ == "__main__":
    main()