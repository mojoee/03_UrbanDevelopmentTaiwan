from transformers import pipeline

task = "zero-shot-classification"
model = "facebook/bart-large-mnli"
classifier = pipeline(task, model)


text_travel = "Let's book a flight to the Bali"
text_work = "I have to code late tonight on the new sofware update" 
labels = ["travel", "work"]

result_travel = classifier(text_travel, labels)
print(result_travel)