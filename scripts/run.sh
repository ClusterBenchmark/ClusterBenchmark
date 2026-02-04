#!/bin/bash

mkdir -p assortativity

rm -f assortativity/*

runs=1
mem_limit=32
threads=16
time_limit=60
clusters=4

for i in 0.95 0.925 0.90 0.875 0.85 0.825 0.80 0.775 0.75 0.725 0.70 0.675 0.65 0.625 0.60 0.575 0.55 0.525 0.50 0.475 0.45 0.425 0.40 0.375 0.35 0.325 0.30;
do
    source .venv/bin/activate
    python3 gen_adc_sbm.py --assortativity "$i" --prefix "$i"
    deactivate

    ../external/cnm/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/cnm.csv
    ../external/walktrap/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/walktrap.csv
    ../external/wt/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/wt.csv
    ../external/louvain/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/louvain.csv
    ../external/combo/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/combo.csv
    ../external/hollocou/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/hollocou.csv
    ../external/vieclus/run.sh "$i".graph $runs 5 $threads $mem_limit >> assortativity/vieclus.csv
    ../external/leiden/run.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/leiden.csv
    ../external/dmon/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> assortativity/dmon.csv
    ../external/commdgi/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> assortativity/commdgi.csv
    ../external/gnns/run.sh "$i".graph $runs $time_limit $threads $mem_limit >> assortativity/gnns.csv
    ../external/ucode/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> assortativity/ucode.csv
    ../external/dgcluster/run.sh "$i".graph $runs $time_limit $threads $mem_limit "$i".features >> assortativity/dgcluster.csv
    ../external/magi/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> assortativity/magi.csv
    ../external/clustre/run_fast.sh "$i".graph $runs $time_limit $mem_limit >> assortativity/clustre.csv
    ../external/lim/run.sh "$i".graph $runs $time_limit $threads $mem_limit "$i".features >> assortativity/lim.csv

    rm "$i".graph
    rm "$i".features
    rm "$i".labels
done

# mkdir -p feature_std

# rm -f feature_std/*

# for j in {-20..10}
# do
#     exp=$(echo "$j / 10" | bc -l)
#     i=$(echo "scale=4; e($exp * l(10))" | bc -l)

#     source .venv/bin/activate
#     python3 gen_adc_sbm.py --feature_signal "$i" --prefix "$i"
#     deactivate

#     ../external/cnm/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/cnm.csv
#     ../external/walktrap/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/walktrap.csv
#     ../external/wt/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/wt.csv
#     ../external/louvain/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/louvain.csv
#     ../external/combo/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/combo.csv
#     ../external/hollocou/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/hollocou.csv
#     ../external/vieclus/run.sh "$i".graph $runs 5 $threads $mem_limit >> feature_std/vieclus.csv
#     ../external/leiden/run.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/leiden.csv
#     ../external/dmon/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> feature_std/dmon.csv
#     ../external/commdgi/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> feature_std/commdgi.csv
#     ../external/gnns/run.sh "$i".graph $runs $time_limit $threads $mem_limit >> feature_std/gnns.csv
#     ../external/ucode/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> feature_std/ucode.csv
#     ../external/dgcluster/run.sh "$i".graph $runs $time_limit $threads $mem_limit "$i".features >> feature_std/dgcluster.csv
#     ../external/magi/run.sh "$i".graph $runs $time_limit $threads $clusters $mem_limit "$i".features >> feature_std/magi.csv
#     ../external/clustre/run_fast.sh "$i".graph $runs $time_limit $mem_limit >> feature_std/clustre.csv
#     ../external/lim/run.sh "$i".graph $runs $time_limit $threads $mem_limit "$i".features >> feature_std/lim.csv

#     rm "$i".graph
#     rm "$i".features
#     rm "$i".labels
# done

# for i in 1.00 0.95 0.90 0.85 0.80 0.75 0.70 0.65 0.60 0.55 0.50 0.45 0.40 0.35 0.30;
# do
#     source .venv/bin/activate
#     python3 gen_adc_sbm.py --feature_std $i --feature_signal 1.0 --assortativity 0.55 --prefix "$i"
#     python3 mix_graph_with_knn.py --graph "$i".graph  --features "$i".features --out "$i"_mix.graph
#     deactivate

#     cp "$i".labels "$i"_mix.labels

#     ../external/commdgi/run.sh "$i".graph 2 100 8 4 "$i".features >> feature_std/commdgi.csv
#     ../external/dmon/run.sh "$i".graph 2 100 8 4 "$i".features >> feature_std/dmon.csv
#     ../external/louvain/run.sh "$i".graph 2 60 >> feature_std/louvain.csv
#     ../external/louvain/run.sh "$i"_mix.graph 2 60 >> feature_std/louvain_mix.csv
#     ../external/leiden/run.sh "$i".graph 2 60 >> feature_std/leiden.csv
#     ../external/leiden/run.sh "$i"_mix.graph 2 60 >> feature_std/leiden_mix.csv
#     ../external/vieclus/run.sh "$i".graph 2 1 8 >> feature_std/vieclus.csv
#     ../external/vieclus/run.sh "$i"_mix.graph 2 1 8 >> feature_std/vieclus_mix.csv

#     rm "$i".graph
#     rm "$i".features
#     rm "$i".labels

#     rm "$i"_mix.graph
#     rm "$i"_mix.labels
# done
