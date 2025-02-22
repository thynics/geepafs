import subprocess
import os
import time
import random
import asyncio


async def run_geepafs():
    dvfscmd = f'sudo ./dvfs mod Assure p95 > output/dvfs_{time.time()}.txt'
    os.system(dvfscmd)

async def tegrastats_record():
    global tegrastats_command_thread
    tegrastats_command_thread = await asyncio.create_subprocess_shell(
        "sudo tegrastats",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    print("create tegrastats success")

    with open("./tegrastats_records_geepafs.txt", "a") as tf, open("tegrastats_output.txt", "w") as lf:
        while True:
            line = await tegrastats_command_thread.stdout.readline()
            if not line:
                break
            decoded_line = line.decode('utf-8').strip()
            lf.seek(0)
            lf.truncate()
            lf.write(decoded_line.strip())
            lf.flush()
            tf.write(str(time.time()) +"---"+ decoded_line.strip() + "\n")
            tf.flush()


benchmarks = ["inception_v4", "vgg19", "tiny-yolov3", "resnet"]
gpu_dir = '/sys/devices/gpu.0/devfreq/17000000.gp10b/'
available_gpu_frequencies = [114750000, 216750000, 318750000,
                             420750000, 522750000, 624750000,
                             726750000, 854250000, 930750000,
                             1032750000, 1122000000, 1236750000,
                             1300500000]

min_gpu_frequency_path = gpu_dir + 'min_freq'
max_gpu_frequency_path = gpu_dir + 'max_freq'

current_gpu_frequency = 1300500000

mem_dir = '/sys/kernel/debug/bpmp/debug/clk/emc/'
available_memory_frequency = [1062400000, 1331200000, 1600000000, 1866000000]

def set_gpu_frequency(f):
    global current_gpu_frequency
    if f >= current_gpu_frequency:
        current_gpu_frequency = f
        os.system(f'echo {f} > {max_gpu_frequency_path}')
        os.system(f'echo {f} > {min_gpu_frequency_path}')
    if f < current_gpu_frequency:
        current_gpu_frequency = f
        os.system(f'echo {f} > {min_gpu_frequency_path}')
        os.system(f'echo {f} > {max_gpu_frequency_path}')

def set_memory_frequency(f):
    os.system(f'echo 1 >/sys/kernel/debug/bpmp/debug/clk/emc/mrq_rate_locked')
    os.system(f'echo {f} > /sys/kernel/debug/bpmp/debug/clk/emc/rate')
    os.system(f'echo 1 > /sys/kernel/debug/bpmp/debug/clk/emc/state')

benchmark_dir = "/media/work_data/long/jetson_benchmarks"

def get_benchmark_command(benchmark_name):
    return f"sudo python3 {benchmark_dir}/benchmark.py \
            --jetson_clocks --jetson_devkit tx2 --model_name {benchmark_name}\
            --csv_file_path {benchmark_dir}/benchmark_csv/tx2-nano-benchmarks.csv\
            --model_dir {benchmark_dir}"

async def run_benchmarks(tag:str):
    for bm in benchmarks:
        await asyncio.sleep(10)
        process = await asyncio.create_subprocess_shell(
            f"{get_benchmark_command(bm)} > {bm}_{tag}_output.txt",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        await process.wait()

def block_run_benchmarks(tag:str):
    for bm in benchmarks:
        os.system(f"{get_benchmark_command(bm)} > {bm}_{tag}_output.txt")

async def main():
    set_memory_frequency(1866000000)
    await asyncio.sleep(20)

    set_gpu_frequency(1300500000)
    await asyncio.sleep(20)

    tegrastats_task = asyncio.create_task(tegrastats_record())

    await asyncio.sleep(20)
    print(f"{time.time()}: run geepafs ...")
    geepafs = asyncio.create_task(run_geepafs())
    block_run_benchmarks("")

    geepafs.cancel()
    tegrastats_task.cancel()

asyncio.run(main())