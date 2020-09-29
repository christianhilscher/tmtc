import numpy as np
import pandas as pd
import os
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource

output_notebook()

#set up working directory
wd_lc = "/Users/llccf/OneDrive/Dokumente/tmtc/"
os.chdir(wd_lc)

def get_first(number, first = 4):
    first = float(str(number)[:first])
    return(first)

#!#####################
#! MISSINGS INQUIRY
#!#####################

#*########
#! DATA
#*########
"""
#number of obs.: 269800
#ids matched to single firm_num
firm_to00 = pd.read_csv("data/tables_to2000/firm_to00.csv")
firm_to89 = pd.read_csv("data/tables_to2000/firm_to89.csv")
firm = firm_to89.append(firm_to00)

#firm_num matched to single id's
#number of obs.: 38646
match_to00 = pd.read_csv("data/tables_to2000/match_to00.csv")
match_to89 = pd.read_csv("data/tables_to2000/match_to89.csv")
match = match_to89.append(match_to00)
#!but apparently not the same

#number of obs.: 223442
pair_to00 = pd.read_csv("data/tables_to2000/pair_to00.csv")
pair_to89 = pd.read_csv("data/tables_to2000/pair_to89.csv")
pair = pair_to89.append(pair_to00)

#number of obs.: 269800
name_to00 = pd.read_csv("data/tables_to2000/name_to00.csv")
name_to89 = pd.read_csv("data/tables_to2000/name_to89.csv")
name = name_to89.append(name_to00)

#number of obs.: 1986871
grant_match_to89 = pd.read_csv("data/tables_to2000/grant_match_to89.csv")
grant_match_to00 = pd.read_csv("data/tables_to2000/grant_match_to00.csv")
grant_match = grant_match_to89.append(grant_match_to00)
"""

#below of most interest
#number of obs.: 1986871
grant_firm = pd.read_csv("data/grant_firm.csv")

#number of obs.: 2436225
grant_grant = pd.read_csv("data/grant_grant.csv")

#number of obs.: 19581061
grant_cite = pd.read_csv("data/grant_cite.csv")

#Patentsview
pv = pd.read_csv("data/patentsview/rawassignee.tsv", sep = "\t")
cits = pd.read_csv("data/patentsview/uspatentcitation.tsv", sep = "\t")
cits["year"] =  cits["date"].apply(get_first)
cits_red = cits[cits["year"] < 2001]
otherref = pd.read_csv("data/patentsview/otherreference.tsv", sep = "\t")

#*########
#! NUMBER OF PATENTS
#*########

#*how many unique patents exist?
#main file -> grant_grant
pats = grant_grant["patnum"].drop_duplicates(keep = "first")
no_pats = len(pats) #2436218

#citations
#how many unique patents in src?
pats_cite = grant_cite["src"].drop_duplicates(keep = "first")
no_pats_cite = len(pats_cite) #2,375,231
#how many unique patents in dst?
pats_cited = grant_cite["dst"].drop_duplicates(keep = "first")
no_pats_cited = len(pats_cited) #3,651,557
#how many unique patents in src and dst combined?
pats_cit = pats_cite.append(pats_cited).drop_duplicates(keep = "first")
no_pats_cit = len(pats_cit) #4,251,496

#firm_num - patnum allocation
pats_firmnum = grant_firm["patnum"].drop_duplicates(keep = "first")
no_pats_firmnum = len(pats_firmnum) #1,986,866

"""
Summary:
    - cannot (!) have information on all patents that are contained
    in citation info df; we have info on ~2.4 million patents, while
    citations in total contain ~4.2 million patents overall (unique)

    - a firm_num is only matched to ~1.9 million patents,
    hence additionally ~500k patents are missing when matching firm_num
    to patent -> why? WHAT IS FIRM_NUM EXACTLY?

    -next up: what is the larger source of discrepancy between citation
    patents and info patents? src or dst?
"""

#*########
#! MISSINGS PER CATEGORY (SRC AND DST)
#*########

#*get an owner list
owner = grant_grant[["patnum", "owner"]]
owner = owner.drop_duplicates(keep = "first") #5 duplicates exist

#*info missing on src
#check how many of the UNIQUE src patents have no matched owner
src = pd.DataFrame(grant_cite["src"].drop_duplicates())
src_owner = src.merge(owner, left_on = "src", right_on = "patnum", how = "outer")

"""
-> use outer join such that I keep
    - pats that are not src but in main
    - pats that are in src but not in main
Now, look for
    1. src - patnum matched, owner NaN (src_1)
    2. src NaN, patnum exists (src_2)
    3. src exists, patnum NaN (src_3)
"""
src_1 = src_owner[src_owner["src"] == src_owner["patnum"]]
#how many matched pats do not have an owner?
src_1_miss = src_1["owner"].isnull().sum() #442,990

