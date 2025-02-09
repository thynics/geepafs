import subprocess

def monitor_tegrastats(output_file):
    command = ["sudo", "tegrastats"]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        try:
            for line in proc.stdout:
                print(line)
        except KeyboardInterrupt:
            print("terminate tegrastats")
            proc.terminate()

if __name__ == "__main__":
    output_file_path = "tegrastats_output.txt"
    monitor_tegrastats(output_file_path)
