import sys
from pathlib import Path
import warnings
sys.path.append(str(Path(__file__).parent.parent))
warnings.filterwarnings("ignore")

import torch
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from trl import SFTConfig, SFTTrainer
from peft import LoraConfig, prepare_model_for_kbit_training

from sft.dataset_builder import build_sft_examples


def build_and_split_dataset(seed: int = 42, val_fraction: float = 0.15):
    """Build and split dataset for sft training."""
    examples = build_sft_examples(seed=seed)
    n_val = max(1, int(len(examples) * val_fraction))
    return examples[n_val:], examples[:n_val]  # train, val


def main(
    model_name: str = "Qwen/Qwen2.5-Math-1.5B-Instruct",
    output_dir: str = "./qwen-checkpoint",
    n_epochs: int = 20,
    learning_rate: float = 2e-5,
    use_lora: bool = True,
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
    print(f"Loaded {model_name} for QLoRa training.")
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

    peft_config = None
    if use_lora:
        peft_config = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
            task_type="CAUSAL_LM",
        )

    sft_config = SFTConfig(
        output_dir=output_dir,
        num_train_epochs=n_epochs,
        learning_rate=learning_rate,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        eval_strategy="steps",
        save_strategy="steps",
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        optim="paged_adamw_8bit",
        logging_steps=100,
        max_length=1024,
        packing=False,
        save_steps=100,
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

    print("Start training ...")
    trainer.train()
    print("Done training!")
    trainer.save_model(output_dir)
    print(f"SFT complete. Checkpoint saved to {output_dir}")
    # Next step: use this checkpoint as the starting model_name in ppo_finetune.py


if __name__ == "__main__":
    main()