#include <stdio.h>
#include <stdlib.h>
#include <systemd/sd-daemon.h>

int main() {
    uint64_t watchdogUsec;
    int sdres = sd_watchdog_enabled(0, &watchdogUsec);
}
