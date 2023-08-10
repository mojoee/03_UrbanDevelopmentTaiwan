import torch
from torch.nn import functional as F
from transformers import pipeline
from transformers import AutoTokenizer


torch.set_default_dtype(torch.bfloat16)

task = "zero-shot-classification"
model = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model)

#tokenizer = GPT2Tokenizer.from_pretrained(model_version)
#model = GPT2LMHeadModel.from_pretrained(model_version)
classifier = pipeline(task, model=model)

def check_tokens_in_dict(labels, tokenizer):
    c = 0
    for token in labels:
        if tokenizer.encode(token) in tokenizer.get_vocab().keys():
            c += 1
    print(f"{c} tokens in dict")


def classify_text(sentence, labels, tokenizer, model):
    inputs = tokenizer.batch_encode_plus([sentence] + labels,
                                        return_tensors='pt',
                                        pad_to_max_length=True)
    input_ids = inputs['input_ids']
    attention_mask = inputs['attention_mask']
    output = model(input_ids, attention_mask=attention_mask)[0]
    sentence_rep = output[:1].mean(dim=1)
    label_reps = output[1:].mean(dim=1)

    # now find the labels with the highest cosine similarities to
    # the sentence
    similarities = F.cosine_similarity(sentence_rep, label_reps)
    closest = similarities.argsort(descending=True)
    result = {}
    #for ind in closest:
        #print(f'label: {labels[ind]} \t similarity: {similarities[ind]}')
        
    return closest, similarities


def zero_shot_classification(text, labels):

    result_travel = classifier(text, labels, torch_dtype=torch.float16, device=0, eos_token_id=tokenizer.eos_token_id)
    return result_travel
