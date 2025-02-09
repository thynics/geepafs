# run vgg

# 1. max frequency.
# 2. with geepafs

# perf
# energy consumption (avg power * time)

import subprocess
import time

# start tegrastats first
print("start tegrastats")
tegrastats_thread = subprocess.Popen(["sudo python3 ~/geepafs/tegrastats.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)


# run geepafs
print("start dvfs")
dvfs_thread = subprocess.Popen(["sudo ./dvfs mod Assure p90"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)

# warm-up run for about 30s
warn_up_thread = subprocess.Popen(["sudo python3 ~/jetson_benchmarks/benchmark.py --jetson_clocks --jetson_devkit tx2 --model_name vgg19 --csv_file_path ~/jetson_benchmarks/benchmark_csv/tx2-nano-benchmarks.csv --model_dir ~/jetson_benchmarks"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
print("warm up for 60s")
time.sleep(60)
# kill vgg, and re-run
print("warn up finished")
warn_up_thread.terminate()

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

# run vgg
vgg_start_time = time.time()
with open("vgg_max_perf_result.txt", "w") as f:
    vgg_perf_thread = subprocess.Popen(["sudo python3 ~/jetson_benchmarks/benchmark.py --jetson_clocks --jetson_devkit tx2 --model_name vgg19 --csv_file_path ~/jetson_benchmarks/benchmark_csv/tx2-nano-benchmarks.csv --model_dir ~/jetson_benchmarks"], stdout=f, stderr=subprocess.STDOUT, shell=True)
vgg_perf_thread.wait()
vgg_end_time = time.time()
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
    max_perf_lines = [extract(line.split("---")[1]) for line in tf if time_window(dvfs_vgg_start_time, dvfs_vgg_end_time, line)]

with open(f'vgg_geepafs_result.txt', "r") as dvfs_f, open(f'vgg_max_perf_result.txt', "r") as max_perf_f:
    dvfs_time = float([line for line in dvfs_f][10].split(":")[1][1:])
    max_perf_time = float([line for line in dvfs_f][10].split(":")[1][1:])

dvfs_avg_power = sum(x[gpu_power_key] for x in dvfs_lines) / len(dvfs_lines)
max_avg_power = sum(x[gpu_power_key] for x in max_perf_lines) / len(max_perf_lines)

dvfs_energy = dvfs_avg_power * dvfs_time
max_energy = max_avg_power * max_perf_time

print(f"Energy Decreased By{(max_energy - dvfs_energy)/max_energy:.2%}")
print(f"Performance Decreased By{(dvfs_time - max_perf_time)/dvfs_time:.2%}")