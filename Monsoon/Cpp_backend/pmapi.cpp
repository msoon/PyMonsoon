// Cpp_implementation.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include <future>
#include <iostream>
#include <thread>


using namespace std;
static const int QueueSize = 640000; //10,000 packet buffer, approximately 2-6 seconds worth of samples.
static const int packetLength = 64; //per firmware spec.
volatile bool running;
unsigned char Queue[QueueSize];
std::vector<UCHAR> processingQueue[QueueSize];
int queueIndex = 0;
int readIndex = 0;
thread sampleThread;
bool kernalDriverDetatched = false;

void sendCommand(libusb_device_handle* handle, unsigned char operation, int value)
{
	std::vector<unsigned char> bytes = intToBytes(value);
	short wIndex = ((bytes[3]) << 8 | bytes[2]);
	short Value = ((bytes[1] << 8) | operation);
	libusb_control_transfer(handle, 0x40, 0x01, wIndex, Value, 0, 0, 1000);
}

void stopSampling(libusb_device_handle* handle)
{
	running = false;
	libusb_control_transfer(handle, 0x40, 0x03, 0, 0, 0, 0, 5000);
	sampleThread.join();
}

int getSamples(UCHAR* processingQueue)
{
	int count = 0;
	if (queueIndex < readIndex)
	{
		count = QueueSize;
	}
	else
	{
		count = queueIndex;
	}
	int numPackets = count / packetLength;
	int processingIndex = 0;
	for(int i = readIndex; i < count; i ++)
	{
		processingQueue[processingIndex] = Queue[i];
		processingIndex++;
	}
	readIndex = count;
	if (readIndex >= QueueSize)
	{
		readIndex = 0;
	}
	return numPackets;

}

void startSampling(libusb_device_handle* handle, int calTime, int maxTime)
{
	std::vector<unsigned char> values_array = intToBytes(calTime);
	std::vector<unsigned char> maxTime_array = intToBytes(maxTime);
	short wValue = (values_array[0] | values_array[1]);
	short wIndex = (0x02 | 0);
	libusb_control_transfer(handle, 0x40, 0x02, wValue, wIndex, reinterpret_cast<unsigned char*>(maxTime_array.data()), 4, 5000);
	//std::future<void> result(std::async(getBulkData));
	sampleThread = thread(getBulkData, handle);
}

void init()
{
	queueIndex = 0;
	running = true;
	for (int i = 0; i < QueueSize; i++)
	{
		Queue[i] = 0;
	}
}

int getValue(libusb_device_handle* handle, unsigned char operation, int length)
{
	unsigned char data[4] = { 0,0,0,0 };
	short wIndex = (operation | 0);
	libusb_control_transfer(handle, 0xC0, 0x01, 0, wIndex, data, 4, 5000);
	int result = ((((data[3] << 24) | data[2] << 16) | data[1] << 8) | data[0]);
	return result;
}

libusb_device_handle* openDevice(int VID, int PID)
{
	int res = 0;
	libusb_device_handle* handle = 0;
	res = libusb_init(0);
	handle = libusb_open_device_with_vid_pid(0, VID, PID);
	if (libusb_kernel_driver_active(handle, 0))
	{
		libusb_detach_kernel_driver(handle, 0);
		kernalDriverDetatched = true;
	}
	res = libusb_claim_interface(handle, 0);
	return handle;
}

void getBulkData(libusb_device_handle* handle)
{
	init();
	int lengthTransferred = 0;
	unsigned char test = 0;
	while (running)
	{
		libusb_bulk_transfer(
			handle,
			0x81,
			&Queue[queueIndex],
			packetLength,
			&lengthTransferred,
			1);

		if (lengthTransferred > 0)
		{
			//TODO:  It might not strictly be necessary to zero out unused bits.
			//But I expect doing this will prevent someone from pulling their hair out while debugging later.
			//If you need that tiny extra ounce of performance, get rid of this.
			/*
			for (int i = queueIndex; i < queueIndex + packetLength; i++)
			{
				std::cout << std::hex << static_cast<unsigned>(Queue[i]);
				std::cout << " ";
			}
			std::cout << "\n";
			*/
			//std::cout << "\n";
			queueIndex += packetLength;//Always increment by 64 bytes.
			if (queueIndex >= QueueSize)
			{
				queueIndex = 0;
			}

		}
	}
}

void testRun(int blah)
{
	std::cout << blah;
}

void closeDevice(libusb_device_handle* handle)
{
	if (kernalDriverDetatched)
	{
		libusb_attach_kernel_driver(handle, 0);
		kernalDriverDetatched = false;
	}
	libusb_release_interface(handle, 0);
	
	libusb_exit(0);
}

std::vector<unsigned char> intToBytes(int paramInt)
{
	std::vector<unsigned char>  arrayOfByte(4);
	for (int i = 0; i < 4; i++)
		arrayOfByte[3 - i] = (paramInt >> (i * 8));
	return arrayOfByte;
}


