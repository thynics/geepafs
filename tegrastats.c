// init tegrastat process on backgound
// init - only once
// read tegrastat from shared memory

#include <stdio.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <unistd.h>
#include <pthread.h>
#include <string.h>

#include "tegrastats.h"

#include <sys/wait.h>
#include <signal.h>


#define SHM_SIZE sizeof(tegrastats_info_t)  // Shared memory size
#define SEM_NAME "/tegrastats_init_semaphore"
#define BUFFER_SIZE 1024

volatile sig_atomic_t keep_running = 1;

void sigint_handler(int sig) {
    keep_running = 0;
}


unsigned int get_closest_frequency(unsigned int input) {
    if (input == 114) return 114750000;
    else if (input == 216) return 216750000;
    else if (input == 318) return 318750000;
    else if (input == 420) return 420750000;
    else if (input == 522) return 522750000;
    else if (input == 624) return 624750000;
    else if (input == 726) return 726750000;
    else if (input == 854) return 854250000;
    else if (input == 930) return 930750000;
    else if (input == 1032) return 1032750000;
    else if (input == 1122) return 1122000000;
    else if (input == 1236) return 1236750000;
    else if (input == 1300) return 1300500000;
    else {
        printf("Frequency not available.\n");
        return 0;  // Return 0 if input does not match any case
    }
}
void *bash_thread(void *arg) {
    int pipefd[2];
    pid_t pid;
    char buffer[BUFFER_SIZE];

    // 注册信号处理函数用于优雅退出
    signal(SIGINT, sigint_handler);

    if (pipe(pipefd) == -1) {
        perror("pipe");
        return 1;
    }

    if ((pid = fork()) == -1) {
        perror("fork");
        return 1;
    }

    if (pid == 0) { // child
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        close(pipefd[1]);
        execl("/bin/bash", "sudo tegrastats", NULL);
        perror("execl");
        return 1;
    } else { // parent
        close(pipefd[1]);
        FILE* stream = fdopen(pipefd[0], "r");
        
        key_t key = ftok("tegrastats_content", 65);  // Generate unique key for shared memory
        if (key == -1) {
            perror("Failed to generate key");
            goto exit_thread;
        }
    
        // Create or get the shared memory segment
        int shmid = shmget(key, SHM_SIZE, 0666 | IPC_CREAT);
        if (shmid == -1) {
            perror("Failed to create or get shared memory");
            goto exit_thread;
        }
    
        // Attach the shared memory to the process's address space
        tegrastats_info_t *shared_memory = (tegrastats_info_t *)shmat(shmid, NULL, 0);
        if (shared_memory == (void *)-1) {
            perror("Failed to attach shared memory");
            goto exit_thread;
        }

        if (!stream) {
            perror("fdopen");
            return 1;
        }
        tegrastats_info_t t_info;
        while (keep_running && fgets(buffer, BUFFER_SIZE, stream)) {
            size_t len = strlen(buffer);
            if (len > 0 && buffer[len-1] == '\n') {
                buffer[--len] = '\0';
            }
            printf("Processed: %s\n", buffer);
            const char delim[] = " ";
            char *saveptr;
            char *token = strtok_r(buffer, delim, &saveptr);
            char *last = NULL;
            while (token != NULL) {
                if (last != NULL) {
                    if (strcmp(token, "EMC_FREQ")) {
                        unsigned int mem_util = 0;
                        int i = 0;
                        while(token[i] != '%') {
                            mem_util = mem_util * 10 + (token[i++] - '0');
                        }
                        t_info.mem_util = mem_util;
                    }
                    if (strcmp(token, "GR3D_FREQ")) {
                        unsigned int gpu_util = 0;
                        unsigned int gpu_freq = 0;
                        int mode = 1;
                        for (int i = 0; i < strlen(token); ++i) {
                            if(token[i] == '%') continue;
                            if(token[i] == '@') {
                                mode = 0;
                                continue;
                            };
                            if(mode) {
                                gpu_util = gpu_util * 10 + (token[i] - '0');
                            } else {
                                gpu_freq = gpu_freq * 10 + (token[i] - '0');
                            }
                        }
                        t_info.gpu_util = gpu_util;
                        t_info.current_freq = get_closest_frequency(gpu_freq);
                    }
                    if (strcmp(token, "VDD_SYS_GPU")) {
                        unsigned int power = 0;
                        int i = 0;
                        while(token[i] != '/') {
                            power = power * 10 + token[i++] - '0';
                        }
                        t_info.current_power = power;
                    }
                    last = NULL;
                } else if (strcmp(token, "EMC_FREQ")) {
                    last = "EMC_FREQ";
                } else if (strcmp(token, "GR3D_FREQ")) {
                    last = "GR3D_FREQ";
                } else if (strcmp(token, "VDD_SYS_GPU")) {
                    last = "VDD_SYS_GPU";
                }
            }
            *shared_memory = t_info;
            fflush(stdout);
        }

        // 清理资源
        kill(pid, SIGTERM);  // 发送终止信号
        fclose(stream);
        waitpid(pid, NULL, 0);  // 等待子进程退出
        printf("\nProcess terminated.\n");

exit_thread:
    pthread_exit(NULL);
}
}

// todo interval parameters
int tegrastats_init() {

}
void tegrastats_terminate() {
    // 
}
