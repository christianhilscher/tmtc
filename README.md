# tmtc

Project on counting and analysing patent thickets and their economic effects. Data is taken from USPTO using patent parser by Doug Henley. For now, includes all US  granted patents from 1976 - 2000. 

Thickets are measured using the network analysis approach presented in Fischer \& Ringler (2015) when it comes to unweighted edges. For weighted edges approach is based on DeGrazia et al. (2020). Definition of a triple - and, hence, a patent blocking situation - is based on von Graevenitz et al. (2011) for all cases.

## Steps 
* Use Patent Parser by Douglas Haney (https://github.com/iamlemec/patents) to parse patent data into csv files
* Merge industrial codes to ipcs standards 
* Following Fischer \& Ringler (2015) identify each triangle in the citations between firms as blocking relationship - aka a patent thicket
* Use NLP algorithm for checking similarity between patent claims. These are then used as weights when counting the triangles - approach taken from deGrazia et al. (2020)