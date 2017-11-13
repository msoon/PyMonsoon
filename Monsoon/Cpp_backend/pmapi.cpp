// Cpp_implementation.cpp : Defines the entry point for the console application.
//

#include "stdafx.h"
#include <future>
#include <iostream>
#include <thread>
#include <string>
#include <libusb.h>
#include<sys/resource.h>


using namespace std;
static const int QueueSize = 6400; //10,000 packet buffer, approximately 2-6 seconds worth of samples.
static const int packetLength = 64; //per firmware spec.
std::atomic<bool> running;
unsigned char Queue[QueueSize];
std::vector<unsigned char> processingQueue[QueueSize];
int queueIndex = 0;
int readIndex = 0;
thread sampleThread;


//Python test
static const int pyQueueSize = 6400;
unsigned char g_packets[pyQueueSize];
libusb_device_handle* g_handle;
int g_count = 0;
void pySetup(int VID, int PID, int serialno)
{
	g_handle = openDevice(VID, PID,serialno);
}

void pyClose()
{
	closeDevice(g_handle);
}

void pyStart(int calTime, int maxTime)
{
	for (int i = 0; i < QueueSize; i++)
	{
		g_packets[i] = 0;
	}
	startSampling(g_handle, calTime, maxTime);
}

void pyStop()
{
	stopSampling(g_handle);
}

unsigned char* pyGetBulkData(int num_numbers, unsigned char *packets)
{
	g_count = getSamples(packets, num_numbers);
	return packets;
}

int pyQueueCount()
{
	return g_count;
}

void pySendCommand(unsigned char operation, int value)
{
	sendCommand(g_handle, operation, value);
}

int pyGetValue(unsigned char operation, int length)
{
	return getValue(g_handle, operation, length);
}

//CPP Functions:

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

int getSamples(unsigned char* processingQueue, int maxTransfer)
{
	int count = 0;
	int numPackets = 0;
	if (queueIndex < readIndex)
	{
		count = QueueSize;
	}
	else
	{
		count = queueIndex;
	}
	if ((count - readIndex) > maxTransfer)
	{
		count = readIndex + maxTransfer;
	}
	numPackets = (count - readIndex) / packetLength;
	int processingIndex = 0;
	for (int i = readIndex; i < count; i++)
	{
		processingQueue[processingIndex] = Queue[i];
		processingIndex++;
	}
	readIndex = count;
	if (readIndex >= QueueSize)
	{
		readIndex = 0;
	}
	/*
	std::cout <<"Number of packets in Queue: ";
	std::cout << queueIndex /64;
	std::cout << "\n";
	std::cout << "Number of packets read: ";
	std::cout << readIndex/64;
	std::cout << "\n";
	*/
	return numPackets;

}

void startSampling(libusb_device_handle* handle, int calTime, int maxTime)
{
	std::vector<unsigned char> values_array = intToBytes(calTime);
	std::vector<unsigned char> maxTime_array = intToBytes(maxTime);
	short wValue = (values_array[0] | values_array[1]);
	short wIndex = (0x02 | 0);
	libusb_control_transfer(handle, 0x40, 0x02, wValue, wIndex, reinterpret_cast<unsigned char*>(maxTime_array.data()), 4, 5000);
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

libusb_device_handle* openDevice(int VID, int PID, int serialno)
{
	libusb_device **usb_devices;
	libusb_context *usb_context;
	int res = 0;
	libusb_device_handle* handle = 0;
	int kernalDriverDetached = 0; //TODO:  Kernal Driver detaching needs to happen with Linux.
	res = libusb_init(&usb_context);
	int device_count;
	device_count = libusb_get_device_list(usb_context, &usb_devices);
	libusb_device_descriptor d;
	string ss;
	unsigned char data[6];
	for (int i = 0; i < device_count; i++)
	{
		res = libusb_get_device_descriptor(usb_devices[i], &d);
		if (d.idProduct == PID && d.idVendor == VID)
		{
			res = libusb_open(usb_devices[i], &handle);
			if(res == 0)
			{
				libusb_get_string_descriptor_ascii(handle, d.iSerialNumber, data, sizeof(data));
				ss = "";
				for (int i = 0; i < 6; i++)
				{
					ss += data[i]; // call std::string::operator +=(char*)
				}
				int serial = std::stoi(ss);
				if (serialno == NULL || serialno == serial)
				{
					break;
				}
				else
				{
					libusb_release_interface(handle, 0);
				}
			}
		}

	}
	res = libusb_claim_interface(handle, 0);
	return handle;
}

void getBulkData(libusb_device_handle* handle)
{
	init();
	int lengthTransferred = 0;

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
			queueIndex += packetLength;//Always increment by 64 bytes.
			if (queueIndex >= QueueSize)
			{
				queueIndex = 0;
			}

		}
	}
}


void closeDevice(libusb_device_handle* handle)
{
	libusb_release_interface(handle, 0);
	//libusb_exit(0);
}

std::vector<unsigned char> intToBytes(int paramInt)
{
	std::vector<unsigned char>  arrayOfByte(4);
	for (int i = 0; i < 4; i++)
		arrayOfByte[3 - i] = (paramInt >> (i * 8));
	return arrayOfByte;
}


