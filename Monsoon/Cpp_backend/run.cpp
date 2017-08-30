#include "stdafx.h"

int main()
{
	LVPM Monsoon;
	Monsoon.setup_usb();
	Monsoon.getCalValues();
	Monsoon.setVout(3.7);
	Monsoon.Start(1250, INFINITE);
	std::this_thread::sleep_for(std::chrono::milliseconds(5000));
	Monsoon.Stop();
	Monsoon.setVout(0);
	Monsoon.Close();

}