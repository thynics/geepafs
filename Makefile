
# Location of the CUDA Toolkit
CUDA_PATH := "/usr/local/cuda"

ifeq (${ARCH},$(filter ${ARCH},32 64))
    # If correct architecture and libnvidia-ml library is not found 
    # within the environment, build using the stub library
    
    ifneq (,$(findstring Ubuntu,$(OS)))
        DEB := $(shell dpkg -l | grep cuda)
        ifneq (,$(findstring cuda, $(DEB)))
            NVML_LIB := /usr/lib/nvidia-$(DRIVER_BRANCH)
        else 
            NVML_LIB := /lib${ARCH}
        endif
    endif

    ifneq (,$(findstring SUSE,$(OS)))
        RPM := $(shell rpm -qa cuda*)
        ifneq (,$(findstring cuda, $(RPM)))
            NVML_LIB := /usr/lib${ARCH}
        else
            NVML_LIB := /lib${ARCH}
        endif
    endif

    ifneq (,$(findstring CentOS,$(RHEL_OS)))
        RPM := $(shell rpm -qa cuda*)
        ifneq (,$(findstring cuda, $(RPM)))
            NVML_LIB := /usr/lib${ARCH}/nvidia
        else
            NVML_LIB := /lib${ARCH}
        endif
    endif

    ifneq (,$(findstring Red Hat,$(RHEL_OS)))
        RPM := $(shell rpm -qa cuda*)
        ifneq (,$(findstring cuda, $(RPM)))
            NVML_LIB := /usr/lib${ARCH}/nvidia
        else
            NVML_LIB := /lib${ARCH}
        endif
    endif

    ifneq (,$(findstring Fedora,$(RHEL_OS)))
        RPM := $(shell rpm -qa cuda*)
        ifneq (,$(findstring cuda, $(RPM)))
            NVML_LIB := /usr/lib${ARCH}/nvidia
        else
            NVML_LIB := /lib${ARCH}
        endif
    endif

else
    NVML_LIB := /usr/local/lib${ARCH}/stubs/
    $(info "libnvidia-ml.so.1" not found, using stub library.)
endif

ifneq (${ARCH},$(filter ${ARCH},32 64))
	$(error Unknown architecture!)
endif

NVML_LIB += /usr/local/cuda/lib64/
NVML_LIB_L := $(addprefix -L , $(NVML_LIB))

CFLAGS  := -I /usr/local/include -I /usr/local/cuda/include
LDFLAGS := $(NVML_LIB_L) -lm

SOURCES := dvfs.c tegrastats.c
OBJECTS := $(SOURCES:.c=.o)

all: dvfs

# Compile dvfs by linking both object files
dvfs: $(OBJECTS)
	$(CC) $(OBJECTS) $(CFLAGS) $(LDFLAGS) -o dvfs

# Generic rule to compile each source file into object files
%.o: %.c
	$(CC) -c $< $(CFLAGS) -o $@

clean:
	-@rm -f $(OBJECTS)
	-@rm -f dvfs
