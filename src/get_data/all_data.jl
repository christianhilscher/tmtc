using Pkg
using CSV, DataFrames
using PyCall
using Levenshtein

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")

cd(data_path)
assignee = CSV.read("assignee.tsv")
raw_assignee = CSV.read("rawassignee.tsv")
patents = CSV.read("patent.tsv")

println(names(patents))
println(names(assignee))
println(names(raw_assignee))

df = leftjoin(assignee, raw_assignee, on = :id => :assignee_id, makeunique=true)


println(names(df))

py"""
import re

#
# weak name standardization
#

# regular expression substitutions
paren = r'\'s|\(.*\)|\.'
punct = r'[^\w\s]'
space = r'[ ]{2,}'

paren_re = re.compile(paren)
punct_re = re.compile(punct)
space_re = re.compile(space)

# standardize firm name
def standardize_weak(name):
    name = name.lower()
    name = paren_re.sub(' ', name)
    name = punct_re.sub(' ', name)
    name = space_re.sub(' ', name)
    return name.strip()

#
# strong name standardization
#

# whitespace
white0 = r' +'
white0_re = re.compile(white0)

# postscripts
post0 = r'(\ba corp.|;|,).*$'
post0_re = re.compile(post0)

# acronyms
acronym1 = r'\b(\w) (\w) (\w)\b'
acronym1_re = re.compile(acronym1)
acronym2 = r'\b(\w) (\w)\b'
acronym2_re = re.compile(acronym2)
acronym3 = r'\b(\w)-(\w)-(\w)\b'
acronym3_re = re.compile(acronym3)
acronym4 = r'\b(\w)-(\w)\b'
acronym4_re = re.compile(acronym4)
acronym5 = r'\b(\w\w)&(\w)\b'
acronym5_re = re.compile(acronym5)
acronym6 = r'\b(\w)&(\w)\b'
acronym6_re = re.compile(acronym6)
acronym7 = r'\b(\w) & (\w)\b'
acronym7_re = re.compile(acronym7)

# punctuation
punct0 = r'\'s|\(.*\)|\.'
punct1 = r'[^\w\s]'
punct0_re = re.compile(punct0)
punct1_re = re.compile(punct1)

# generic terms
states = ['del', 'de', 'ny', 'va', 'ca', 'pa', 'oh', 'nc', 'wi', 'ma']
compustat = ['plc', 'cl', 'redh', 'adr', 'fd', 'lp', 'cp', 'tr', 'sp', 'cos', 'gp', 'old', 'new']
generics = ['the', 'a', 'of', 'and', 'an']
en_corps = ['corporation', 'incorporated', 'company', 'limited', 'inc', 'llc', 'ltd', 'corp']
eu_corps = ['aktiengesellschaft', 'aktiebolag', 'ag', 'nv', 'bv', 'gmbh', 'co', 'bv', 'sa', 'ab', 'se']
jp_corps = ['kabushiki', 'kaisha', 'seisakusho']
variants = ['trust', 'group', 'grp', 'hldgs', 'holdings', 'comm', 'inds', 'hldg', 'tech', 'international', 'comp']
dropout = states + compustat + generics + en_corps + eu_corps + jp_corps + variants
gener0_re = re.compile('|'.join([rf'\b{el}\b' for el in dropout]))

# standardize a firm name
def standardize_strong(name):
    name = name.lower()
    name = post0_re.sub('', name)
    name = acronym1_re.sub(r'\1\2\3', name)
    name = acronym2_re.sub(r'\1\2', name)
    name = acronym3_re.sub(r'\1\2\3', name)
    name = acronym4_re.sub(r'\1\2', name)
    name = acronym5_re.sub(r'\1\2', name)
    name = acronym6_re.sub(r'\1\2', name)
    name = acronym7_re.sub(r'\1\2', name)
    name = punct0_re.sub('', name)
    name = punct1_re.sub(' ', name)
    name = gener0_re.sub('', name)
    name = white0_re.sub(' ', name)
    return name.strip()

"""

un_names = unique(df[!,:organization])
un_names = un_names[ismissing.(un_names).!=1]
std_names = Vector{String}(undef, length(un_names))

@progress for (ind, element) in enumerate(un_names)
    std_names[ind] = py"standardize_strong"(element)
end

std_names


levenshtein(std_names[1], std_names[2])
