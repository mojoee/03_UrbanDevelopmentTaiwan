# JOIN

## Datsets
scraped data from JOIN, IVoting

## Definitions

Deliberation Platforms: E-Petition

## Results during analysis

* DBSCAN could not find any clusters, only noise. Might be due to high dimensionality of the data


## Paper

* assessing the e-petitioning 
* how many proposals did make it through?
* talk to what responsibles did

## Questions about dataset

* difference between submission and publication date
* how does the threshold get determined?
* What does a threshold of 0 mean?
* How many travel-related proposals did make it?

## Questions for DEA

* How did the pariticpation change over the years?
* Did the semantics change over time ? From car to bike?
* Can we relocate similar Proposals? Grenzwert? Embedding Space?
* Filter the transport issues from JOIN
* Was waren denn die TOP 10 in JOIN?
* Deutschen Fussballplatz? Sport anliegen?
* What categories are adressed? Clusters?
* How are the differences between JOIN and IVOTE?
* What are the general topics that the both platofrms contain?
* Welche Proposals haben ein Bezug zu den Subcategories/Topics? Wie viele Proposals per Subcategory?
* was interessiert die Bevoelkerung? Meinungsbild
* wer hat es denn geschafft?
* Was ist aus dem Fussballfelder Thema geworden?
* Should we translate the examples to english to better understand everything? Similar to German to English translations used in [^1]


## Method
* explore data with pandas
* embedd the proposals with ChatGPT

## Todos
* DEA --> 1st draft
* embedd the text into embedding space --> done
* find clusters for the embeddings
* are other embeddings better?
* get some feedback and see where we can go
* labels for the dataset
* use translations of the text to be able to verify the results
* Sankey diagram
* refine stopwords for english
* compare english and chinese
* create groundtruth 
* implement a labeling pipeline with LLM models

## Research Questions

* How do translations change embeddings?


## Demand


## Paper Abgabe

The paper is due on 1st July for the icdm.


## Time frame


## Sources 

* The performance of BERT as data representation of text clustering, Subaki et al.
* [Medium Article](https://towardsdatascience.com/a-friendly-introduction-to-text-clustering-fa996bcefd04)
* [Latent semantic Analysis](https://en.wikipedia.org/wiki/Latent_semantic_analysis)
* [Python LSA](https://www.datacamp.com/tutorial/discovering-hidden-topics-python)
* [LDA](https://towardsdatascience.com/a-friendly-introduction-to-text-clustering-fa996bcefd04)
* [^1] Lapesa, Gabriella, et al. "Analysis of Political Debates through Newspaper Reports: Methods and Outcomes." Datenbank-Spektrum 20 (2020): 143-153.