src_2 = src_owner[(src_owner["src"].isnull()) & (src_owner["patnum"].isnull() == False)]
#how many pats are mentioned in main but not in src?
src_2_miss = len(src_2) #60,987

src_3 = src_owner[(src_owner["src"].isnull() == False) & (src_owner["patnum"].isnull())]
#how many pats are mentioned in src but not in main?
src_3_miss = len(src_3) #0 !

#*info missing on dst
dst = pd.DataFrame(grant_cite["dst"].drop_duplicates())
dst_owner = dst.merge(owner, left_on = "dst", right_on = "patnum", how = "outer")
"""
-> use outer join such that I keep
    - pats that are not dst but in main
    - pats that are in dst but not in main
Now, look for
    1. dst - patnum matched, owner NaN (dst_1)
    2. dst NaN, patnum exists (dst_2)
    3. dst exists, patnum NaN (dst_3)
"""
dst_1 = dst_owner[dst_owner["dst"] == dst_owner["patnum"]]
#how many matched pats do not have an owner?
dst_1_miss = dst_1["owner"].isnull().sum() #333,617

dst_2 = dst_owner[(dst_owner["dst"].isnull()) & (dst_owner["patnum"].isnull() == False)]
#how many pats are mentioned in main but not in dst?
dst_2_miss = len(dst_2) #627,735

dst_3 = dst_owner[(dst_owner["dst"].isnull() == False) & (dst_owner["patnum"].isnull())]
#how many pats are mentioned in dst but not in main?
dst_3_miss = len(dst_3) # 1,843,072!

#*########
#! SHARES OF MISSINGS
#*########

"""
- have number of missings in each relevant combination now
for src and dst alone, what about combined?
"""

src_dst = pd.DataFrame(src["src"].append(dst["dst"]).drop_duplicates()).rename(columns = {0: "pat"})
src_dst["dst"] = src_dst["pat"].isin(dst["dst"])
src_dst["src"] = src_dst["pat"].isin(src["src"])

src_dst_owner = src_dst.merge(owner, left_on = "pat", right_on = "patnum", how = "left", indicator = True)
tot = src_dst_owner

"""
Now want to find out:
    1. how many "pat" have no match?
    2. how many "pat" and src == True & dst == False have no match? What is share?
    3. how many "pat" and dst == True & src == False have no match? What is share?
    4. how many "pat" and dst == True & src == True have no match? What is share?
    5. how many owners of "pat" that are matched are missing?
    6. how many owners of "pat" and src == True & dst == False that are matched are missing? What is share?
    7. how many owners of "pat" and dst == True & src == False that are matched are missing? What is share?
    8. how many "pat" and dst == True & src == True have no match? What is share?
"""

#*1.
pat_1 = tot[tot["_merge"] == "left_only"]
#*A: 1,843,073

#*2.
pat_2 = pat_1[(pat_1["src"] == True) & (pat_1["dst"] == False)]
#*A: 0; 0%

#*3.
pat_3 = pat_1[(pat_1["dst"] == True) & (pat_1["src"] == False)]
#*A: 1,843,073; 100%

#*4.
pat_4 = pat_1[(pat_1["dst"] == True) & (pat_1["src"] == True)]
#*A: there is noverlap in these

#*5.
both = tot[tot["_merge"] == "both"]
pat_5 = both["owner"].isnull().sum()
#*A: 446,103

#*6.
both_src = both[(both["src"] == True) & (both["dst"] == False)]
pat_6 = both_src["owner"].isnull().sum()
share_6 = pat_6/pat_5
#*A: 112,486; 25.22%

#*7.
both_dst = both[(both["src"] == False) & (both["dst"] == True)]
pat_7 = both_dst["owner"].isnull().sum()
share_7 = pat_7/pat_5
#*A: 3113; 0.698%

#*8.
both_srcdst = both[(both["src"] == True) & (both["dst"] == True)]
pat_8 = both_srcdst["owner"].isnull().sum()
share_8 = pat_8/pat_5
#*A: 330504; 74.01%

"""
Summary:
    - not matched patents are ONLY contained in dst, not in src
    - i.e. missing info on dst, not on src
    - missing owners are mostly of patents which are both, src and dst
        - this is quite bad for us since we are interested in patents that are both/firms that own both
"""

#*########
#! PATENTSVIEW DATA
#*########

#* USING RAWASSIGNEE DATASET
#merge unique firm names from patent parser with unique firm names
#from patentsview
firms_parser = owner["owner"].dropna().tolist()
firms_parser = list(dict.fromkeys(firms_parser))
firms_parser = pd.DataFrame(firms_parser).rename(columns = {0: "firms"})
firms_parser["firms"] = firms_parser["firms"].str.lower()
firms_pv = pv["organization"].dropna().tolist()
firms_pv = list(dict.fromkeys(firms_pv))
firms_pv = pd.DataFrame(firms_pv).rename(columns = {0: "firms"})
firms_pv = pd.DataFrame(firms_pv["firms"].str.lower())

