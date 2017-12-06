#include "stdafx.h"
#include <stdio.h>



int main(int argc, char *argv[])
{
	std::auto_ptr<LVPM> Monsoon (new LVPM);
	using namespace std::chrono_literals;
	Monsoon->setup_usb(60000);
	Monsoon->getCalValues();
	Monsoon->setVout(3.7);
	int i = 0;
	while (i < 5000)
	{
		Monsoon->Start(1250, 0xFFFFFFFF);
		Monsoon->Stop();
		printf("%d\n",i);
		i++;
	}
	Monsoon->setVout(0);
	Monsoon->Close();
}

