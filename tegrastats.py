import subprocess
import time

def monitor_tegrastats(output_file):
    command = ["sudo tegrastats"]
    with open(output_file, "w") as file, open("tegrastats_all.txt", "w") as all_f:
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

if __name__ == "__main__":
    output_file_path = "tegrastats_output.txt"
    monitor_tegrastats(output_file_path)