#check which firms are matched, which firms are only parser df and which ones only in patentsview
firms_match = firms_parser.merge(firms_pv, left_on = "firms", right_on = "firms", how = "outer", indicator = True)
both = firms_match[firms_match["_merge"] == "both"].reset_index()
parser = firms_match[firms_match["_merge"] == "left_only"].reset_index()
pv = firms_match[firms_match["_merge"] == "right_only"].reset_index()

both_share = len(both)/len(firms_match)
parser_share = len(parser)/len(firms_match)
pv_share = len(pv)/len(firms_match)
shares = [both_share, parser_share, pv_share]
x = [1, 2, 3]
ticks = {1: "both", 2: "Parser", 3: "Patentsview"}

#* PLOT
plot = figure(plot_width = 500, plot_height = 500,
            title = "Share of firm matches; total number of firms: 742518",
            x_axis_label = "Datasource", y_axis_label = "Percentage")
plot.vbar(x = x, top = shares, width = 0.9)
plot.xaxis.ticker = list(ticks.keys())
plot.xaxis.major_label_overrides = ticks
plot.xaxis.major_label_orientation = 0.8
show(plot)
export_png(plot, filename = "output/tmp/match_pv.png")

#* HOW MANY OF MISSINGS IN PARSER ARE MATCHED NOW
pv_pats = pv[["patent_id", "organization"]]
pv_pats = pv_pats.drop_duplicates(subset = ["patent_id"], keep = "first")
dst_missings = pat_3[["pat"]]
match_missings = dst_missings.merge(pv_pats, left_on = "pat", right_on = "patent_id", how = "outer", indicator = True)

"""
Only 474 patents added, strongly suggesting that the missing citations
are indeed data from other patent systems or non-patent citations.
"""

#* Otherref dataset
ref_pats = otherref["patent_id"].drop_duplicates(keep = "first")
dst_missings = pat_3[["pat"]]
matched = dst_missings.merge(ref_pats, left_on = "pat", right_on = "patent_id", how = "outer", indicator = True)

#*matching total src_dst with patentsview data
matched = src_dst.merge(pv_pats, left_on = "pat", right_on = "patent_id", how = "outer", indicator = True)
matched[matched["_merge"] == "both"]


#*########
#! MISSINGS BY YEAR
#*########
owner_year = grant_grant[["owner", "patnum", "pubdate"]]
owner_year["year"] = owner_year["pubdate"].apply(get_first)




#*########
#! PLOTS
#*########
from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
output_notebook()

categories = ["owners"]
shares = ["src", "src & dst", "dst"]
colors = ["#c9d9d3", "#718dbf", "#e84d60"]

both_data = {"categories" : categories, "src" : [share_6*100], "src & dst" : [share_8*100], "dst" : [share_7*100]}
source = ColumnDataSource(both_data)

fig = figure(x_range = categories, plot_height = 250, title = "Missings", toolbar_location = None)
fig.vbar_stack(shares, x = "categories", width = 0.5, source = source, color = ["green", "blue", "red"],
            legend_label = shares)

fig.y_range.start = 0
fig.x_range.range_padding = 0.1
fig.xgrid.grid_line_color = None
fig.axis.minor_tick_line_color = None
fig.outline_line_color = None
fig.legend.location = "top_right"
fig.legend.orientation = "vertical"

show(fig)

sum_data = {"Patents": [no_pats_cite, no_pats_cited, no_pats_cit],
                "Missings SRC": [src_1_miss, src_2_miss, src_3_miss],
                "Missings DST": [dst_1_miss, dst_2_miss, dst_3_miss],
                "Missing owners shares": [share_6 * 100, share_7 * 100, share_8 * 100]}
summary_df = pd.DataFrame(data = sum_data)

##############
#Patents claim research dataset
#############

claims1 = pd.read_csv("data/patentclaims_pt1.csv", sep = ";", header = 0)
claims2 = pd.read_csv("data/patentclaims_pt2.csv", sep = ";", header = None)
claims2 = claims2.rename(columns = {0: "pat_no", 1: "claim_no", 2: "claim_txt", 3: "dependencies", 4: "ind_flg", 5: "appl_id"})
claims1 = claims1.drop("appl_id", axis = 1)
claims = claims1.append(claims2)

claims_pat = pd.DataFrame(claims["pat_no"].drop_duplicates())
claims_pat["pat_no"] = claims_pat["pat_no"].astype(str)
pats = pd.DataFrame(grant_grant["patnum"].drop_duplicates())

merged_claims = pats.merge(claims_pat, left_on = "patnum", right_on = "pat_no", how = "inner")

share = len(merged_claims)/len(pats)
