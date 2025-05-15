from datasets import load_dataset
from transformers import T5Tokenizer, T5ForConditionalGeneration, TrainingArguments, Trainer
from datasets import Dataset

import json

# Load your dataset (replace with your real data)
with open("dataset.json") as f:
    data = json.load(f)

# Split into training and validation
train_data = data[:int(0.8 * len(data))]
val_data = data[int(0.8 * len(data)):]

dataset = Dataset.from_list(train_data)
val_dataset = Dataset.from_list(val_data)

# Load tokenizer and model
tokenizer = T5Tokenizer.from_pretrained("t5-small")
model = T5ForConditionalGeneration.from_pretrained("t5-small")

# Preprocessing
def preprocess(batch):
    inputs = tokenizer(
        ["summarize: " + text for text in batch["text"]],
        truncation=True,
        padding="max_length",
        max_length=512
    )
    targets = tokenizer(
        batch["summary"],
        truncation=True,
        padding="max_length",
        max_length=150
    )
    inputs["labels"] = targets["input_ids"]
    return inputs

tokenized_train = dataset.map(preprocess, batched=True)
tokenized_val = val_dataset.map(preprocess, batched=True)

args = TrainingArguments(
    output_dir="./results",
    per_device_train_batch_size=2,
    per_device_eval_batch_size=2,
    num_train_epochs=3,
    logging_dir="./logs",
    logging_steps=10,
    save_steps=10,
    do_train=True,
    do_eval=True
)


trainer = Trainer(
    model=model,
    args=args,
    train_dataset=tokenized_train,
    eval_dataset=tokenized_val
)

trainer.train()
model.save_pretrained("finetuned_t5_model")
tokenizer.save_pretrained("finetuned_t5_model")
