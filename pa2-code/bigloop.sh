#!/bin/bash
arr=(1 2 3)
arr2=("no" "ip_stride" "spp" "no" "no" "no" "spp")
arr3=("lru" "lru" "lru" "rrip" "irrip" "dyn_irrip" "dyn_irrip")
arr4=("baseline" "task1a" "task1b" "base2" "task2a" "task2b" "task3")
for i in `seq 0 $((${#arr[@]}-1))`; do
    for j in `seq 0 $((${#arr2[@]}-1))`; do
        echo $i $j
        # sed -i -e "s/float threshold = [0-9.]*;/float threshold = ${arr[$i]};/g" -e "s/float leader_sets = [0-9.]*;/float leader_sets = ${arr2[$j]};/g" replacement/dyn_irrip.l2c_repl
        if [[ ${arr4[$j]} -eq "task3" ]]; then
            sed -i -e "s/#define TASK_3 0/#define TASK_3 1/g" replacement/dyn_irrip.l2c_repl
        else
            sed -i -e "s/#define TASK_3 1/#define TASK_3 0/g" replacement/dyn_irrip.l2c_repl
        fi
        ./build_champsim.sh ${arr2[$j]} ${arr3[$j]} ${arr4[$j]}
        ./bin/hashed_perceptron-no-${arr2[$j]}-no-no-no-no-no-lru-lru-lru-${arr3[$j]}-lru-lru-lru-lru-1core-${arr4[$j]} -warmup_instructions 25000000 -simulation_instructions 25000000 -traces ../traces/Trace${arr[$i]}.gz > text-files-dir/${arr4[$j]}_${arr[$i]}.txt
    done
done

