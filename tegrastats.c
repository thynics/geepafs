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


#define SHM_SIZE sizeof(tegrastats_info_t)  // Shared memory size
#define SEM_NAME "/tegrastats_init_semaphore"
#define BUFFER_SIZE 1024


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
    char *command = (char *)arg;
    char buffer[BUFFER_SIZE];
    FILE *fp = popen("ls", "r");
    if (fp == NULL) {
        perror("popen failed");
        pthread_exit(NULL);
    }

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

    tegrastats_info_t t_info;
    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        buffer[strcspn(buffer, "\n")] = 0;
        printf("Processed line: %s\n", buffer);
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
    }

exit_thread:
    pclose(fp);
    pthread_exit(NULL);
}

// todo interval parameters
int tegrastats_init() {
    key_t key = ftok("tegrastats_init", 65);  // Generate unique key for shared memory
    if (key == -1) {
        perror("Failed to generate key");
        return -1;
    }

    // Create or get the shared memory segment
    int shmid = shmget(key, sizeof(int), 0666 | IPC_CREAT);
    if (shmid == -1) {
        perror("Failed to create or get shared memory");
        return -1;
    }

    // Attach the shared memory to the process's address space
    int *shared_memory = (int *)shmat(shmid, NULL, 0);
    if (shared_memory == (void *)-1) {
        perror("Failed to attach shared memory");
        return -1;
    }

    // Create or open the semaphore
    sem_t *sem = sem_open(SEM_NAME, O_CREAT, 0666, 1);
    if (sem == SEM_FAILED) {
        perror("Failed to create or open semaphore");
        shmdt(shared_memory);
        return -1;
    }

    // Lock the semaphore to ensure mutual exclusion
    sem_wait(sem);

    // Check if shared memory is uninitialized or its value is not 1
    if (/*shared_memory != 1*/1) {
        pthread_t thread;
        char bash_command[] = "sudo tegrastats";
        if (pthread_create(&thread, NULL, bash_thread, bash_command) != 0) {
            perror("pthread_create failed");
            return 1;
        }
        // *shared_memory = 1;  // Initialize shared memory and set value to 1
    } else {
        printf("Shared memory already initialized. Skipping init.\n");
    }
    // Unlock the semaphore
    sem_post(sem);
    // Close the semaphore
    sem_close(sem);
    return 0;  // Return 0 to indicate normal execution
}

// read current tegrastats,  and extract it to struct
int tegrastats_get(tegrastats_info_t *info) {
    key_t key = ftok("tegrastats_content", 65);  // Generate unique key for shared memory
    if (key == -1) {
        perror("Failed to generate key");
        return -1;
    }

    // Create or get the shared memory segment
    int shmid = shmget(key, SHM_SIZE, 0666 | IPC_CREAT);
    if (shmid == -1) {
        perror("Failed to create or get shared memory");
        return -1;
    }

    // Attach the shared memory to the process's address space
    tegrastats_info_t *shared_memory = (tegrastats_info_t *)shmat(shmid, NULL, 0);
    if (shared_memory == (void *)-1) {
        perror("Failed to attach shared memory");
        return -1;
    }

    memcpy(info, shared_memory, sizeof(tegrastats_info_t));
    printf("Read tegrastats info: %d %d %d \n", info->current_freq, info->current_power, info->gpu_util);
    return 0;
}
void tegrastats_terminate() {
    // 
}
