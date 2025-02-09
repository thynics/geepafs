# run vgg

# 1. max frequency.
# 2. with geepafs

# perf
# energy consumption (avg power * time)

import subprocess
import time
import os


dir = '/sys/devices/gpu.0/devfreq/17000000.gp10b'

available_frequencies = [114750000, 216750000, 318750000, 
                        420750000, 522750000, 624750000,
                        726750000, 854250000, 930750000,
                        1032750000, 1122000000, 1236750000,
                        1300500000]

min_frequency_path = dir + '/min_freq'
max_frequency_path = dir + '/max_freq'

process_tegrastats = None

def set_gpu_frequency(f):
    if f not in available_frequencies:
        raise ValueError(f"Frequency {f} is not supported.")
    
    with open(min_frequency_path, "w") as min_f_file, open(max_frequency_path, "w") as max_f_file:
        min_f_file.write(str(f) + "\n")
        max_f_file.write(str(f) + "\n")

os.remove("vgg_geepafs_result.txt")
os.remove("vgg_max_perf_result.txt")

# start tegrastats first
print("start tegrastats")
tegrastats_thread = subprocess.Popen(["sudo python3 ~/geepafs/tegrastats.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)



set_gpu_frequency(1300500000)
time.sleep(60)

# run vgg
vgg_start_time = time.time()
with open("vgg_max_perf_result.txt", "w") as f:
    vgg_perf_thread = subprocess.Popen(["sudo python3 ~/jetson_benchmarks/benchmark.py --jetson_clocks --jetson_devkit tx2 --model_name vgg19 --csv_file_path ~/jetson_benchmarks/benchmark_csv/tx2-nano-benchmarks.csv --model_dir ~/jetson_benchmarks"], stdout=f, stderr=subprocess.STDOUT, shell=True)
vgg_perf_thread.wait()
vgg_end_time = time.time()

# run geepafs
print("start dvfs")
dvfs_thread = subprocess.Popen(["sudo ./dvfs mod Assure p90"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

# warm-up run for about 30s
warn_up_thread = subprocess.Popen(["/home/long/cublasgemm-benchmark/gemm"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
print("warm up for 60s")
time.sleep(60)
# kill vgg, and re-run
print("warn up finished")
warn_up_thread.terminate()
set_gpu_frequency(1300500000)
time.sleep(60)

# vgg -> vgg_geepafs_result.txt
# read tegrastats file, and calculate avg power
print(f'{time.time()}: start run vgg')
dvfs_vgg_start_time = time.time()
with open("vgg_geepafs_result.txt", "w") as f:
    vgg_thread = subprocess.Popen(["sudo python3 ~/jetson_benchmarks/benchmark.py --jetson_clocks --jetson_devkit tx2 --model_name vgg19 --csv_file_path ~/jetson_benchmarks/benchmark_csv/tx2-nano-benchmarks.csv --model_dir ~/jetson_benchmarks"], stdout=f, stderr=subprocess.STDOUT, shell=True)
vgg_thread.wait()
dvfs_vgg_end_time = time.time()
# kill geepafs
dvfs_thread.terminate()
# vgg -> vgg_max_perf_result.txt
# read tegrastats file, and calculate avg power.


tegrastats_thread.terminate()


mem_band_key = "EMC_FREQ"
gpu_util_key = "GR3D_FREQ"
gpu_power_key = "VDD_SYS_GPU"
cpu_power_key = "VDD_SYS_CPU"
tegrastats_keys = [mem_band_key, gpu_util_key, gpu_power_key, cpu_power_key]

# return dict{str:float}
def extract(p:str):
    # extract from 
    s = p.split(" ")
    last = ""
    tmp = {}
    for v in s:
        if v in tegrastats_keys:
            last = v
        else:
            if last != "":
                tmp[last]=v
                last = ""
    return {
        mem_band_key: int(tmp[mem_band_key].split("%")[0]),
        gpu_util_key: int(tmp[gpu_util_key].split("%")[0]),
        gpu_power_key: int(tmp[gpu_power_key].split("/")[0]),
        cpu_power_key: int(tmp[cpu_power_key].split("/")[0]),
    }

def time_window(start, end, line):
    ts = float(line.split("---")[0])
    return ts >= start and ts <= end

# calculation
with open("tegrastats_all.txt", "r") as tf:
    dvfs_lines = [extract(line.split("---")[1]) for line in tf if time_window(dvfs_vgg_start_time, dvfs_vgg_end_time, line)]
with open("tegrastats_all.txt", "r") as tf:
    max_perf_lines = [extract(line.split("---")[1]) for line in tf if time_window(vgg_start_time, vgg_end_time, line)]

print(len(dvfs_lines))
print(len(max_perf_lines))

print(dvfs_vgg_start_time, dvfs_vgg_end_time, vgg_start_time, vgg_end_time)

dvfs_time = (dvfs_vgg_end_time - dvfs_vgg_start_time)
max_perf_time = (vgg_end_time - vgg_start_time)


dvfs_avg_power = sum(x[gpu_power_key] for x in dvfs_lines) / len(dvfs_lines)
max_avg_power = sum(x[gpu_power_key] for x in max_perf_lines) / len(max_perf_lines)

dvfs_energy = dvfs_avg_power * dvfs_time
max_energy = max_avg_power * max_perf_time

print(f"Energy Decreased By{(max_energy - dvfs_energy)/max_energy:.2%}")
print(f"Performance Decreased By{(dvfs_time - max_perf_time)/dvfs_time:.2%}")