#!/bin/bash
arr=(0.4 0.45 0.50 0.55 0.60)
arr2=(0.05 0.1)
for i in `seq 0 $((${#arr[@]}-1))`; do
    for j in `seq 0 $((${#arr2[@]}-1))`; do
        echo $i $j ${arr[$i]} ${arr2[$j]}
        sed -i -e "s/float threshold = [0-9.]*;/float threshold = ${arr[$i]};/g" -e "s/float leader_sets = [0-9.]*;/float leader_sets = ${arr2[$j]};/g" replacement/dyn_irrip.l2c_repl
        ./build_champsim.sh no dyn_irrip task2b_${arr[$i]}_${arr2[$j]}
        ./bin/hashed_perceptron-no-no-no-no-no-no-no-lru-lru-lru-dyn_irrip-lru-lru-lru-lru-1core-task2b_${arr[$i]}_${arr2[$j]} -warmup_instructions 25000000 -simulation_instructions 25000000 -traces ../traces/Trace1.gz > text-files-dir/dyn_irrip_1_${arr[$i]}_${arr2[$j]}.txt
    done
done

