# tmtc

Project for analysing the effect of patent thickets. Data is taken from the UPSTO and for now includes all patents in the US from 1976-2000. 

The relationship between the citations is analysed with a network analysis approach based. 

## First steps

* Following Fischer \& Ringler (2015) and identify each triangle in the citations between firms as blocking relationship
* Use NLP algorithm for checking similarity between patent claims. These are then used as weights when counting the triangles - approach taken from deGrazia et al. (2020)
