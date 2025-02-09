import subprocess

def monitor_tegrastats(output_file):
    command = ["sudo tegrastats"]
    with open(output_file, "w") as file:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True) as proc:
            try:
                for line in proc.stdout:
                    file.seek(0)
                    file.truncate()
                    file.write(str(line.strip()))
                    file.flush()
                    
            except KeyboardInterrupt:
                proc.terminate()

if __name__ == "__main__":
    output_file_path = "tegrastats_output.txt"
    monitor_tegrastats(output_file_path)
