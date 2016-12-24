#include <stdio.h>
#include <stdlib.h>
#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <termios.h>
#include <fcntl.h>

static int open_port(int port)
{
	int fd = -1; /* File descriptor for the port, we return it. */
	int ret;
	char device[13] = {0};

	sprintf(device, "/dev/ttyUSB%d", port);

	fd = open(device, O_RDWR | O_NOCTTY | O_NDELAY);
	if (fd == -1) {
		printf("Unable to open the port\n");
		return -1;
	}

	/* block */
	ret = fcntl(fd, F_SETFL, 0);
	if (ret < 0) {
		printf("fcntl\n");
		return -1;
	}

	ret = isatty(STDIN_FILENO);
	return fd;
}

static int setup_port(int fd, int speed, int data_bits, int parity, int stop_bits)
{
	int speed_arr[] = {B115200, B9600, B38400, B19200, B4800};
	int name_arr[] = {115200, 9600, 38400, 19200, 4800};
	struct termios opt;
	int ret=-1;
	int i=0;
	int len=0;

	ret = tcgetattr(fd, &opt);		/* get the port attr */
	if (ret < 0)
		printf("Unable to get the attribute\n");

	opt.c_cflag |= (CLOCAL | CREAD); /* enable the receiver, set local mode */
	opt.c_cflag &= ~CSIZE;	/* mask the character size bits*/
	opt.c_cflag &= ~CRTSCTS; /* remove hw handshake */

	/* baud rate */
	len = sizeof(speed_arr) / sizeof(int);
	for (i = 0; i < len; i++) {
		if (speed == name_arr[i]) {
			cfsetispeed(&opt, speed_arr[i]);
			cfsetospeed(&opt, speed_arr[i]);
		}
		if (i == len) {
			printf("Unsupported baud rate.\n");
			exit(-1);
		}
	}

	/* data bits */
	switch (data_bits)
	{
	case 8:
		opt.c_cflag |= CS8;
		break;
	case 7:
		opt.c_cflag |= CS7;
		break;
	default:
		printf("Unsupported data bits.\n");
	}

	/* parity bits */
	switch (parity)
	{
	case 'N':
	case 'n':
		opt.c_cflag &= ~PARENB;
		opt.c_cflag &= ~PARODD;
		break;
	case 'O':
	case 'o':
		opt.c_cflag|=(INPCK|ISTRIP); /*enable parity check, strip parity bits*/
		opt.c_cflag |= (PARODD | PARENB);
		break;
	case 'E':
	case 'e':
		opt.c_cflag|=(INPCK|ISTRIP); /*enable parity check, strip parity bits*/
		opt.c_cflag |= PARENB;
		opt.c_cflag &= ~PARODD;
		break;
	default:
		printf("Unsupported parity bits.\n");
	}

	/* stop bits */
	switch (stop_bits)
	{
	case 1:
		opt.c_cflag &= ~CSTOPB;
		break;
	case 2:
		opt.c_cflag |= CSTOPB;
		break;
	default:
		printf("Unsupported stop bits.\n");
	}

	opt.c_iflag = IGNBRK;
	opt.c_iflag &= ~(IXON|IXOFF|IXANY);

	tcflush(fd, TCIFLUSH);
	opt.c_cc[VTIME] = 1; /* no time out */
	opt.c_cc[VMIN] = 60; /* minimum number of characters to read */

	ret = tcsetattr(fd, TCSANOW, &opt); /* update it now */
	if (ret < 0) {
		printf("Unable to setup the port.\n");
		exit(0);
	}

	return 0; /* everything is OK! */
}

static void usage(char *pname)
{
	printf("<Usage>: %s [on/off]\n", pname);
}

enum {
	AC_ON = 1,
	AC_OFF = 2,
};

int main(int argc, char *argv[])
{
	int fd, op, ret;
	int learn = 0;
	char buf[20];
	char *pname, *pbase;
	
	pbase = strdup(argv[0]);
	pname = basename(pbase);

	if (argc != 2) {
		usage(pname);
		return 0;
	}

	if (!strcmp(pname, "ac-ctrl"))
		learn = 0;
	else if (!strcmp(pname, "ac-learn"))
		learn = 1;
	else {
		usage(pname);
		close(fd);
		return 0;
	}

	if (!strncmp(argv[1], "on", 2))
		op = AC_ON;
	else if (!strncmp(argv[1], "off", 3))
		op = AC_OFF;
	else {
		usage(pname);
		close(fd);
		return 0;
	}

	fd = open_port(0);          /* open the port(com1) */
	if (fd < 0)
		exit(0);

	ret = setup_port(fd, 9600, 8, 'N', 1);
	if (ret < 0)
		exit(0);

	memset(buf, 0, 20);
	if (learn == 0) {
		sprintf(buf, "send %d", op);
		ret = write(fd, buf, 6);
		if (ret <= 0) {
			printf("write %s error\n", buf);
			goto err;
		}
	} else {
		sprintf(buf, "learn %d", op);
		ret = write(fd, buf, 7);
		if (ret <= 0) {
			printf("write %s error\n", buf);
			exit(0);
		}
	}
	printf("Turn %s the air condition\n", op == AC_ON ? "on":"off");
	ret = read(fd, buf, 3);
	if (ret > 0)
		buf[ret] = '\0';
	else
		strcpy(buf, "FAIL");
	printf("response:%s\n", buf);
err:
	close(fd);

	return 0;
}
