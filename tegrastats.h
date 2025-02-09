typedef struct tegrastats_info
{
    unsigned int gpu_util;
    unsigned int mem_util;
    unsigned int current_power;
    unsigned int current_freq;
} tegrastats_info_t;

int tegrastats_init();

int tegrastats_get(tegrastats_info_t *info);

void tegrastats_terminate();