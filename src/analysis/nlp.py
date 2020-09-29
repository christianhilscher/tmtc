import os
import pandas as pd 
import nltk as nlp 
from sklearn.feature_extraction.text import TfidfVectorizer 

#set directory to current wd 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

#import data for testing 
cits = pd.read_csv("data/df3 3.csv")
