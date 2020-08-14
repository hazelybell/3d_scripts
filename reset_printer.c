#include <unistd.h>
#include <sys/ioctl.h> //ioctl() call defenitions

int main() {
    int RTS_flag;
    int DTR_flag;
    RTS_flag = TIOCM_RTS;
    DTR_flag = TIOCM_DTR;
    ioctl(0, TIOCMBIS, &RTS_flag); // RTS LOW
    ioctl(0, TIOCMBIS, &DTR_flag); // DTR LOW
    usleep(100 * 1000); // in us
    ioctl(0, TIOCMBIC, &RTS_flag); // RTS HIGH
    ioctl(0, TIOCMBIC, &DTR_flag); // RTS HIGH
}
