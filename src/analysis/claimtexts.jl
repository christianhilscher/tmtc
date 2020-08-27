using Pkg
using LightGraphs, MetaGraphs
using CSV, DataFrames
using TextAnalysis, Profile
using BenchmarkTools
using ProgressMeter

wd = "/Users/christianhilscher/Desktop/tmtc/"

data_path = joinpath(wd, "data/")
data_path_full = joinpath(wd, "data/full/")
data_path_tmp = joinpath(wd, "data/tmp/")
graph_path = joinpath(wd, "output/tmp/")


function gather_bypatent(df::DataFrame)

    patent_arr = Array{String}(undef, length(unique(df[!,:pat_no])))
    txt_arr = similar(patent_arr)

    @progress for (ind, patent) in enumerate(unique(df[!,:pat_no]))
        patent_arr[ind] = patent
        txt_arr[ind] = join(df[df[!,:pat_no].==patent, :claim_txt])
    end

    return DataFrame(pat_no = patent_arr, claim_txt = txt_arr)
end

function makecorpus(df::DataFrame)

    tmp = Vector{StringDocument}(undef, size(df, 1))
    for i in eachindex(df[!,:pat_no])
        tmp[i] = StringDocument(df[i, :claim_txt])
    end

    crps = Corpus(tmp)
    return crps
end

function preproces!(crps::Corpus)
	prepare!(crps, strip_articles)
	prepare!(crps, strip_indefinite_articles)
	prepare!(crps, strip_definite_articles)
	# prepare!(crps, strip_preposition)
	prepare!(crps, strip_pronouns)
	prepare!(crps, strip_stopwords)
	prepare!(crps, strip_numbers)
	prepare!(crps, strip_non_letters)
	# prepare!(crps, strip_spares_terms)
	prepare!(crps, strip_frequent_terms)
	# prepare!(crps, strip_html_tags)

	stem!(crps)
end

function cosine_similarity(a::AbstractVector, b::AbstractVector)
	sA, sB, sI = 0.0, 0.0, 0.0

	for i in 1:length(a)
		sA += a[i]^2
		sI += a[i] * b[i]
	end
	for i in 1:length(b)
		sB += b[i]^2
	end
	return sI / sqrt(sA * sB)
end

function getweightmatrix(df::DataFrame)

	crps = makecorpus(df)

	preproces!(crps)
	update_lexicon!(crps)

	m = DocumentTermMatrix(crps)
	weights = tf_idf(m)
	return weights
end

function get_edgeweigth(node1::String, node2::String, info_mat::DataFrame,  weightmat)

	row1 = findfirst(x -> x == node1, info_mat[!,:pat_no])
	row2 = findfirst(x -> x == node2, info_mat[!,:pat_no])

	weight = cosine_similarity(weightmat[row1,:], weightmat[row2,:])
	return weight
end

## Playground

cd(join([data_path, "csv/"]))
df_text = CSV.read("patent_claims_fulltext.csv")

df = df_text[1:10000,:]

abc = gather_bypatent(df)



ghi = getweightmatrix(abc)
cosine_similarity(ghi[1,:], ghi[4,:])

get_edgeweigth("3930271", "3931342", abc, ghi)
