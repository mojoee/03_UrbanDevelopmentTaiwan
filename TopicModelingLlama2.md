# **Topic Modeling with Llama2** 🦙
*Create easily interpretable topics with BERTopic and Llama 2*
<br>
<div>
<img src="https://github.com/MaartenGr/BERTopic/assets/25746895/35441954-4405-465c-97f7-a57ee91315b8" width="750"/>
</div>


We will explore how we can use Llama2 for Topic Modeling without the need to pass every single document to the model. Instead, we are going to leverage BERTopic, a modular topic modeling technique that can use any LLM for fine-tuning topic representations.

BERTopic works rather straightforward. It consists of 5 sequential steps: embedding documents, reducing embeddings in dimensionality, cluster embeddings, tokenize documents per cluster, and finally extract the best representing words per topic.
<br>
<div>
<img src="https://github.com/MaartenGr/BERTopic/assets/25746895/e9b0d8cf-2e19-4bf1-beb4-4ff2d9fa5e2d" width="500"/>
</div>

However, with the rise of LLMs like **Llama 2**, we can do much better than a bunch of independent words per topic. It is computally not feasible to pass all documents to Llama 2 directly and have it analyze them. We can employ vector databases for search but we are not entirely search which topics to search for.

Instead, we will leverage the clusters and topics that were created by BERTopic and have Llama 2 fine-tune and distill that information into something more accurate.

This is the best of both worlds, the topic creation of BERTopic together with the topic representation of Llama 2.
<br>
<div>
<img src="https://github.com/MaartenGr/BERTopic/assets/25746895/7c7374a1-5b41-4e93-aafd-a1587367767b" width="500"/>
</div>

Now that this intro is out of the way, let's start the hands-on tutorial!

# 📄 **Data**

Datasets are the titles and proposals of the e-participation platformns


```python
from urbandev.utils import load_dataset

source = "JOIN"   # JOIN, or ivoting
docs, labels, timestamps = load_dataset(source=source, type='sklearn')
# Extract abstracts to train on and corresponding titles

```

To give you an idea, a doc looks like the following:


```python
# Example usage
from urbandev.utils import load_json
translate=False
if translate:
    json_file = "./data/JoinData2025.json"  # Update this with the actual JSON file path
    df = load_json(json_file)

    # Save to Excel
    output_file = "./data/JoinData2025.xlsx"
    df.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}")

```


```python
print(docs[400])
```

    Relaxing remote townships (six metropolis: population below 50,000. Non -six capital counties and cities: below 30,000) set up hospital restrictions to balance the distribution of medical resources._1. Article 6, paragraph 1 of the current "Establishment or Expansion License Measures for Hospitals": Acute general beds in the secondary medical area, per 1,000 people shall not exceed 50 beds; in the first -level medical area, acute average beds have a hospital of 500 beds above 500 beds or above. The number of beds must not exceed six beds per 10,000 people.
    2. Since the implementation of the above provisions for seven years, the restrictions of the so -called "per thousand people must not exceed 50 beds" are only accelerating the development of the medical concentration metropolitan area.
    Third, remote towns and regions, the population is scarce, coupled with the area and setting cost of the hospital's acute bed, the cost of the setting of the bed has increased year by year, it is not easy to attract aspiration doctors to invest in grass -roots medical services in the hometown. For large consortium legal persons, under the assessment principle of investment feedback rates, many remote towns are evaluated as not -listed investment areas.
    4. The restrictions on the above provisions have led to a few kilometers around or even more than ten kilometers around many township administrative districts.
    V. Specific measures: Article 6, paragraph 1 of the "Hospital Establishing or Expanded License Measures" mentioned above, adds to the book: But the book in the six municipalities in the six major cities or less than 30,000 townships in the administrative district or non -six capital counties and cities In the district, the hospital with the number of acute average beds below the 499 beds will not be limited by the aforementioned people with no more than 50 beds.
    6. With the aging trend of the social population, the hospital has gradually become a sufficient condition in people's lives. However, the hospital excessively concentrated on the metropolitan area, remote towns and towns for more than ten kilometers, but no hospital. It will only drive the population living in remote towns and leave the original place due to medical needs. Essence
    Seventh, the establishment of a stable scale will also bring a sense of stability of local aging, which should be included in one of the policy promotion measures of the government's long -term photo 2.0.


# 🤗 HuggingFace Hub Credentials
Before we can load in Llama2 using a number of tricks, we will first need to accept the License for using Llama2. The steps are as follows:


