import matplotlib

counts = [4126, 3219, 1747, 890, 727, 672, 500, 498, 476, 369, 281, 240, 187, 187]
names = ["Government Policies and Regulations", 
         "Traffic Safety Regulations", 
         "Education Policies in Taiwan",
         "Labor Rights and Regulations in Taiwan",
         "Government Response to Covid-19 Epidemic",
         "Energy Transition and Sustainable Development",
         "Housing Market Regulation",
         "Criminal Justice Reform",
         "Political Status of Taiwan and its relation to China",
         "Electoral Reform",
         "Animal Welfare and Protection Policies",
         "Tobacco Control and Smoking Regulations",
         "Media Regulation and False Information Online", 
         "Gender and Military Service"]


import matplotlib.pyplot as plt 
 
  
  
fig = plt.figure(figsize = (10, 5))
 
# creating the bar plot
plt.bar(names, counts, color ='pink', 
        width = 0.4)

plt.xticks(rotation=90)
plt.ylabel("No. of Proposals")
plt.title("Cluster Sizes in JOIN Dataset")
plt.savefig("./results/BarJOIN.png", bbox_inches='tight')