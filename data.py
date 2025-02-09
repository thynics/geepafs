dvfs_vgg_start_time = 1739132184.3430378
dvfs_vgg_end_time = 1739132695.119636
vgg_start_time = 1739132695.1196973
vgg_end_time = 1739133058.8895764

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