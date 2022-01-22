import os
import pandas as pd 

#set directory to current wd 
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

"""
goal today: 
- implement tf-idf 
-what do I want: 
    - for each edge in our network we want to calculate the tf-idf 
        of the claim texts of the nodes on each side of the edge 
- first: merge claim texts and the nodes we have such that claims dataset is reduced to smaller size 
"""

#import data for testing 
cits = pd.read_csv("data/df3 3.csv")
claims = pd.read_csv("data/patent_claims_fulltext.csv", encoding = "latin1")
claims.head()
pats = pd.DataFrame(cits["src"].append(cits["dst"]).drop_duplicates(), columns = ["pats"]).reset_index(drop = True)
pats_claims = claims.merge(pats, left_on = "pat_no", right_on = "pats")
pats_claims_group = pats_claims[["pat_no", "claim_txt"]]
pats_claims_group["claim_txt"] = pats_claims_group["claim_txt"].astype(str)
pats_claims_group.to_csv("data/patent_claims_matched.csv")
pats_claimsjoined = pats_claims_group.groupby("pat_no").transform(lambda x: ";".join(x))
pats_claimsjoined = pats_claimsjoined.drop_duplicates()
pats_claimsjoined.to_csv("data/patent_claims_merged.csv")

claims = pd.read_csv("data/patent_claims_merged.csv")
claims2 = pd.read_csv("data/patent_claims_matched.csv")
claims2 = claims2[["Unnamed: 0", "pat_no"]]
claims2.head()
claims = claims.merge(claims2, left_on = "Unnamed: 0", right_on = "Unnamed: 0")
claims.to_csv("data/claimtexts_withpatnos.csv")
