import time
from nltk import text
import pandas as pd 
import nltk
from pandas.io.parsers import TextParser 
from sklearn.feature_extraction.text import TfidfVectorizer 
import os 
nltk.download('stopwords')

wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#!read in data 
claims = pd.read_csv("data/claimtexts_withpatnos.csv").drop(["Unnamed: 0", "Unnamed: 0.1"], axis = 1)
cits = pd.read_csv("data/df3 3.csv")
#triads = pd.read_csv("data/triads_lists.csv")

#!implement tf-idf between two patents 
#*first: get two patents that have a link -> lets just use the first one 
cit_example = cits.iloc[0, :]
#*get the two patents we want to compare
src = cit_example["src"]
dst = cit_example["dst"]
#*get claimtexts
claim_src = claims["claim_txt"][claims["pat_no"] == src][740]
claim_dst = claims["claim_txt"][claims["pat_no"] == dst][37126]

from nltk.tokenize import word_tokenize
from string import punctuation
from nltk.corpus import stopwords
from sklearn.metrics.pairwise import cosine_similarity
import string

def tokenizer(text, puncts = list(string.punctuation), stop = stopwords.words('english')): 
    '''
    Return a tokenized list having removed 
        - digits 
        - punctuation 
        - uppercase 
    '''
    tokens = word_tokenize(text)
    tokens = [i for i in tokens if i not in puncts]
    tokens = [i for i in tokens if not (i.isdigit())]
    tokens = [i for i in tokens if i not in stop]
    tokens = [i.lower() for i in tokens]
    return(tokens)

def get_tfidf(texts = [text1, text2], tokenizer = None, idf = False):
    vectorizer = TfidfVectorizer(use_idf = idf, tokenizer = tokenizer, lowercase = True, smooth_idf = False)
    response = vectorizer.fit(texts)
    response = response.transform(texts)
    names = vectorizer.get_feature_names()
    return(response, names)

def get_cossim(tfidfresp): 
    arr1 = tfidfresp[0].toarray()
    arr2 = tfidfresp[1].toarray()
    cossim = cosine_similarity(arr1, arr2)
    return(cossim)

def get_weights(texts): 
    resp = get_tfidf(texts)
    weight = get_cossim(resp)
    return(weight)

testdf = cits.iloc[0:100, 0:2]
testdf = testdf.merge(claims, left_on = "src", right_on = "pat_no").rename(columns = {"claim_txt": "claim_src"})
testdf = testdf.merge(claims, left_on = "dst", right_on = "pat_no").rename(columns = {"claim_txt": "claim_dst"})
testdf = testdf.drop(["pat_no_x", "pat_no_y"], axis = 1)
weights = []
tick = time.time()
for x, y in zip(testdf["claim_src"], testdf["claim_dst"]): 
    texts = [x, y]
    weights.append(get_weights(texts))
tock = time.time() 
timing = tock - tick 
print(timing)

#playing around
results = get_tfidf([claim_src, claim_dst])
len(results.toarray()[0])
len(claim_src.split())
testdf["weights"] = weights
claim_src = testdf.loc[0, "claim_src"]
claim_dst = testdf.loc[0, "claim_dst"]
resultstab = testdf.drop(["claim_src", "claim_dst"], axis = 1)
resultstab[0:10]

text1 = "To be or not to be."
text2 = "To become or not to become"
results, names = get_tfidf([text1, text2])
results[0].toarray()
results[1].toarray()

from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer(lowercase = True)
termfrequency = vectorizer.fit_transform([claim_src, claim_dst])
summed = termfrequency[0].toarray().sum()
single = termfrequency[0].todense()
vectorizer.get_feature_names()
tf = single/summed
