#include <stdio.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/ioctl.h> //ioctl() call defenitions
#include <unistd.h>

int main() {
   int RTS_flag;
   RTS_flag = TIOCM_RTS;
   DTR_flag = TIOCM_DTR;
   ioctl(0, TIOCMBIS, &DTR_flag); //Set RTS pin
   sleep(1);
   ioctl(0, TIOCMBIC, &DTR_flag); //Clear RTS pin
   close(fd);
}
