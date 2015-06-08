#include <time.h>
#include <X11/resource.h>
#include <locale.h>


int main (int argc, char **argv) {

	time_t now;
  	struct tm *timeinfo;
  	char *timestr;

  	struct battstate *life;

  	while(1){
  		now = time(0);
  		timeinfo = localtime ( &now );
  		timestr = asctime (timeinfo);

  		printf("%s",timestr);

  		sleep(1);
  	}

  	return 0;
}