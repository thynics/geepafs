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
#include <stdlib.h>


unsigned int get_closest_frequency(unsigned int input)
{
    if (input == 114)
        return 114750000;
    else if (input == 216)
        return 216750000;
    else if (input == 318)
        return 318750000;
    else if (input == 420)
        return 420750000;
    else if (input == 522)
        return 522750000;
    else if (input == 624)
        return 624750000;
    else if (input == 726)
        return 726750000;
    else if (input == 854)
        return 854250000;
    else if (input == 930)
        return 930750000;
    else if (input == 1032)
        return 1032750000;
    else if (input == 1122)
        return 1122000000;
    else if (input == 1236)
        return 1236750000;
    else if (input == 1300)
        return 1300500000;
    else
    {
        printf("Frequency not available: %d.\n", input);
        return 0; // Return 0 if input does not match any case
    }
}

// todo interval parameters
int tegrastats_init()
{
    return 0;
}

int tegrastats_get(tegrastats_info_t *info)
{

    FILE *file = fopen("tegrastats_output.txt", "rb");  // 以二进制方式打开文件
    if (file == NULL) {
        perror("open file fail");
        return 1;
    }

    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    rewind(file);

    char *buffer = (char *)malloc(file_size + 1);
    if (buffer == NULL) {
        perror("allocate buffer fail");
        fclose(file);
        return 1;
    }
    size_t bytes_read = fread(buffer, 1, file_size, file);
    buffer[bytes_read] = '\0';

    const char delim[] = " ";
    char *saveptr;
    char *token = strtok_r(buffer, delim, &saveptr);
    char *last = NULL;
    while (token != NULL)
    {
        if (last != NULL)
        {
            printf("LAST: %s\n", last);
            printf("NOW: %s\n", token);
            if (strcmp(token, "EMC_FREQ"))
            {
                unsigned int mem_util = 0;
                int i = 0;
                while (token[i] != '%')
                {
                    mem_util = mem_util * 10 + (token[i++] - '0');
                }
                info->mem_util = mem_util;
            }
            if (strcmp(token, "GR3D_FREQ"))
            {
                unsigned int gpu_util = 0;
                unsigned int gpu_freq = 0;
                int mode = 1;
                for (int i = 0; i < strlen(token); ++i)
                {
                    if (token[i] == '%')
                        continue;
                    if (token[i] == '@')
                    {
                        mode = 0;
                        continue;
                    };
                    if (mode)
                    {
                        gpu_util = gpu_util * 10 + (token[i] - '0');
                    }
                    else
                    {
                        gpu_freq = gpu_freq * 10 + (token[i] - '0');
                    }
                }
                info->gpu_util = gpu_util;
                info->current_freq = get_closest_frequency(gpu_freq);
            }
            if (strcmp(token, "VDD_SYS_GPU"))
            {
                unsigned int power = 0;
                int i = 0;
                while (token[i] != '/')
                {
                    power = power * 10 + token[i++] - '0';
                }
                info->current_power = power;
            }
            last = NULL;
        }
        else if (strcmp(token, "EMC_FREQ"))
        {
            last = "EMC_FREQ";
        }
        else if (strcmp(token, "GR3D_FREQ"))
        {
            last = "GR3D_FREQ";
        }
        else if (strcmp(token, "VDD_SYS_GPU"))
        {
            last = "VDD_SYS_GPU";
        }
    }
    return 0;
}

void tegrastats_terminate()
{
    //
}