* Create a HuggingFace account [here](https://huggingface.co)
* Apply for Llama 2 access [here](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf)
* Get your HuggingFace token [here](https://huggingface.co/settings/tokens)

After doing so, we can login with our HuggingFace credentials so that this environment knows we have permission to download the Llama 2 model that we are interested in.


```python
from huggingface_hub import notebook_login
# key: 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
notebook_login()
```


    VBox(children=(HTML(value='<center> <img\nsrc=https://huggingface.co/front/assets/huggingface_logo-noborder.sv…


# 🦙 **Llama 2**

Now comes one of the more interesting components of this tutorial, how to load in a Llama 2 model on a T4-GPU!

We will be focusing on the `'meta-llama/Llama-2-13b-chat-hf'` variant. It is large enough to give interesting and useful results whilst small enough that it can be run on our environment.

We start by defining our model and identifying if our GPU is correctly selected. We expect the output of `device` to show a cuda device:


```python
from torch import cuda

model_id = 'meta-llama/Llama-2-13b-chat-hf'
#model_id = "meta-llama/Meta-Llama-3-8B-Instruct"
device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

print(device)
```

    cuda:0


## **Optimization & Quantization**

In order to load our 13 billion parameter model, we will need to perform some optimization tricks. Since we have limited VRAM and not an A100 GPU, we will need to "condense" the model a bit so that we can run it.

There are a number of tricks that we can use but the main principle is going to be 4-bit quantization.

This process reduces the 64-bit representation to only 4-bits which reduces the GPU memory that we will need. It is a recent technique and quite an elegant at that for efficient LLM loading and usage. You can find more about that method [here](https://arxiv.org/pdf/2305.14314.pdf) in the QLoRA paper and on the amazing HuggingFace blog [here](https://huggingface.co/blog/4bit-transformers-bitsandbytes).


```python
from torch import bfloat16
import transformers

# set quantization configuration to load large model with less GPU memory
# this requires the `bitsandbytes` library

bnb_config = transformers.BitsAndBytesConfig(
    load_in_4bit=True,  # 4-bit quantization
    bnb_4bit_quant_type='nf4',  # Normalized float 4
    bnb_4bit_use_double_quant=True,  # Second quantization after the first
    bnb_4bit_compute_dtype=bfloat16,  # Computation type
    llm_int8_enable_fp32_cpu_offload=True
)
```

These four parameters that we just run are incredibly important and bring many LLM applications to consumers:
* `load_in_4bit`
  * Allows us to load the model in 4-bit precision compared to the original 32-bit precision
  * This gives us an incredibly speed up and reduces memory!
* `bnb_4bit_quant_type`
  * This is the type of 4-bit precision. The paper recommends normalized float 4-bit, so that is what we are going to use!
* `bnb_4bit_use_double_quant`
  * This is a neat trick as it perform a second quantization after the first which further reduces the necessary bits
* `bnb_4bit_compute_dtype`
  * The compute type used during computation, which further speeds up the model.



Using this configuration, we can start loading in the model as well as the tokenizer:


```python
# Llama 2 Tokenizer
tokenizer = transformers.AutoTokenizer.from_pretrained(model_id)


device_map = {
    "transformer.word_embeddings": 0,
    "transformer.word_embeddings_layernorm": 0,
    "lm_head": "cpu",
    "transformer.h": 0,
    "transformer.ln_f": 0,
    "model.embed_tokens": "cpu",
    "model.layers.0.input_layernorm.weight": "cpu",
    "model.layers.0.mlp.down_proj.weight": "cpu",
    "model.layers.0.mlp.gate_proj.weight": "cpu",
    "model.layers.0.mlp.up_proj.weight": "cpu",
    "model.layers.0.post_attention_layernorm.weight": "cpu",
    "model.layers.0.self_attn.k_proj.weight": "cpu",
    "model.layers.0.self_attn.o_proj.weight": "cpu",
    "model.layers.0.self_attn.q_proj.weight": "cpu",
    "model.layers": "cpu",
    "model.norm.weight": "cpu"
}

# Llama 2 Model
model = transformers.AutoModelForCausalLM.from_pretrained(
    model_id,
    trust_remote_code=True,
    quantization_config=bnb_config,
    device_map="auto",

)
model.eval()
```


    Loading checkpoint shards:   0%|          | 0/3 [00:00<?, ?it/s]





    LlamaForCausalLM(
      (model): LlamaModel(
        (embed_tokens): Embedding(32000, 5120, padding_idx=0)
        (layers): ModuleList(
          (0-39): 40 x LlamaDecoderLayer(
            (self_attn): LlamaAttention(
              (q_proj): Linear4bit(in_features=5120, out_features=5120, bias=False)
              (k_proj): Linear4bit(in_features=5120, out_features=5120, bias=False)
              (v_proj): Linear4bit(in_features=5120, out_features=5120, bias=False)
              (o_proj): Linear4bit(in_features=5120, out_features=5120, bias=False)
              (rotary_emb): LlamaRotaryEmbedding()
            )
            (mlp): LlamaMLP(
              (gate_proj): Linear4bit(in_features=5120, out_features=13824, bias=False)
              (up_proj): Linear4bit(in_features=5120, out_features=13824, bias=False)
              (down_proj): Linear4bit(in_features=13824, out_features=5120, bias=False)
              (act_fn): SiLUActivation()
            )
            (input_layernorm): LlamaRMSNorm()
            (post_attention_layernorm): LlamaRMSNorm()
          )
        )
        (norm): LlamaRMSNorm()
      )
      (lm_head): Linear(in_features=5120, out_features=32000, bias=False)
    )



Using the model and tokenizer, we will generate a HuggingFace transformers pipeline that allows us to easily generate new text:


```python
# Our text generator
generator = transformers.pipeline(
    model=model, tokenizer=tokenizer,
    task='text-generation',
    temperature=0.1,
    max_new_tokens=500,
    repetition_penalty=1.1
)
```

    Xformers is not installed correctly. If you want to use memory_efficient_attention to accelerate training use the following command to install Xformers
    pip install xformers.


## **Prompt Engineering**

To check whether our model is correctly loaded, let's try it out with a few prompts.


```python
prompt = "Could you explain to me how 4-bit quantization works as if I am 5?"
res = generator(prompt)
print(res[0]["generated_text"])
```

    Could you explain to me how 4-bit quantization works as if I am 5?
    
    Sure! Imagine you have a big box of crayons. Each crayon represents a different color, like red, blue, green, and so on. Now, imagine that instead of using all the different colors, we only use four colors: red, blue, green, and yellow. This is like 4-bit quantization.
    
    So, when we want to draw a picture, we can only choose one of these four colors to use. We can't mix them together or use any other colors. It's like we're limited to just these four colors.
    
    For example, let's say we want to draw a tree. We could use the green crayon to draw the leaves, but we couldn't use the blue crayon to draw the sky because it's not one of our allowed colors. Instead, we would have to use the yellow crayon to draw the sky.
    
    This is kind of like how 4-bit quantization works in computers. Instead of using all the different numbers that a computer can represent, we only use four bits (or colors) to represent everything. So, instead of being able to use any number we want, we can only use one of these four "colors" to represent each number.


Although we can directly prompt the model, there is actually a template that we need to follow. The template looks as follows:

```python
"""
<s>[INST] <<SYS>>

{{ System Prompt }}

<</SYS>>

{{ User Prompt }} [/INST]

{{ Model Answer }}
"""
```

This template consists of two main components, namely the `{{ System Prompt }}` and the `{{ User Prompt }}`:
* The `{{ System Prompt }}` helps us guide the model during a conversation. For example, we can say that it is a helpful assisant that is specialized in labeling topics.
* The  `{{ User Prompt }}` is where we ask it a question.

You might have noticed the `[INST]` tags, these are used to identify the beginning and end of a prompt. We can use these to model the conversation history as we will see more in-depth later on.

Next, let's see how we can use this template to optimize Llama 2 for topic modeling.

### **Prompt Template**

We are going to keep our `system prompt` simple and to the point:


```python
# System prompt describes information given to all conversations
system_prompt = """
<s>[INST] <<SYS>>
You are a helpful, respectful and honest assistant for labeling topics.
<</SYS>>
"""
```

We will tell the model that it is simply a helpful assistant for labeling topics since that is our main goal.

In contrast, our `user prompt` is going to the be a bit more involved. It will consist of two components, an **example** and the **main prompt**.

Let's start with the **example**. Most LLMs do a much better job of generating accurate responses if you give them an example to work with. We will show it an accurate example of the kind of output we are expecting.


```python
# Example prompt demonstrating the output we are looking for
example_prompt = """
I have a topic that contains the following documents:
- Traditional diets in most cultures were primarily plant-based with a little meat on top, but with the rise of industrial style meat production and factory farming, meat has become a staple food.
- Meat, but especially beef, is the word food in terms of emissions.
- Eating meat doesn't make you a bad person, not eating meat doesn't make you a good one.

The topic is described by the following keywords: 'meat, beef, eat, eating, emissions, steak, food, health, processed, chicken'.

Based on the information about the topic above, please create a short label of this topic. Make sure you to only return the label and nothing more.

[/INST] Environmental impacts of eating meat
"""
```

This example, based on a number of keywords and documents primarily about the impact of
meat, helps to model to understand the kind of output it should give. We show the model that we were expecting only the label, which is easier for us to extract.

Next, we will create a template that we can use within BERTopic:


```python
# Our main prompt with documents ([DOCUMENTS]) and keywords ([KEYWORDS]) tags
main_prompt = """
[INST]
I have a topic that contains the following documents:
[DOCUMENTS]

The topic is described by the following keywords: '[KEYWORDS]'.

Based on the information about the topic above, please create a short label of this topic. Make sure you to only return the label and nothing more.
[/INST]
"""
```

There are two BERTopic-specific tags that are of interest, namely `[DOCUMENTS]` and `[KEYWORDS]`:

* `[DOCUMENTS]` contain the top 5 most relevant documents to the topic
* `[KEYWORDS]` contain the top 10 most relevant keywords to the topic as generated through c-TF-IDF

This template will be filled accordingly to each topic. And finally, we can combine this into our final prompt:


```python
prompt = system_prompt + example_prompt + main_prompt
```

# 🗨️ **BERTopic**

Before we can start with topic modeling, we will first need to perform two steps:
* Pre-calculating Embeddings
* Defining Sub-models

## **Preparing Embeddings**

By pre-calculating the embeddings for each document, we can speed-up additional exploration steps and use the embeddings to quickly iterate over BERTopic's hyperparameters if needed.

🔥 **TIP**: You can find a great overview of good embeddings for clustering on the [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard).


```python
from sentence_transformers import SentenceTransformer

# Pre-calculate embeddings
embedding_model = SentenceTransformer("BAAI/bge-large-en")
embeddings = embedding_model.encode(docs, show_progress_bar=True)
```


    Batches:   0%|          | 0/654 [00:00<?, ?it/s]


## **Sub-models**

Next, we will define all sub-models in BERTopic and do some small tweaks to the number of clusters to be created, setting random states, etc.


```python
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer

if source=="iVoting":
    min_cluster_size = 5
elif source=="JOIN":
    min_cluster_size = 150
UMAP_neighbors = 50

umap_model = UMAP(n_neighbors=UMAP_neighbors, n_components=20, min_dist=0.0, metric='cosine', random_state=42)
hdbscan_model = HDBSCAN(min_cluster_size=min_cluster_size, metric='euclidean', cluster_selection_method='eom', prediction_data=True)
vectorizer_model = CountVectorizer(stop_words="english")
```

    /media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/.venv/lib/python3.11/site-packages/umap/distances.py:1063: NumbaDeprecationWarning: The 'nopython' keyword argument was not supplied to the 'numba.jit' decorator. The implicit default value for this argument is currently False, but it will be changed to True in Numba 0.59.0. See https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-object-mode-fall-back-behaviour-when-using-jit for details.
      @numba.jit()
    /media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/.venv/lib/python3.11/site-packages/umap/distances.py:1071: NumbaDeprecationWarning: The 'nopython' keyword argument was not supplied to the 'numba.jit' decorator. The implicit default value for this argument is currently False, but it will be changed to True in Numba 0.59.0. See https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-object-mode-fall-back-behaviour-when-using-jit for details.
      @numba.jit()
    /media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/.venv/lib/python3.11/site-packages/umap/distances.py:1086: NumbaDeprecationWarning: The 'nopython' keyword argument was not supplied to the 'numba.jit' decorator. The implicit default value for this argument is currently False, but it will be changed to True in Numba 0.59.0. See https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-object-mode-fall-back-behaviour-when-using-jit for details.
      @numba.jit()
    /media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/.venv/lib/python3.11/site-packages/umap/umap_.py:660: NumbaDeprecationWarning: The 'nopython' keyword argument was not supplied to the 'numba.jit' decorator. The implicit default value for this argument is currently False, but it will be changed to True in Numba 0.59.0. See https://numba.readthedocs.io/en/stable/reference/deprecation.html#deprecation-of-object-mode-fall-back-behaviour-when-using-jit for details.
      @numba.jit()


As a small bonus, we are going to reduce the embeddings we created before to 2-dimensions so that we can use them for visualization purposes when we have created our topics.


```python
# Pre-reduce embeddings for visualization purposes
reduced_embeddings = UMAP(n_neighbors=20, n_components=2, min_dist=0.2, metric='cosine', random_state=42).fit_transform(embeddings)
```

### **Representation Models**

One of the ways we are going to represent the topics is with Llama 2 which should give us a nice label. However, we might want to have additional representations to view a topic from multiple angles.

Here, we will be using c-TF-IDF as our main representation and [KeyBERT](https://maartengr.github.io/BERTopic/getting_started/representation/representation.html#keybertinspired), [MMR](https://maartengr.github.io/BERTopic/getting_started/representation/representation.html#maximalmarginalrelevance), and [Llama 2](https://maartengr.github.io/BERTopic/getting_started/representation/llm.html) as our additional representations.


```python
from bertopic.representation import KeyBERTInspired, MaximalMarginalRelevance, TextGeneration

# KeyBERT
keybert = KeyBERTInspired()

# MMR
mmr = MaximalMarginalRelevance(diversity=0.2)

# Text generation with Llama 2
llama2 = TextGeneration(generator, prompt=prompt)

# All representation models
representation_model = {
    "KeyBERT": keybert,
    "Llama2": llama2,
    "MMR": mmr,
}
```

# 🔥 **Training**

Now that we have our models prepared, we can start training our topic model! We supply BERTopic with the sub-models of interest, run `.fit_transform`, and see what kind of topics we get.


```python
from bertopic import BERTopic

topic_model = BERTopic(

  # Sub-models
  embedding_model=embedding_model,
  umap_model=umap_model,
  hdbscan_model=hdbscan_model,
  representation_model=representation_model,
  vectorizer_model=vectorizer_model,

  # Hyperparameters
  top_n_words=10,
  verbose=True
)

# Train model
#topics, probs = topic_model.fit_transform(docs, embeddings, y=labels)
topics, probs = topic_model.fit_transform(docs, embeddings)

```

    2025-02-06 18:57:53,172 - BERTopic - Reduced dimensionality


    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)


    2025-02-06 18:57:56,175 - BERTopic - Clustered reduced embeddings
    100%|██████████| 20/20 [00:13<00:00,  1.43it/s]


Now that we are done training our model, let's see what topics were generated:


```python
# Show topics
dfOut = topic_model.get_topic_info()
```


```python
dfOut
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Topic</th>
      <th>Count</th>
      <th>Name</th>
      <th>Representation</th>
      <th>KeyBERT</th>
      <th>Llama2</th>
      <th>MMR</th>
      <th>Representative_Docs</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>-1</td>
      <td>6710</td>
      <td>-1_people_government_taiwan_public</td>
      <td>[people, government, taiwan, public, law, use,...</td>
      <td>[taiwan, china, article, country, yuan, public...</td>
      <td>[Government and Public Policy in Taiwan, , , ,...</td>
      <td>[people, government, taiwan, public, law, use,...</td>
      <td>[Strict punishment for punishment_Forcing the ...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2702</td>
      <td>0_school_students_education_high</td>
      <td>[school, students, education, high, teachers, ...</td>
      <td>[school, students, schools, education, taiwan,...</td>
      <td>[Reforms in Taiwanese Education, , , , , , , ,...</td>
      <td>[school, students, education, high, teachers, ...</td>
      <td>[After 12 years of national teaching, college ...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>1947</td>
      <td>1_road_traffic_car_speed</td>
      <td>[road, traffic, car, speed, lane, light, drivi...</td>
      <td>[highway, road, vehicle, vehicles, locomotive,...</td>
      <td>[Road Safety and Traffic Management, , , , , ,...</td>
      <td>[road, traffic, car, speed, lane, light, drivi...</td>
      <td>[Please simplify the rules of priority rights ...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2</td>
      <td>1294</td>
      <td>2_power_nuclear_water_plastic</td>
      <td>[power, nuclear, water, plastic, food, energy,...</td>
      <td>[taiwan, nuclear, energy, environment, power, ...</td>
      <td>[Sustainable Energy and Environmental Protecti...</td>
      <td>[power, nuclear, water, plastic, food, energy,...</td>
      <td>[Ask the government to lead the people to save...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3</td>
      <td>1149</td>
      <td>3_epidemic_medical_health_insurance</td>
      <td>[epidemic, medical, health, insurance, people,...</td>
      <td>[taiwan, china, patient, medical, country, for...</td>
      <td>[Taiwan's Healthcare Response to Severe Epidem...</td>
      <td>[epidemic, medical, health, insurance, people,...</td>
      <td>[Health Insurance Complete Reform Solutions-Co...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>4</td>
      <td>997</td>
      <td>4_labor_salary_workers_work</td>
      <td>[labor, salary, workers, work, hours, day, ove...</td>
      <td>[overtime, salary, workers, employee, labor, h...</td>
      <td>[Labor and Overtime Pay in China, , , , , , , ...</td>
      <td>[labor, salary, workers, work, hours, day, ove...</td>
      <td>[The time salary of overtime pay is seriously ...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>5</td>
      <td>810</td>
      <td>5_death_criminal_penalty_crime</td>
      <td>[death, criminal, penalty, crime, years, sexua...</td>
      <td>[taiwan, sentenced, imprisonment, china, execu...</td>
      <td>[Debate over the death penalty in Taiwan, , , ...</td>
      <td>[death, criminal, penalty, crime, years, sexua...</td>
      <td>[Modify Article 271 of the Criminal Law_Propos...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>6</td>
      <td>743</td>
      <td>6_railway_station_rail_speed</td>
      <td>[railway, station, rail, speed, line, high, ro...</td>
      <td>[kaohsiung, keelung, taichung, pingtung, zuoyi...</td>
      <td>[High-Speed Rail Extension in Pingtung, Taiwan...</td>
      <td>[railway, station, rail, speed, line, high, ro...</td>
      <td>[The high -speed rail extension Pingtung Zuoyi...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>7</td>
      <td>729</td>
      <td>7_election_voting_political_votes</td>
      <td>[election, voting, political, votes, legislato...</td>
      <td>[elected, election, voters, elections, represe...</td>
      <td>[Electoral reforms in Taiwan, , , , , , , , , ]</td>
      <td>[election, voting, political, votes, legislato...</td>
      <td>[Requires the relevant regulations such as the...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>8</td>
      <td>535</td>
      <td>8_military_service_defense_soldiers</td>
      <td>[military, service, defense, soldiers, women, ...</td>
      <td>[society, military, equality, army, gender, ch...</td>
      <td>[Gender and Military Service, , , , , , , , , ]</td>
      <td>[military, service, defense, soldiers, women, ...</td>
      <td>[Amending the "Military Service Law" refers to...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>9</td>
      <td>513</td>
      <td>9_china_republic_taiwan_country</td>
      <td>[china, republic, taiwan, country, chinese, ho...</td>
      <td>[taiwan, china, taiwanese, republic, nationali...</td>
      <td>[Nationality and Identity in China, , , , , , ...</td>
      <td>[china, republic, taiwan, country, chinese, ho...</td>
      <td>[The abbreviation of the Republic of China, us...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>10</td>
      <td>461</td>
      <td>10_animals_dogs_animal_pet</td>
      <td>[animals, dogs, animal, pet, cats, stray, pets...</td>
      <td>[taiwan, pet, stray, animals, dogs, public, an...</td>
      <td>[Pet and Stray Animal Management, , , , , , , ...</td>
      <td>[animals, dogs, animal, pet, cats, stray, pets...</td>
      <td>[Cats and dogs across the country (including c...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>11</td>
      <td>427</td>
      <td>11_driving_drunk_alcohol_driver</td>
      <td>[driving, drunk, alcohol, driver, years, drink...</td>
      <td>[fined, penalty, penalties, offenders, sentenc...</td>
      <td>[Drunk Driving Laws and Penalties, , , , , , ,...</td>
      <td>[driving, drunk, alcohol, driver, years, drink...</td>
      <td>[Increased the liability of alcohol. Drunk dri...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>12</td>
      <td>416</td>
      <td>12_smoke_smoking_cigarettes_cigarette</td>
      <td>[smoke, smoking, cigarettes, cigarette, health...</td>
      <td>[tobacco, smokers, taiwan, smoking, cigarettes...</td>
      <td>[Tobacco Control Measures and Smoke Tax, , , ,...</td>
      <td>[smoke, smoking, cigarettes, cigarette, health...</td>
      <td>[Set up a smoking room to encourage people to ...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>13</td>
      <td>360</td>
      <td>13_house_housing_tax_price</td>
      <td>[house, housing, tax, price, land, houses, est...</td>
      <td>[land, housing, property, houses, households, ...</td>
      <td>[Housing market regulation, , , , , , , , , ]</td>
      <td>[house, housing, tax, price, land, houses, est...</td>
      <td>[Treatment of land hoarding to achieve average...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>14</td>
      <td>289</td>
      <td>14_children_child_childcare_parents</td>
      <td>[children, child, childcare, parents, care, fe...</td>
      <td>[taiwan, salary, increase, rate, income, child...</td>
      <td>[Parenting and Fertility Support in Taiwan, , ...</td>
      <td>[children, child, childcare, parents, care, fe...</td>
      <td>[Take various measures to increase Taiwan's fe...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>15</td>
      <td>236</td>
      <td>15_news_media_information_fake</td>
      <td>[news, media, information, fake, online, platf...</td>
      <td>[reporters, reporter, media, report, political...</td>
      <td>[Media Ethics and Regulation, , , , , , , , , ]</td>
      <td>[news, media, information, fake, online, platf...</td>
      <td>[Online platform media professional ethics lac...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>16</td>
      <td>223</td>
      <td>16_license_age_driver_test</td>
      <td>[license, age, driver, test, driving, 16, old,...</td>
      <td>[age, motorcycle, driving, taiwan, license, ro...</td>
      <td>[Lowering the Age Limit for Obtaining a Motorc...</td>
      <td>[license, age, driver, test, driving, 16, old,...</td>
      <td>[Falling the age of driving in the driving mot...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>17</td>
      <td>205</td>
      <td>17_https_www_com_marriage</td>
      <td>[https, www, com, marriage, html, cc, tw, news...</td>
      <td>[四等親, 中國大陸, 紐西蘭, 那你們就不知道優生學是限制到四等親最科學嗎, 如果兩人都為...</td>
      <td>[\nMarriage laws and regulations across differ...</td>
      <td>[https, www, com, marriage, html, cc, tw, news...</td>
      <td>[The civil law stipulates that the six -class ...</td>
    </tr>
    <tr>
      <th>19</th>
      <td>18</td>
      <td>177</td>
      <td>18_tax_yuan_card_payment</td>
      <td>[tax, yuan, card, payment, 000, banknotes, cre...</td>
      <td>[taiwan, banknote, subsidy, income, yuan, chin...</td>
      <td>[Fiscal policies and taxation, , , , , , , , , ]</td>
      <td>[tax, yuan, card, payment, 000, banknotes, cre...</td>
      <td>[Unified the final end of various payment, ful...</td>
    </tr>
  </tbody>
</table>
</div>




```python
# save it to text
dfOut.to_csv("Topicssize50.csv")
```

We got over 100 topics that were created and they all seem quite diverse.We can use the labels by Llama 2 and assign them to topics that we have created. Normally, the default topic representation would be c-TF-IDF, but we will focus on Llama 2 representations instead.



```python

```


```python
#need to remove \n in front

llama2_labels = [label[0][0].split("\n")[1] if label[0][0].startswith('\n') else label[0][0].split("\n")[0] for label in topic_model.get_topics(full=True)["Llama2"].values()]
topic_model.set_topic_labels(llama2_labels)
```

# 📊 **Visualize**
We can go through each topic manually, which would take a lot of work, or we can visualize them all in a single interactive graph.
BERTopic has a bunch of [visualization functions](https://medium.com/r/?url=https%3A%2F%2Fmaartengr.github.io%2FBERTopic%2Fgetting_started%2Fvisualization%2Fvisualize_documents.html) that we can use. For now, we are sticking with visualizing the documents.


```python
titles=[]
for doc in docs:
    titles.append(doc[:30])
```


```python
topic_model.visualize_documents(titles, title="Topic Model Join 2015-2025", reduced_embeddings=reduced_embeddings, hide_annotations=True, hide_document_hover=True, custom_labels=True)
```



# 🖼️ (BONUS): **Advanced Visualization**

Although we can use the built-in visualization features of BERTopic, we can also create a static visualization that might be a bit more informative.

We start by creating the necessary variables that contain our reduced embeddings and representations:


```python
import itertools
import pandas as pd

# Define colors for the visualization to iterate over
colors = itertools.cycle(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#d00000', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000'])
color_key = {str(topic): next(colors) for topic in set(topic_model.topics_)}

# Prepare dataframe and ignore outliers
df = pd.DataFrame({"x": reduced_embeddings[:, 0], "y": reduced_embeddings[:, 1], "Topic": [str(t) for t in topic_model.topics_]})
df["Length"] = [len(doc) for doc in docs]
df = df.loc[df.Topic != "-1"]
df = df.loc[(df.y > -10) & (df.y < 10) & (df.x < 10) & (df.x > -10), :]
df["Topic"] = df["Topic"].astype("category")

# Get centroids of clusters
mean_df = df.groupby("Topic").mean().reset_index()
mean_df.Topic = mean_df.Topic.astype(int)
mean_df = mean_df.sort_values("Topic")
```


```python
import seaborn as sns
from matplotlib import pyplot as plt
from adjustText import adjust_text
import matplotlib.patheffects as pe
import textwrap

fig = plt.figure(figsize=(20, 20))
sns.scatterplot(data=df, x='x', y='y', c=df['Topic'].map(color_key), alpha=0.5, sizes=(20, 10), size="Length")

# Annotate top 50 topics
texts, xs, ys = [], [], []
for row in mean_df.iterrows():
  topic = row[1]["Topic"]
  name = textwrap.fill(topic_model.custom_labels_[int(topic)+1], 20)

  if int(topic) <= 50:
    xs.append(row[1]["x"])
    ys.append(row[1]["y"])
    texts.append(plt.text(row[1]["x"], row[1]["y"], name, size=18, ha="center", color=color_key[str(int(topic))],
                          path_effects=[pe.withStroke(linewidth=0.5, foreground="black")]
                          ))

# Adjust annotations such that they do not overlap
adjust_text(texts, x=xs, y=ys, time_lim=1, force_text=(0.01, 0.02), force_static=(0.01, 0.02), force_pull=(0.5, 0.5))
plt.axis('off')
plt.legend('', frameon=False)
plt.savefig(f'./results/Llama2Visualization_{source}_{min_cluster_size}_{UMAP_neighbors}.png', dpi=600)
plt.show()
```


    
![png](TopicModelingLlama2_files/TopicModelingLlama2_53_0.png)
    



```python
# filter out passed proposals
import numpy as np
data = load_dataset(source=source, type="pandas")
if source=="JOIN":
    data["Passed"] = "No"
    data['Passed'] = np.where(data["upvotes"] >= data["threshold"], 1, data['Passed'])
    data['Passed'] = np.where(data["threshold"]==0, 0, data['Passed'])
elif source=="iVoting":
    data["Passed"] = "No"
    data['Passed'] = np.where(data["seconds"] >= 3000, 1, data['Passed'])
    data['Passed'] = np.where(data["seconds"]==0, 0, data['Passed'])
```


```python
# Define colors for the visualization to iterate over
colors = itertools.cycle(['#e6194b', '#3cb44b', '#ffe119', '#4363d8', '#f58231', '#911eb4', '#46f0f0', '#f032e6', '#bcf60c', '#fabebe', '#008080', '#e6beff', '#9a6324', '#d00000', '#800000', '#aaffc3', '#808000', '#ffd8b1', '#000075', '#808080', '#ffffff', '#000000'])
color_key = {str(topic): next(colors) for topic in set(topic_model.topics_)}

# Prepare dataframe and ignore outliers
df = pd.DataFrame({"x": reduced_embeddings[:, 0], "y": reduced_embeddings[:, 1], "Topic": [str(t) for t in topic_model.topics_]})
df["Length"] = [len(doc) for doc in docs]
df = df.loc[df.Topic != "-1"]
df = df.loc[(df.y > -10) & (df.y < 10) & (df.x < 10) & (df.x > -10), :]
df["Topic"] = df["Topic"].astype("category")
df["Passed"] = data["Passed"]
df=df[df["Passed"]==1]

# Get centroids of clusters
mean_df = df.groupby("Topic").mean().reset_index()
mean_df.Topic = mean_df.Topic.astype(int)
mean_df = mean_df.sort_values("Topic")
```


```python
# plot only passed proposals
fig = plt.figure(figsize=(20, 20))
sns.scatterplot(data=df, x='x', y='y', c=df['Topic'].map(color_key), alpha=0.8, sizes=(5, 10), size="Length")

# Annotate top 50 topics
texts, xs, ys = [], [], []
for row in mean_df.iterrows():
  topic = row[1]["Topic"]
  name = textwrap.fill(topic_model.custom_labels_[int(topic)+1], 20)

  if int(topic) <= 50:
    xs.append(row[1]["x"])
    ys.append(row[1]["y"])
    texts.append(plt.text(row[1]["x"], row[1]["y"], name, size=18, ha="center", color=color_key[str(int(topic))],
                          path_effects=[pe.withStroke(linewidth=0.5, foreground="black")]
                          ))

# Adjust annotations such that they do not overlap
adjust_text(texts, x=xs, y=ys, time_lim=1, force_text=(0.01, 0.02), force_static=(0.01, 0.02), force_pull=(0.5, 0.5))
plt.axis('off')
plt.legend('', frameon=False)
plt.savefig(f'./results/Llama2Visualization_{source}_{min_cluster_size}_{UMAP_neighbors}.png')
plt.show()
```

    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values
    posx and posy should be finite values



    
![png](TopicModelingLlama2_files/TopicModelingLlama2_56_1.png)
    


# Backup Saving


```python
# To save: model, reduced embeddings, representative docs
!pip install safetensors
```

    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    Requirement already satisfied: safetensors in ./.venv/lib/python3.11/site-packages (0.3.2)
    
    [1m[[0m[34;49mnotice[0m[1;39;49m][0m[39;49m A new release of pip is available: [0m[31;49m23.2.1[0m[39;49m -> [0m[32;49m25.0[0m
    [1m[[0m[34;49mnotice[0m[1;39;49m][0m[39;49m To update, run: [0m[32;49mpip install --upgrade pip[0m



```python
import pickle

with open('rep_docs.pickle', 'wb') as handle:
    pickle.dump(topic_model.representative_docs_, handle, protocol=pickle.HIGHEST_PROTOCOL)

with open('reduced_embeddings.pickle', 'wb') as handle:
    pickle.dump(reduced_embeddings, handle, protocol=pickle.HIGHEST_PROTOCOL)

# with open('filename.pickle', 'rb') as handle:
#     b = pickle.load(handle)
```


```python
embedding_model = "BAAI/bge-large-en"
topic_model.save("final", serialization="safetensors", save_ctfidf=True, save_embedding_model=embedding_model)
```


```python
!zip -r /content/llama2.zip /content/final

```

    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    	zip warning: name not matched: /content/final
    
    zip error: Nothing to do! (try: zip -r /content/llama2.zip . -i /content/final)



```python
!jupyter nbconvert --to markdown TopicModelingLlama2.ipynb
```

    huggingface/tokenizers: The current process just got forked, after parallelism has already been used. Disabling parallelism to avoid deadlocks...
    To disable this warning, you can either:
    	- Avoid using `tokenizers` before the fork if possible
    	- Explicitly set the environment variable TOKENIZERS_PARALLELISM=(true | false)
    [NbConvertApp] Converting notebook TopicModelingLlama2.ipynb to markdown
    /media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/.venv/lib/python3.11/site-packages/nbconvert/filters/datatypefilter.py:39: UserWarning: Your element with mimetype(s) dict_keys(['application/vnd.plotly.v1+json']) is not able to be represented.
      warn("Your element with mimetype(s) {mimetypes}"
    [NbConvertApp] Support files will be in TopicModelingLlama2_files/
    [NbConvertApp] Making directory TopicModelingLlama2_files
    [NbConvertApp] Making directory TopicModelingLlama2_files
    [NbConvertApp] Making directory TopicModelingLlama2_files
    [NbConvertApp] Writing 95304 bytes to TopicModelingLlama2.md



```python
from numpy import dot
from numpy.linalg import norm

def get_cos_sim(a, b):
    cos_sim = dot(a, b)/(norm(a)*norm(b))
    return cos_sim

closest_topic = []
for emb in embeddings:
    sims=[]
    for i in range(len(topic_model.topic_embeddings_)):
        b=topic_model.topic_embeddings_[i]
        cos_sim=get_cos_sim(emb,b)
        sims.append(cos_sim)
    n=sims.index(max(sims))
    closest_topic.append(n)

```


```python
topic_model.get_topic_info()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Topic</th>
      <th>Count</th>
      <th>Name</th>
      <th>CustomName</th>
      <th>Representation</th>
      <th>KeyBERT</th>
      <th>Llama2</th>
      <th>MMR</th>
      <th>Representative_Docs</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>-1</td>
      <td>6710</td>
      <td>-1_people_government_taiwan_public</td>
      <td>Government and Public Policy in Taiwan</td>
      <td>[people, government, taiwan, public, law, use,...</td>
      <td>[taiwan, china, article, country, yuan, public...</td>
      <td>[Government and Public Policy in Taiwan, , , ,...</td>
      <td>[people, government, taiwan, public, law, use,...</td>
      <td>[Strict punishment for punishment_Forcing the ...</td>
    </tr>
    <tr>
      <th>1</th>
      <td>0</td>
      <td>2702</td>
      <td>0_school_students_education_high</td>
      <td>Reforms in Taiwanese Education</td>
      <td>[school, students, education, high, teachers, ...</td>
      <td>[school, students, schools, education, taiwan,...</td>
      <td>[Reforms in Taiwanese Education, , , , , , , ,...</td>
      <td>[school, students, education, high, teachers, ...</td>
      <td>[After 12 years of national teaching, college ...</td>
    </tr>
    <tr>
      <th>2</th>
      <td>1</td>
      <td>1947</td>
      <td>1_road_traffic_car_speed</td>
      <td>Road Safety and Traffic Management</td>
      <td>[road, traffic, car, speed, lane, light, drivi...</td>
      <td>[highway, road, vehicle, vehicles, locomotive,...</td>
      <td>[Road Safety and Traffic Management, , , , , ,...</td>
      <td>[road, traffic, car, speed, lane, light, drivi...</td>
      <td>[Please simplify the rules of priority rights ...</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2</td>
      <td>1294</td>
      <td>2_power_nuclear_water_plastic</td>
      <td>Sustainable Energy and Environmental Protection</td>
      <td>[power, nuclear, water, plastic, food, energy,...</td>
      <td>[taiwan, nuclear, energy, environment, power, ...</td>
      <td>[Sustainable Energy and Environmental Protecti...</td>
      <td>[power, nuclear, water, plastic, food, energy,...</td>
      <td>[Ask the government to lead the people to save...</td>
    </tr>
    <tr>
      <th>4</th>
      <td>3</td>
      <td>1149</td>
      <td>3_epidemic_medical_health_insurance</td>
      <td>Taiwan's Healthcare Response to Severe Epidemic</td>
      <td>[epidemic, medical, health, insurance, people,...</td>
      <td>[taiwan, china, patient, medical, country, for...</td>
      <td>[Taiwan's Healthcare Response to Severe Epidem...</td>
      <td>[epidemic, medical, health, insurance, people,...</td>
      <td>[Health Insurance Complete Reform Solutions-Co...</td>
    </tr>
    <tr>
      <th>5</th>
      <td>4</td>
      <td>997</td>
      <td>4_labor_salary_workers_work</td>
      <td>Labor and Overtime Pay in China</td>
      <td>[labor, salary, workers, work, hours, day, ove...</td>
      <td>[overtime, salary, workers, employee, labor, h...</td>
      <td>[Labor and Overtime Pay in China, , , , , , , ...</td>
      <td>[labor, salary, workers, work, hours, day, ove...</td>
      <td>[The time salary of overtime pay is seriously ...</td>
    </tr>
    <tr>
      <th>6</th>
      <td>5</td>
      <td>810</td>
      <td>5_death_criminal_penalty_crime</td>
      <td>Debate over the death penalty in Taiwan</td>
      <td>[death, criminal, penalty, crime, years, sexua...</td>
      <td>[taiwan, sentenced, imprisonment, china, execu...</td>
      <td>[Debate over the death penalty in Taiwan, , , ...</td>
      <td>[death, criminal, penalty, crime, years, sexua...</td>
      <td>[Modify Article 271 of the Criminal Law_Propos...</td>
    </tr>
    <tr>
      <th>7</th>
      <td>6</td>
      <td>743</td>
      <td>6_railway_station_rail_speed</td>
      <td>High-Speed Rail Extension in Pingtung, Taiwan</td>
      <td>[railway, station, rail, speed, line, high, ro...</td>
      <td>[kaohsiung, keelung, taichung, pingtung, zuoyi...</td>
      <td>[High-Speed Rail Extension in Pingtung, Taiwan...</td>
      <td>[railway, station, rail, speed, line, high, ro...</td>
      <td>[The high -speed rail extension Pingtung Zuoyi...</td>
    </tr>
    <tr>
      <th>8</th>
      <td>7</td>
      <td>729</td>
      <td>7_election_voting_political_votes</td>
      <td>Electoral reforms in Taiwan</td>
      <td>[election, voting, political, votes, legislato...</td>
      <td>[elected, election, voters, elections, represe...</td>
      <td>[Electoral reforms in Taiwan, , , , , , , , , ]</td>
      <td>[election, voting, political, votes, legislato...</td>
      <td>[Requires the relevant regulations such as the...</td>
    </tr>
    <tr>
      <th>9</th>
      <td>8</td>
      <td>535</td>
      <td>8_military_service_defense_soldiers</td>
      <td>Gender and Military Service</td>
      <td>[military, service, defense, soldiers, women, ...</td>
      <td>[society, military, equality, army, gender, ch...</td>
      <td>[Gender and Military Service, , , , , , , , , ]</td>
      <td>[military, service, defense, soldiers, women, ...</td>
      <td>[Amending the "Military Service Law" refers to...</td>
    </tr>
    <tr>
      <th>10</th>
      <td>9</td>
      <td>513</td>
      <td>9_china_republic_taiwan_country</td>
      <td>Nationality and Identity in China</td>
      <td>[china, republic, taiwan, country, chinese, ho...</td>
      <td>[taiwan, china, taiwanese, republic, nationali...</td>
      <td>[Nationality and Identity in China, , , , , , ...</td>
      <td>[china, republic, taiwan, country, chinese, ho...</td>
      <td>[The abbreviation of the Republic of China, us...</td>
    </tr>
    <tr>
      <th>11</th>
      <td>10</td>
      <td>461</td>
      <td>10_animals_dogs_animal_pet</td>
      <td>Pet and Stray Animal Management</td>
      <td>[animals, dogs, animal, pet, cats, stray, pets...</td>
      <td>[taiwan, pet, stray, animals, dogs, public, an...</td>
      <td>[Pet and Stray Animal Management, , , , , , , ...</td>
      <td>[animals, dogs, animal, pet, cats, stray, pets...</td>
      <td>[Cats and dogs across the country (including c...</td>
    </tr>
    <tr>
      <th>12</th>
      <td>11</td>
      <td>427</td>
      <td>11_driving_drunk_alcohol_driver</td>
      <td>Drunk Driving Laws and Penalties</td>
      <td>[driving, drunk, alcohol, driver, years, drink...</td>
      <td>[fined, penalty, penalties, offenders, sentenc...</td>
      <td>[Drunk Driving Laws and Penalties, , , , , , ,...</td>
      <td>[driving, drunk, alcohol, driver, years, drink...</td>
      <td>[Increased the liability of alcohol. Drunk dri...</td>
    </tr>
    <tr>
      <th>13</th>
      <td>12</td>
      <td>416</td>
      <td>12_smoke_smoking_cigarettes_cigarette</td>
      <td>Tobacco Control Measures and Smoke Tax</td>
      <td>[smoke, smoking, cigarettes, cigarette, health...</td>
      <td>[tobacco, smokers, taiwan, smoking, cigarettes...</td>
      <td>[Tobacco Control Measures and Smoke Tax, , , ,...</td>
      <td>[smoke, smoking, cigarettes, cigarette, health...</td>
      <td>[Set up a smoking room to encourage people to ...</td>
    </tr>
    <tr>
      <th>14</th>
      <td>13</td>
      <td>360</td>
      <td>13_house_housing_tax_price</td>
      <td>Housing market regulation</td>
      <td>[house, housing, tax, price, land, houses, est...</td>
      <td>[land, housing, property, houses, households, ...</td>
      <td>[Housing market regulation, , , , , , , , , ]</td>
      <td>[house, housing, tax, price, land, houses, est...</td>
      <td>[Treatment of land hoarding to achieve average...</td>
    </tr>
    <tr>
      <th>15</th>
      <td>14</td>
      <td>289</td>
      <td>14_children_child_childcare_parents</td>
      <td>Parenting and Fertility Support in Taiwan</td>
      <td>[children, child, childcare, parents, care, fe...</td>
      <td>[taiwan, salary, increase, rate, income, child...</td>
      <td>[Parenting and Fertility Support in Taiwan, , ...</td>
      <td>[children, child, childcare, parents, care, fe...</td>
      <td>[Take various measures to increase Taiwan's fe...</td>
    </tr>
    <tr>
      <th>16</th>
      <td>15</td>
      <td>236</td>
      <td>15_news_media_information_fake</td>
      <td>Media Ethics and Regulation</td>
      <td>[news, media, information, fake, online, platf...</td>
      <td>[reporters, reporter, media, report, political...</td>
      <td>[Media Ethics and Regulation, , , , , , , , , ]</td>
      <td>[news, media, information, fake, online, platf...</td>
      <td>[Online platform media professional ethics lac...</td>
    </tr>
    <tr>
      <th>17</th>
      <td>16</td>
      <td>223</td>
      <td>16_license_age_driver_test</td>
      <td>Lowering the Age Limit for Obtaining a Motorcy...</td>
      <td>[license, age, driver, test, driving, 16, old,...</td>
      <td>[age, motorcycle, driving, taiwan, license, ro...</td>
      <td>[Lowering the Age Limit for Obtaining a Motorc...</td>
      <td>[license, age, driver, test, driving, 16, old,...</td>
      <td>[Falling the age of driving in the driving mot...</td>
    </tr>
    <tr>
      <th>18</th>
      <td>17</td>
      <td>205</td>
      <td>17_https_www_com_marriage</td>
      <td>Marriage laws and regulations across different...</td>
      <td>[https, www, com, marriage, html, cc, tw, news...</td>
      <td>[四等親, 中國大陸, 紐西蘭, 那你們就不知道優生學是限制到四等親最科學嗎, 如果兩人都為...</td>
      <td>[\nMarriage laws and regulations across differ...</td>
      <td>[https, www, com, marriage, html, cc, tw, news...</td>
      <td>[The civil law stipulates that the six -class ...</td>
    </tr>
    <tr>
      <th>19</th>
      <td>18</td>
      <td>177</td>
      <td>18_tax_yuan_card_payment</td>
      <td>Fiscal policies and taxation</td>
      <td>[tax, yuan, card, payment, 000, banknotes, cre...</td>
      <td>[taiwan, banknote, subsidy, income, yuan, chin...</td>
      <td>[Fiscal policies and taxation, , , , , , , , , ]</td>
      <td>[tax, yuan, card, payment, 000, banknotes, cre...</td>
      <td>[Unified the final end of various payment, ful...</td>
    </tr>
  </tbody>
</table>
</div>




```python
topic_model.get_representative_docs(7)
```




    ['Requires the relevant regulations such as the Central Election Association and the Ministry of the Interior\'s Election of Election and Election and Election and Election and Improve the "Military and Police Conditioning" Transfer Voting System "to protect the right to election for military police_Article 17 of the Constitution: "The people have the right to election, dismissal, creation, and resurgence."\n\xa0 \nArticle 13 of the "Presidential Vice Presidential Election and Removal Law" and Article 17, paragraph 1 of the "Public Officials Election Removal Law" stipulates: "Elementary candidates should vote at the voting of the household registration place in addition to other regulations."\n\xa0 \nArticle 13 of the "Presidential Vice Presidential Election Law" and Article 17 and 2 of the "Public Officials Election Removal Law" stipulate: "The staff of the voting office must vote in a vote in the household registration or place of work. However, the voters of the workplace are limited to the same election area in the same election area and in the same municipalities and counties (cities). "\n\xa0 \nAccording to the 112 -year budget of the Ministry of National Defense: 171,422 of the National Military Officials and Soldiers\n\xa0 \nAccording to the 110 -year statistical report of the Police Department: 74,091 policemen\n\xa0 \nAccording to the 110 -year statistical report of the Fire Department: 15,957 fires\n\xa0 \nA total of 261,470 people in the military and police in the country\n\xa0 \nAlthough the news report clarified that about 5,000 officers and soldiers could not vote in 2022, the Central Election Commission stated in 2018 that police officers who were dispatched as guards who were voted belonged to the staff of the voting office. Evil in the application work place\n\xa0 \nBut if it wasn\'t for the police officer of the voting office? For example, the police officers reported by the public report of the public\n\xa0 \nFirefighting is not a staff member of the voting office, but still needs to be on duty to cope with the sudden fire and rescue\n\xa0 \nThere are currently current staff members who vote for voting to vote for implementation experience. Should the military police apply for a transfer of voting? And if it is true that the number of influences that the Ministry of National Defense and the Police Department have said that the "military police" system is not difficult? \n\xa0 \nArticle 16, (1 of the Presidential Vice Presidential Election Law "and Article 20 of the" Public Response Election Removal Law "averaged the provisions:" The registration information of the household registration has been registered on the 20th day before the voting, and the qualifications of the electoral qualifications are in accordance with regulations. , Will be compiled into the roster. "\n\xa0 \n是否可考量于投票日前2~3个月由中央选举委员会行文国防部、内政部(警政署、消防署)、各县市政府警察局及消防局调查「移转投票」(包含：申请书、 Identity card and service certificate, application for transfer voting location [for example, the invoicing center of the service unit address], etc.), the relevant "transfer voting" details are compared to "national citizen voting is not in the draft voting law". Each service unit gives the affiliated personnel to maintain the minimum service number and go out to vote for 2 to 3 hours\n\xa0 \nThe National Army, Police, Fire Fighting and other personnel adhere to their posts to maintain law and order, but the government\'s administration is lazy, and the right to election for the national army, police, fire protection and other personnel is not seen.\n\xa0 \nThe Ministry of National Defense, the Ministry of the Interior (Police Department, Fire Department) stated: "Thank you brothers of the National Army and the police fire colleagues to adhere to their posts, and be happy to add and improve the" Military and Police "System of" Transfer Voting "to ensure that the national army, police The right to election of firefighters and other personnel! "',
     'Requires the relevant regulations such as the Central Election Association and the Ministry of the Interior\'s Election of Election and Election and Election and Election and Improve the "Military and Police Conditioning" Transfer Voting System "to protect the right to election for military police_Article 17 of the Constitution: "The people have the right to election, dismissal, creation, and resurgence."\n\xa0 \nArticle 13 of the "Presidential Vice Presidential Election and Removal Law" and Article 17, paragraph 1 of the "Public Officials Election Removal Law" stipulates: "Elementary candidates should vote at the voting of the household registration place in addition to other regulations."\n\xa0 \nArticle 13 of the "Presidential Vice Presidential Election Law" and Article 17 and 2 of the "Public Officials Election Removal Law" stipulate: "The staff of the voting office must vote in a vote in the household registration or place of work. However, the voters of the workplace are limited to the same election area in the same election area and in the same municipalities and counties (cities). "\n\xa0 \nAccording to the 112 -year budget of the Ministry of National Defense: 171,422 of the National Military Officials and Soldiers\n\xa0 \nAccording to the 110 -year statistical report of the Police Department: 74,091 policemen\n\xa0 \nAccording to the 110 -year statistical report of the Fire Department: 15,957 fires\n\xa0 \nA total of 261,470 people in the military and police in the country\n\xa0 \nAlthough the news report clarified that about 5,000 officers and soldiers could not vote in 2022, the Central Election Commission stated in 2018 that police officers who were dispatched as guards who were voted belonged to the staff of the voting office. Evil in the application work place\n\xa0 \nBut if it wasn\'t for the police officer of the voting office? For example, the police officers reported by the public report of the public\n\xa0 \nFirefighting is not a staff member of the voting office, but still needs to be on duty to cope with the sudden fire and rescue\n\xa0 \nThere are currently current staff members who vote for voting to vote for implementation experience. Should the military police apply for a transfer of voting? And if it is true that the number of influences that the Ministry of National Defense and the Police Department have said that the "military police" system is not difficult? \n\xa0 \nArticle 16, (1 of the Presidential Vice Presidential Election Law "and Article 20 of the" Public Response Election Removal Law "averaged the provisions:" The registration information of the household registration has been registered on the 20th day before the voting, and the qualifications of the electoral qualifications are in accordance with regulations. , Will be compiled into the roster. "\n\xa0 \n是否可考量于投票日前2~3个月由中央选举委员会行文国防部、内政部(警政署、消防署)、各县市政府警察局及消防局调查「移转投票」(包含：申请书、 Identity card and service certificate, application for transfer voting location [for example, the invoicing center of the service unit address], etc.), the relevant "transfer voting" details are compared to "national citizen voting is not in the draft voting law". Each service unit gives the affiliated personnel to maintain the minimum service number and go out to vote for 2 to 3 hours\n\xa0 \nThe National Army, Police, Fire Fighting and other personnel adhere to their posts to maintain law and order, but the government\'s administration is lazy, and the right to election for the national army, police, fire protection and other personnel is not seen.\n\xa0 \nThe Ministry of National Defense, the Ministry of the Interior (Police Department, Fire Department) stated: "Thank you brothers of the National Army and the police fire colleagues to adhere to their posts, and be happy to add and improve the" Military and Police "System of" Transfer Voting "to ensure that the national army, police The right to election of firefighters and other personnel! "',
     'my country\'s public official elections shall adopt a system of dislocation (protest voting, abandoned votes) system_Two rotten guava, I don\'t know how to choose? \nAlways elected the same person. \nCandidates attacked each other, but people\'s livelihood issues were lost? \n\xa0 \nIn today\'s Taiwanese society, every time in the election is full of smoke, and candidates spray each other, scolded each other, and even discredit or cognitive operations, but they did not focus on the issue of people\'s livelihood and political opinions that should be cared about. Xian and Neng; or relying on the ticket warehouse or the same election, did not take the opinions of the people to heart, anyway, no one can stop me. The blue -green fighting, although the people are disgusted, they are helpless. They can only pick a tears from the two rotten guava, and pray that they can do a little care of the small common people while dividing the stolen people and suppressing the alien. "In this way, one day after day, the vicious followers make many citizens unwilling to go out to vote, and hand over the right to voting in our hands to others, and it will make us farther and farther from the true meaning and value of democracy.\nA small number of people made a different choice from most people at the time of voting -voting the voting (gambling ticket) to express their dissatisfaction with candidates and elections. Unfortunately, under the current election system, waste tickets are invalid votes. In addition to symbolizing the dissatisfaction of some voters, there is no ability to affect the election results. In 2018, the election of Maiyu Township, Yunlin County, was an example. The former head of the township who was re -elected announced the withdrawal on the last day of the registration. The candidate only needs to be elected as the same number of campaign with a total number of human rights. This was considered a private granting and caused a rebound in the villagers. They organized a waste ticket alliance to call for everyone to vote for votes to resist this unfair election. As a result, the candidate won the threshold of 8068 votes at low altitude, but the waste votes were as high as nearly twice as high as twice, setting a new high in the proportion of scrap votes in the history of our elections! Writing a new chapter for Taiwan\'s democracy, but such a feat still cannot prevent the township chief from taking office. \nThis proposal hopes that "unbelievable votes" (names are tentatively determined by the introduction of some countries (Colombia, Mongolia, Peru, Ecuador, etc.), and the names of protesting voting, waste votes, etc.: Voto EN Blanco, It is literally translated as a blank ticket, and Colombia is the most famous, see attachments) to solve the situation of candidate discomfort and unfair election, and make the following settings in Taiwan\'s elections:\nAdded the "Bad Trust" voting option, providing citizens to express objections and have actual election effects, which are different from invalid votes. In addition, this system is only applicable to a single constituency. \n1. No trust votes reach 35%of valid votes, confiscate the deposit of all candidates, and cancel the subsidy for the election campaign fee\n2. If you don\'t trust the votes of 50%of the valid votes, confiscate the deposit and apply for re -election, the candidate candidate for the election can be replaced by the candidate for the non -political party, and the candidate recommended by the non -political party can refund the election.\n3. 65%of the valid votes of no trust ticket, confiscated margin, re -election and depriving candidate\'s campaign qualification for four years\n4. Reconstruction of non -trust tickets must be re -elected. If it overlap with the first item\nIf the votes do not trust the votes after re -election, the re -election will be re -elected for one year and the penalty will be handled by 65%. The non -trust votes do not have the effect when the presidential election re -election, that is, when the non -trusted votes get the highest votes, they are still elected by candidates with the highest votes. \n\xa0 \nSupporting measures:\n1. The Election Council and the Ministry of the Interior should produce relevant publicity and accept the contents of unwilling votes into the national high school citizen course\n2. Taking a blank ticket or a new field (the proposal suggestion to add a new field) as the mark that label the non -trust ticket, re -determine the relevant identification measures to calculate the votes and the supervisor\n(Interest and influence will be attached Q & A)\n\xa0 \nWith the system of non -confidence, no longer vote, forced to choose, no longer stay at home to let others decide their future! Let\'s find the original intention of the democratic system! \n\xa0 \nIf you have any omissions and suggestions, please give me advice! \n\xa0 \n\xa0 \n\xa0 \n\xa0 \n\xa0']




```python
topic_labels = [topic_model.get_topic_info().iloc[i]["Llama2"][0] for i in closest_topic]
```


```python
data = load_dataset(source=source, type="pandas")
data.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>date</th>
      <th>link</th>
      <th>title_zh</th>
      <th>proposal_zh</th>
      <th>利益與影響</th>
      <th>upvotes</th>
      <th>threshold</th>
      <th>提送日期</th>
      <th>關注數量</th>
      <th>留言數量</th>
      <th>googleAnalytics</th>
      <th>提議者</th>
      <th>proposer</th>
      <th>num_followers</th>
      <th>num_comments</th>
      <th>Category</th>
      <th>proposal_en</th>
      <th>title_en</th>
      <th>label</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>2015-09-10 13:26:19</td>
      <td>https://join.gov.tw/idea/detail/25824c17-f141-...</td>
      <td>Join 平台應提供匯出資料供批次下載</td>
      <td>\n目前 Join 平台為方便機關人員作業，在後台有「打包匯出資料」的功能，但前台沒有開放給...</td>
      <td>這是 kiang 在 g0v 提出的想法。\n利益：提供民間備份，並可介接第三方進行全文檢索...</td>
      <td>22</td>
      <td>250</td>
      <td>2015-09-10 17:12:05</td>
      <td>1</td>
      <td>0</td>
      <td>無</td>
      <td>au</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>At present, in order to facilitate the operati...</td>
      <td>Join platform should provide remittance inform...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>2015-09-10 16:08:10</td>
      <td>https://join.gov.tw/idea/detail/75185e90-3a37-...</td>
      <td>你是否贊成推動「十八歲投票權」及「二十歲被選舉權」?</td>
      <td>鑒於國民年滿十六歲即可工作、納稅，\n年滿十八歲就須負完全的刑事責任並有應考試、服公職的權利...</td>
      <td>世代正義是我國民主發展所必須正視的課題，\n若設置過高的年齡門檻形同將年輕世代排除在體制性的...</td>
      <td>0</td>
      <td>0</td>
      <td>2015-09-10 16:11:31</td>
      <td>0</td>
      <td>0</td>
      <td>無</td>
      <td>森里蛍一</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Given that you can work and pay taxes in view ...</td>
      <td>Do you agree to promote the "18 -year -old vot...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>2015-09-10 19:40:31</td>
      <td>https://join.gov.tw/idea/detail/4e658586-2a08-...</td>
      <td>你是否贊成將國家撥給政黨的競選費用補助金門檻由3.5%降為3%，並設置10%的上限?</td>
      <td>雖然之前國家撥給政黨的競選費用補助金門檻從5%下降至3.5%但仍不夠低，\n以國外案例來說德...</td>
      <td>修法調降政黨競選費用補助金門檻有利於小黨發展並可促進多元政黨政治發展，\n稚現行修正後之門檻...</td>
      <td>5</td>
      <td>250</td>
      <td>2015-09-22 00:45:06</td>
      <td>1</td>
      <td>3</td>
      <td>無</td>
      <td>森里蛍一</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Although the threshold for campaign fees for t...</td>
      <td>Do you agree that the threshold for subsidy fo...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>3</th>
      <td>2015-09-10 20:45:11</td>
      <td>https://join.gov.tw/idea/detail/94b5dca9-57fc-...</td>
      <td>都更的建議</td>
      <td>國家既然採多數決.為何總是被少數人綁架.都更常因釘子戶造成困擾.個人建議.國家要發展.這個問...</td>
      <td>NaN</td>
      <td>2</td>
      <td>250</td>
      <td>2015-09-10 20:49:17</td>
      <td>0</td>
      <td>0</td>
      <td>無</td>
      <td>樂與喜</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Since the country picks up the majority. Why i...</td>
      <td>More suggestions</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>2015-09-10 21:40:32</td>
      <td>https://join.gov.tw/idea/detail/3bdab9bf-d874-...</td>
      <td>引進鞭刑</td>
      <td>依先進國家如新加坡的刑法引進鞭刑讓重刑犯，強姦犯等重大罪犯得到應得的逞罰</td>
      <td>促進社會正義，讓正義得以伸張並幫助這些罪犯記取教訓以及促進受害者人權，進而讓國家進步</td>
      <td>184</td>
      <td>250</td>
      <td>2015-09-10 21:42:48</td>
      <td>4</td>
      <td>0</td>
      <td>無</td>
      <td>UFO</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Protecting the punishment of severe criminals ...</td>
      <td>Introduce</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>




```python
data.insert(0, "BERTLabels", topic_labels) 
```


```python
data.head()
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>BERTLabels</th>
      <th>date</th>
      <th>link</th>
      <th>title_zh</th>
      <th>proposal_zh</th>
      <th>利益與影響</th>
      <th>upvotes</th>
      <th>threshold</th>
      <th>提送日期</th>
      <th>關注數量</th>
      <th>留言數量</th>
      <th>googleAnalytics</th>
      <th>提議者</th>
      <th>proposer</th>
      <th>num_followers</th>
      <th>num_comments</th>
      <th>Category</th>
      <th>proposal_en</th>
      <th>title_en</th>
      <th>label</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>Fiscal policies and taxation</td>
      <td>2015-09-10 13:26:19</td>
      <td>https://join.gov.tw/idea/detail/25824c17-f141-...</td>
      <td>Join 平台應提供匯出資料供批次下載</td>
      <td>\n目前 Join 平台為方便機關人員作業，在後台有「打包匯出資料」的功能，但前台沒有開放給...</td>
      <td>這是 kiang 在 g0v 提出的想法。\n利益：提供民間備份，並可介接第三方進行全文檢索...</td>
      <td>22</td>
      <td>250</td>
      <td>2015-09-10 17:12:05</td>
      <td>1</td>
      <td>0</td>
      <td>無</td>
      <td>au</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>At present, in order to facilitate the operati...</td>
      <td>Join platform should provide remittance inform...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>1</th>
      <td>Electoral reforms in Taiwan</td>
      <td>2015-09-10 16:08:10</td>
      <td>https://join.gov.tw/idea/detail/75185e90-3a37-...</td>
      <td>你是否贊成推動「十八歲投票權」及「二十歲被選舉權」?</td>
      <td>鑒於國民年滿十六歲即可工作、納稅，\n年滿十八歲就須負完全的刑事責任並有應考試、服公職的權利...</td>
      <td>世代正義是我國民主發展所必須正視的課題，\n若設置過高的年齡門檻形同將年輕世代排除在體制性的...</td>
      <td>0</td>
      <td>0</td>
      <td>2015-09-10 16:11:31</td>
      <td>0</td>
      <td>0</td>
      <td>無</td>
      <td>森里蛍一</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Given that you can work and pay taxes in view ...</td>
      <td>Do you agree to promote the "18 -year -old vot...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>2</th>
      <td>Electoral reforms in Taiwan</td>
      <td>2015-09-10 19:40:31</td>
      <td>https://join.gov.tw/idea/detail/4e658586-2a08-...</td>
      <td>你是否贊成將國家撥給政黨的競選費用補助金門檻由3.5%降為3%，並設置10%的上限?</td>
      <td>雖然之前國家撥給政黨的競選費用補助金門檻從5%下降至3.5%但仍不夠低，\n以國外案例來說德...</td>
      <td>修法調降政黨競選費用補助金門檻有利於小黨發展並可促進多元政黨政治發展，\n稚現行修正後之門檻...</td>
      <td>5</td>
      <td>250</td>
      <td>2015-09-22 00:45:06</td>
      <td>1</td>
      <td>3</td>
      <td>無</td>
      <td>森里蛍一</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Although the threshold for campaign fees for t...</td>
      <td>Do you agree that the threshold for subsidy fo...</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>3</th>
      <td>Electoral reforms in Taiwan</td>
      <td>2015-09-10 20:45:11</td>
      <td>https://join.gov.tw/idea/detail/94b5dca9-57fc-...</td>
      <td>都更的建議</td>
      <td>國家既然採多數決.為何總是被少數人綁架.都更常因釘子戶造成困擾.個人建議.國家要發展.這個問...</td>
      <td>NaN</td>
      <td>2</td>
      <td>250</td>
      <td>2015-09-10 20:49:17</td>
      <td>0</td>
      <td>0</td>
      <td>無</td>
      <td>樂與喜</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Since the country picks up the majority. Why i...</td>
      <td>More suggestions</td>
      <td>NaN</td>
    </tr>
    <tr>
      <th>4</th>
      <td>Debate over the death penalty in Taiwan</td>
      <td>2015-09-10 21:40:32</td>
      <td>https://join.gov.tw/idea/detail/3bdab9bf-d874-...</td>
      <td>引進鞭刑</td>
      <td>依先進國家如新加坡的刑法引進鞭刑讓重刑犯，強姦犯等重大罪犯得到應得的逞罰</td>
      <td>促進社會正義，讓正義得以伸張並幫助這些罪犯記取教訓以及促進受害者人權，進而讓國家進步</td>
      <td>184</td>
      <td>250</td>
      <td>2015-09-10 21:42:48</td>
      <td>4</td>
      <td>0</td>
      <td>無</td>
      <td>UFO</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>NaN</td>
      <td>Protecting the punishment of severe criminals ...</td>
      <td>Introduce</td>
      <td>NaN</td>
    </tr>
  </tbody>
</table>
</div>




```python
data.to_csv(f"./results/ALLBertLabelsTopicLLama2_{source}_{min_cluster_size}_{UMAP_neighbors}.csv")

```


```python
data.columns
```




    Index(['BERTLabels', 'date', 'link', 'title_zh', 'proposal_zh', '利益與影響',
           'upvotes', 'threshold', '提送日期', '關注數量', '留言數量', 'googleAnalytics',
           '提議者', 'proposer', 'num_followers', 'num_comments', 'Category',
           'proposal_en', 'title_en', 'label'],
          dtype='object')




```python
# filter out passed proposals
a=data[data["upvotes"]>=data["threshold"]]
a = a[a["threshold"]>0]
```


```python
a.to_csv(f"./results/ALLBertLabelsTopicLLama2Passed_{source}_{min_cluster_size}_{UMAP_neighbors}.csv")

```


```python
topic_model.topic_representations_[4]
```




    [('labor', 0.08918409185779914),
     ('salary', 0.058023956883980404),
     ('workers', 0.046413972016147775),
     ('work', 0.038366603734948185),
     ('hours', 0.03732876407394845),
     ('day', 0.03720395321502746),
     ('overtime', 0.027546303191118372),
     ('holiday', 0.026188119374288596),
     ('days', 0.024858060139787492),
     ('working', 0.023709395324130883)]




```python
import numpy as np

#np.argmin(doc*topic_model.topic_embeddings)
np.argmax(embeddings[0]*topic_model.topic_embeddings_)
```




    15265




```python
topic_model.visualize_hierarchy(custom_labels=True)
```




```python
# # find the label according to calculating the min distance between topic_embedding and the doc embedding

# for doc in docs:
#     for top in topic_model.topic_embeddings_:
#         np.argmin(doc*topic_model.topic_embeddings)
```


```python

```


```python
topics_over_time = topic_model.topics_over_time(docs, timestamps, nr_bins=40)
fig = topic_model.visualize_topics_over_time(topics_over_time, top_n_topics=5, custom_labels=True)
fig.update_layout(
    font=dict(
        family="Courier New, monospace",
        size=20  # Set the font size here
    )
)
fig.show()
```

    40it [00:07,  5.06it/s]





```python
# visualize the topics
fig = topic_model.visualize_barchart(n_words=10, custom_labels=True, width=500, height=500)
fig.write_html(f"/media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/results/topicsVis{source}{min_cluster_size}.html")

```


```python
# Extract hierarchical topics and their representations
hierarchical_topics = topic_model.hierarchical_topics(docs)

# Visualize these representations
topic_model.visualize_hierarchy(hierarchical_topics=hierarchical_topics, custom_labels=True)
fig = topic_model.visualize_hierarchy()
fig.write_html(f"/media/citi-ai/moritz/03_UrbanDevelopmentTaiwan/results/topicsHierarchy{source}{min_cluster_size}.html")

```

    100%|██████████| 18/18 [00:00<00:00, 166.66it/s]



```python
topic_model.find_topics("Main")
```




    ([-1, 2, 0, 4, 8], [0.86113745, 0.84853035, 0.8456297, 0.8448113, 0.8445852])




```python
topic_model.get_topic_info()["Llama2"]
```




    0     [Government and Public Policy in Taiwan, , , ,...
    1     [Reforms in Taiwanese Education, , , , , , , ,...
    2     [Road Safety and Traffic Management, , , , , ,...
    3     [Sustainable Energy and Environmental Protecti...
    4     [Taiwan's Healthcare Response to Severe Epidem...
    5     [Labor and Overtime Pay in China, , , , , , , ...
    6     [Debate over the death penalty in Taiwan, , , ...
    7     [High-Speed Rail Extension in Pingtung, Taiwan...
    8       [Electoral reforms in Taiwan, , , , , , , , , ]
    9       [Gender and Military Service, , , , , , , , , ]
    10    [Nationality and Identity in China, , , , , , ...
    11    [Pet and Stray Animal Management, , , , , , , ...
    12    [Drunk Driving Laws and Penalties, , , , , , ,...
    13    [Tobacco Control Measures and Smoke Tax, , , ,...
    14        [Housing market regulation, , , , , , , , , ]
    15    [Parenting and Fertility Support in Taiwan, , ...
    16      [Media Ethics and Regulation, , , , , , , , , ]
    17    [Lowering the Age Limit for Obtaining a Motorc...
    18    [\nMarriage laws and regulations across differ...
    19     [Fiscal policies and taxation, , , , , , , , , ]
    Name: Llama2, dtype: object




```python
topic_model.get_topic_freq().plot.bar(x='Topic', y='Count',)
```




    <Axes: xlabel='Topic'>




    
![png](TopicModelingLlama2_files/TopicModelingLlama2_84_1.png)
    



```python
topics_cluster0 = topic_model.get_topic_info().iloc[1]
```


```python
topics_over_time.iloc[350:400]
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Topic</th>
      <th>Words</th>
      <th>Frequency</th>
      <th>Timestamp</th>
      <th>Name</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>350</th>
      <td>14</td>
      <td>children, mortgage, inspector, fertility, newborn</td>
      <td>3</td>
      <td>2020-02-25 02:04:49.424999936</td>
      <td>Parenting and Fertility Support in Taiwan</td>
    </tr>
    <tr>
      <th>351</th>
      <td>15</td>
      <td>news, television, media, radio, information</td>
      <td>5</td>
      <td>2020-02-25 02:04:49.424999936</td>
      <td>Media Ethics and Regulation</td>
    </tr>
    <tr>
      <th>352</th>
      <td>16</td>
      <td>age, 16, license, test, driver</td>
      <td>4</td>
      <td>2020-02-25 02:04:49.424999936</td>
      <td>Lowering the Age Limit for Obtaining a Motorcy...</td>
    </tr>
    <tr>
      <th>353</th>
      <td>17</td>
      <td>marriage, di, married, relatives, https</td>
      <td>4</td>
      <td>2020-02-25 02:04:49.424999936</td>
      <td>Marriage laws and regulations across different...</td>
    </tr>
    <tr>
      <th>354</th>
      <td>18</td>
      <td>tax, consumer, 000, coupon, card</td>
      <td>6</td>
      <td>2020-02-25 02:04:49.424999936</td>
      <td>Fiscal policies and taxation</td>
    </tr>
    <tr>
      <th>355</th>
      <td>-1</td>
      <td>hall, government, people, taiwan, public</td>
      <td>129</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Government and Public Policy in Taiwan</td>
    </tr>
    <tr>
      <th>356</th>
      <td>0</td>
      <td>education, school, students, experimental, tea...</td>
      <td>29</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Reforms in Taiwanese Education</td>
    </tr>
    <tr>
      <th>357</th>
      <td>1</td>
      <td>traffic, road, speed, lane, car</td>
      <td>40</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Road Safety and Traffic Management</td>
    </tr>
    <tr>
      <th>358</th>
      <td>2</td>
      <td>vegetarian, vegan, food, environmental, taiwan</td>
      <td>22</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Sustainable Energy and Environmental Protection</td>
    </tr>
    <tr>
      <th>359</th>
      <td>3</td>
      <td>medical, health, epidemic, treatment, insurance</td>
      <td>19</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Taiwan's Healthcare Response to Severe Epidemic</td>
    </tr>
    <tr>
      <th>360</th>
      <td>4</td>
      <td>labor, salary, workers, work, age</td>
      <td>14</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Labor and Overtime Pay in China</td>
    </tr>
    <tr>
      <th>361</th>
      <td>5</td>
      <td>criminal, punishment, death, years, law</td>
      <td>14</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Debate over the death penalty in Taiwan</td>
    </tr>
    <tr>
      <th>362</th>
      <td>6</td>
      <td>railway, rail, line, station, speed</td>
      <td>19</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>High-Speed Rail Extension in Pingtung, Taiwan</td>
    </tr>
    <tr>
      <th>363</th>
      <td>7</td>
      <td>election, voting, votes, candidate, candidates</td>
      <td>19</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Electoral reforms in Taiwan</td>
    </tr>
    <tr>
      <th>364</th>
      <td>8</td>
      <td>military, service, men, women, defense</td>
      <td>10</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Gender and Military Service</td>
    </tr>
    <tr>
      <th>365</th>
      <td>9</td>
      <td>china, republic, flag, party, taiwan</td>
      <td>2</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Nationality and Identity in China</td>
    </tr>
    <tr>
      <th>366</th>
      <td>10</td>
      <td>animal, animals, dogs, chip, smuggling</td>
      <td>11</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Pet and Stray Animal Management</td>
    </tr>
    <tr>
      <th>367</th>
      <td>11</td>
      <td>driving, drunk, wine, prevention, alcohol</td>
      <td>4</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Drunk Driving Laws and Penalties</td>
    </tr>
    <tr>
      <th>368</th>
      <td>12</td>
      <td>smoke, smoking, cigarette, cigarettes, tobacco</td>
      <td>8</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Tobacco Control Measures and Smoke Tax</td>
    </tr>
    <tr>
      <th>369</th>
      <td>13</td>
      <td>house, price, estate, real, housing</td>
      <td>19</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Housing market regulation</td>
    </tr>
    <tr>
      <th>370</th>
      <td>14</td>
      <td>children, child, young, childcare, care</td>
      <td>4</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Parenting and Fertility Support in Taiwan</td>
    </tr>
    <tr>
      <th>371</th>
      <td>15</td>
      <td>media, news, parties, communication, public</td>
      <td>5</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Media Ethics and Regulation</td>
    </tr>
    <tr>
      <th>372</th>
      <td>16</td>
      <td>license, driver, motorcycle, age, test</td>
      <td>6</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Lowering the Age Limit for Obtaining a Motorcy...</td>
    </tr>
    <tr>
      <th>373</th>
      <td>17</td>
      <td>marriage, spouse, adultery, compensation, law</td>
      <td>2</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Marriage laws and regulations across different...</td>
    </tr>
    <tr>
      <th>374</th>
      <td>18</td>
      <td>revitalization, yuan, vouchers, voucher, coupons</td>
      <td>9</td>
      <td>2020-05-20 19:10:00.500000000</td>
      <td>Fiscal policies and taxation</td>
    </tr>
    <tr>
      <th>375</th>
      <td>-1</td>
      <td>people, taiwan, government, public, use</td>
      <td>190</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Government and Public Policy in Taiwan</td>
    </tr>
    <tr>
      <th>376</th>
      <td>0</td>
      <td>school, students, education, learning, high</td>
      <td>134</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Reforms in Taiwanese Education</td>
    </tr>
    <tr>
      <th>377</th>
      <td>1</td>
      <td>road, traffic, car, lane, parking</td>
      <td>57</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Road Safety and Traffic Management</td>
    </tr>
    <tr>
      <th>378</th>
      <td>2</td>
      <td>agricultural, meat, food, plastic, lean</td>
      <td>48</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Sustainable Energy and Environmental Protection</td>
    </tr>
    <tr>
      <th>379</th>
      <td>3</td>
      <td>medical, epidemic, insurance, health, cancer</td>
      <td>30</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Taiwan's Healthcare Response to Severe Epidemic</td>
    </tr>
    <tr>
      <th>380</th>
      <td>4</td>
      <td>labor, workers, foreign, holiday, day</td>
      <td>17</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Labor and Overtime Pay in China</td>
    </tr>
    <tr>
      <th>381</th>
      <td>5</td>
      <td>criminal, law, death, crime, mental</td>
      <td>27</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Debate over the death penalty in Taiwan</td>
    </tr>
    <tr>
      <th>382</th>
      <td>6</td>
      <td>railway, station, rail, line, pingtung</td>
      <td>28</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>High-Speed Rail Extension in Pingtung, Taiwan</td>
    </tr>
    <tr>
      <th>383</th>
      <td>7</td>
      <td>election, voting, people, votes, representatives</td>
      <td>10</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Electoral reforms in Taiwan</td>
    </tr>
    <tr>
      <th>384</th>
      <td>8</td>
      <td>military, service, soldiers, women, defense</td>
      <td>22</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Gender and Military Service</td>
    </tr>
    <tr>
      <th>385</th>
      <td>9</td>
      <td>magnesium, taiwan, china, republic, national</td>
      <td>6</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Nationality and Identity in China</td>
    </tr>
    <tr>
      <th>386</th>
      <td>10</td>
      <td>animals, animal, dog, dogs, pet</td>
      <td>11</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Pet and Stray Animal Management</td>
    </tr>
    <tr>
      <th>387</th>
      <td>11</td>
      <td>driving, drunk, alcohol, years, criminal</td>
      <td>9</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Drunk Driving Laws and Penalties</td>
    </tr>
    <tr>
      <th>388</th>
      <td>12</td>
      <td>smoking, smoke, smokers, cigarettes, cigarette</td>
      <td>8</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Tobacco Control Measures and Smoke Tax</td>
    </tr>
    <tr>
      <th>389</th>
      <td>13</td>
      <td>house, housing, price, houses, ping</td>
      <td>23</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Housing market regulation</td>
    </tr>
    <tr>
      <th>390</th>
      <td>14</td>
      <td>children, child, subsidy, parenting, abuse</td>
      <td>4</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Parenting and Fertility Support in Taiwan</td>
    </tr>
    <tr>
      <th>391</th>
      <td>15</td>
      <td>media, news, online, message, speech</td>
      <td>5</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Media Ethics and Regulation</td>
    </tr>
    <tr>
      <th>392</th>
      <td>16</td>
      <td>age, license, 16, driver, old</td>
      <td>17</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Lowering the Age Limit for Obtaining a Motorcy...</td>
    </tr>
    <tr>
      <th>393</th>
      <td>17</td>
      <td>marriage, parties, laws, mother, https</td>
      <td>8</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Marriage laws and regulations across different...</td>
    </tr>
    <tr>
      <th>394</th>
      <td>18</td>
      <td>hospitals, stock, transactions, tax, traders</td>
      <td>3</td>
      <td>2020-08-14 12:15:11.575000064</td>
      <td>Fiscal policies and taxation</td>
    </tr>
    <tr>
      <th>395</th>
      <td>-1</td>
      <td>people, public, government, taiwan, law</td>
      <td>213</td>
      <td>2020-11-08 05:20:22.649999872</td>
      <td>Government and Public Policy in Taiwan</td>
    </tr>
    <tr>
      <th>396</th>
      <td>0</td>
      <td>students, school, education, class, time</td>
      <td>160</td>
      <td>2020-11-08 05:20:22.649999872</td>
      <td>Reforms in Taiwanese Education</td>
    </tr>
    <tr>
      <th>397</th>
      <td>1</td>
      <td>road, traffic, left, car, turn</td>
      <td>84</td>
      <td>2020-11-08 05:20:22.649999872</td>
      <td>Road Safety and Traffic Management</td>
    </tr>
    <tr>
      <th>398</th>
      <td>2</td>
      <td>food, pork, 中華電信, environmental, eat</td>
      <td>54</td>
      <td>2020-11-08 05:20:22.649999872</td>
      <td>Sustainable Energy and Environmental Protection</td>
    </tr>
    <tr>
      <th>399</th>
      <td>3</td>
      <td>epidemic, medical, prevention, health, people</td>
      <td>69</td>
      <td>2020-11-08 05:20:22.649999872</td>
      <td>Taiwan's Healthcare Response to Severe Epidemic</td>
    </tr>
  </tbody>
</table>
</div>




```python

```


```python

```


```python

```
