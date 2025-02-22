import subprocess
import time
import os

def monitor_tegrastats(output_file):
    command = ["sudo tegrastats"]
    with open(output_file, "w") as file, open("tegrastats_all_22.txt", "w") as all_f:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as proc:
            try:
                for line in proc.stdout:
                    decoded_line = line.decode('utf-8').strip()
                    file.seek(0)
                    file.truncate()
                    file.write(decoded_line.strip())
                    file.flush()
                    all_f.write(str(time.time()) +"---"+ decoded_line.strip() + "\n")
                    all_f.flush
                    
            except KeyboardInterrupt:
                proc.terminate()

output_file_path = "tegrastats_output.txt"
if os.path.exists("tegrastats_all.txt"):
    os.remove("tegrastats_all.txt")
print("start success")
monitor_tegrastats(output_file_path)
