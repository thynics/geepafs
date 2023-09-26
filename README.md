# GEEPAFS

This repository contains the source code of the GEEPAFS policy, as well as examplar scripts to launch experiments and post-process results.

## Requirements

This code targets NVIDIA GPU V100 or A100 on Linux platforms. NVIDIA CUDA should be fully installed on the system. Root privileges are necessary in order to apply GPU frequency setting.

Note that some V100/A100 GPUs' max frequency may be slightly different than the values defined in our codes. In that case, corresponding variables should be adjusted.

(GEEPAFS can also work for GPU types other than V100/A100 in principle. To work for another NVIDIA GPU, the constants in `dvfs.c` including minSetFreq, freqAvgEff, maxFreq, setMemFreq, numAvailableFreqs, numProbFreq, probFreqs, and the function getAvailableFreqs() need to be updated. To work for AMD/Intel/... GPUs, the NVML API calls for metric reading and frequency tuning should also be replaced by corresponding API calls.)

## Setup and Run

- To run the GEEPAFS policy, first open `dvfs.c` and select the correct GPU type by editing the `#define` lines at the front.
- Then, compile `dvfs.c` by executing `make`. Note that `CUDA_PATH` in the Makefile may need to be changed if cuda cannot be found in its default place.
- After compilation, run GEEPAFS with default settings by the command `sudo ./dvfs mod Assure p90`. This command runs the GEEPAFS policy with a performance constraint of 90%. Note that root privileges are necessary in applying frequency tuning. This program runs endlessly by default. Press ctrl-c to stop.
- To run a baseline policy, use the command `sudo ./dvfs mod MaxFreq`, where the name `MaxFreq` can also be replaced by `NVboost`, `EfficientFix`, or `UtilizScale`.

## Launch Experiments

Scripts to launch experiments are provided in `runExp.py`.
- To use the script, first go to folder `cuda_samples/benchmarks/` and use `make` in subfolders to compile each applications one by one. The files in the `cuda_samples` folder are from NVIDIA CUDA Code Samples and are copied here only to facilitate the running of testing experiments. We have made minor changes to the application source codes to extend their execution time.
- After benchmark compilation, launch experiments by the command `sudo python3 runExp.py`. It will automatically launch the GEEPAFS daemon and the benchmarks as subprocesses. Results are saved into the `./output/` folder.

Other benchmarks may also be added into experiments in similar ways. This package does not include more benchmarks as they usually require more steps in compilation and larger datasets (e.g., ImageNet2012 dataset occupies 150 GB).

## Post-Processing

Scripts to post-process the data generated by `runExp.py` are provided in `postprocessing.py`.
By default, the script reads the examplar files `allApps_Assure_p90_2iter_demo.out`, `dvfs_Assure_p90_demo.out`, and output processed files in .csv format. The script calculates the average performance, average power usage, average energy efficiency, etc. for each application.
Edit the script to process other files or other benchmarks.

## Latency Measurement

In the `./latency/` folder, we provide a small program to show how to measure the latency of NVML's metric reading and frequency tuning. More instructions can be found in `./latency/measure_latency.c`.

## Recent Progress

- We are planning to automate the parameter setting part of our codes, to make it easier to support other GPU types.
- We are working on extending this work to use NVIDIA DCGM for metric collection, which is a good alternative to NVML.

## Reference

Improving GPU Energy Efficiency through an Application-transparent Frequency Scaling Policy with Performance Assurance

Link to the paper will be provided.

## License
See the LICENSE file.
