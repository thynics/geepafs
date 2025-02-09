import subprocess
import os
import signal
import threading
import time

dir = '/sys/devices/gpu.0/devfreq/17000000.gp10b'

available_frequencies = [114750000, 216750000, 318750000, 
                        420750000, 522750000, 624750000,
                        726750000, 854250000, 930750000,
                        1032750000, 1122000000, 1236750000,
                        1300500000]

min_frequency_path = dir + '/min_freq'
max_frequency_path = dir + '/max_freq'

process_tegrastats = None

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

def set_gpu_frequency(f):
    if f not in available_frequencies:
        raise ValueError(f"Frequency {f} is not supported.")
    
    with open(min_frequency_path, "w") as min_f_file, open(max_frequency_path, "w") as max_f_file:
        min_f_file.write(str(f) + "\n")
        max_f_file.write(str(f) + "\n")


gpu_util_threshold = 90

scan_freq_list = []

with open("tegrastats_output.txt", "r") as tf:
    while(True):
        info = tf.read()
        t = extract(info)

