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

# RQ

* wie effizieint/hilfreich ist die e-participation platform in Taiwan (IVOTE, JOIN)
* Zeitrahmen, wie hat sich politisch Entwicklung auf E-Platformen ausgewirkt? Korreliert?
* gibt es diese bestimmte personen groesseren Einfluss's auf der Plattform?


eventuell in Diskussion
* wie clustert man sowas hilfreich? --> Bias der Methode ?
* wie sind die Ergebnisse unterschiedlich von der Uebersetzung? Was sind die Artefakte von Uebersetzung? --> Bias der Methode ?

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
* evaluate the topic coherence [^2]

## Todos
- [x] DEA --> 1st draft
- [] embedd the text into embedding space --> done
- [x] find clusters for the embeddings
- [] are other embeddings better?
- [] get some feedback and see where we can go
- [] labels for the dataset
- [] use translations of the text to be able to verify the results
- [] Sankey diagram
- [x] refine stopwords for english
- [] compare english and chinese
- [] create groundtruth 
- [] implement a labeling pipeline with LLM models
- [x] implement the nice visualization with terms and intertopic distance
- [] implement the word cloud for the given topics
- [] tune this notebook with a few more tricks from the source
- [] is there a difference between using abstracts and titles
- [] tryout the method that Chad used, e.g. using text embeddings, kmeans, clustering, cosine similarity
- [] compare the topics created in chinese and english
- [] checkout kaggle approaches https://www.kaggle.com/datasets/allen-institute-for-ai/CORD-19-research-challenge
- [x] do the analysis again with the just translated csv (...2)
- [] cluster the subgroups
- [] nicht informative woerter raus--> funktioniert nicht mit dem set, nation ist immer noch drin
- [] sind die subgruppen vom Verkehr in den passed proposals dabei
- [] flow-diagram vom Prozess (Datenanalyse und allgemein)
- [] sind die outcomes in uebersetzung wie outcomes vom englischen
- [] gibt es bestimmte meinungstraeger? Welche Leute sind denn besonders aktiv?
- [x] tfidf-bow methode ausprobieren
- [] woerter rausfiltern, stopwords
- [] wie kann man artefakte darstellen? Aehnlich wie IKON
- [] fuzzy approach
- [] can we find pedestrian hell by looking at proposals to pedestrians in 2018?
- [] alle proposals angucken (JOIN + IVOTE), welche Themen sind am meisten thematisiert?
- [] Klassifizierung 0-Shot - ERNIE 


## Research Questions

* How do translations change embeddings?


## Demand


## Paper Abgabe

The paper is due on 1st July for the icdm.


## Time frame

## Frameworks used

* pyLDAvis [^3] for topic visualization


## Sources 

* The performance of BERT as data representation of text clustering, Subaki et al.
* [Medium Article](https://towardsdatascience.com/a-friendly-introduction-to-text-clustering-fa996bcefd04)
* [Latent semantic Analysis](https://en.wikipedia.org/wiki/Latent_semantic_analysis)
* [Python LSA](https://www.datacamp.com/tutorial/discovering-hidden-topics-python)
* [LDA](https://towardsdatascience.com/a-friendly-introduction-to-text-clustering-fa996bcefd04)
* [^1] Lapesa, Gabriella, et al. "Analysis of Political Debates through Newspaper Reports: Methods and Outcomes." Datenbank-Spektrum 20 (2020): 143-153.
* [^2] http://svn.aksw.org/papers/2015/WSDM_Topic_Evaluation/public.pdf
* https://notebook.community/bmabey/pyLDAvis/notebooks/pyLDAvis_overview
* pyLDAvis [^3] for topic visualization
* https://colab.research.google.com/drive/1naHywtKY1QUClKTXIOhjFLv0rUheHH4c?usp=sharing#scrollTo=CteSym6g1IgN
* Research on CORD-19 dataset: https://namyalg.medium.com/how-many-topics-4b1095510d0e







