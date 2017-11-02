#include "stdafx.h"
#include <stdio.h>



int main(int argc, char *argv[])
{
	std::auto_ptr<LVPM> Monsoon (new LVPM);
	using namespace std::chrono_literals;
	Monsoon->setup_usb(60000);
	Monsoon->getCalValues();
	Monsoon->setVout(3.7);
	Monsoon->Start(1250, 0xFFFFFFFF);
	std::this_thread::sleep_for(std::chrono_literals::operator ""ms(10000));
	Monsoon->Stop();
	Monsoon->setVout(0);
	Monsoon->Close();
}

