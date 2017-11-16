// stdafx.h : include file for standard system include files,
// or project specific include files that are used frequently, but
// are changed infrequently
//

#pragma once
#ifdef _DEBUG
#undef _DEBUG
#include <Python.h>
#define _DEBUG
#else
#include <Python.h>
#endif


#include "stdafx.h"
#include<mutex>
#include<atomic>

#include <vector>
#include <vector>
#include <libusb.h>
#include <iostream>
#include <thread>
#include <queue>
#include <mutex>
#include <libusb.h>

using namespace std;

//Python test objects
#ifdef WIN32
extern "C" __declspec(dllexport)  void __cdecl pySetup(int VID, int PID, int serialno=NULL);
extern "C" __declspec(dllexport)  void __cdecl  pyClose();
extern "C" __declspec(dllexport)  void __cdecl  pyStart(int calTime, int maxTime);
extern "C" __declspec(dllexport)  void __cdecl  pyStop();
extern "C" __declspec(dllexport)  unsigned char* _cdecl   pyGetBulkData(int num_numbers, unsigned char *numbers);
extern "C" __declspec(dllexport)  int __cdecl   pyQueueCount();
extern "C" __declspec(dllexport)  void __cdecl   pySendCommand(unsigned char operation, int value);
extern "C" __declspec(dllexport)  int __cdecl   pyGetValue(unsigned char operation, int length);
#elif __linux__
extern "C" void  pySetup(int VID, int PID, int serialno = NULL);
extern "C" void  pyClose();
extern "C"  void  pyStart(int calTime, int maxTime);
extern "C" void  pyStop();
extern "C" unsigned char*   pyGetBulkData(int num_numbers, unsigned char *numbers);
extern "C"  int   pyQueueCount();
extern "C"  void   pySendCommand(unsigned char operation, int value);
extern "C"  int   pyGetValue(unsigned char operation, int length);
#endif


typedef struct measurements measurements;
struct measurements {
	int numSamples;
	unsigned char* samples;
};


// TODO: reference additional headers your program requires here
std::vector<unsigned char> intToBytes(int paramInt);
void sendCommand(libusb_device_handle* handle, unsigned char operation, int value);
int getValue(libusb_device_handle* handle, unsigned char operation, int length);
libusb_device_handle*  openDevice(int VID, int PID,int serialno=NULL);
void closeDevice(libusb_device_handle* handle);
void startSampling(libusb_device_handle* handle, int calTime, int maxTime);
void stopSampling(libusb_device_handle* handle);
void init();
void getBulkData(libusb_device_handle* handle);
int getSamples(unsigned char* processingQueue, int maxTransfer);


class LVPM
{
private:
	mutex QueueAccess;
	libusb_device_handle* handle;
	int VendorID = 0x2AB9;
	int ProductID = 0x0001;

	std::queue<std::vector<unsigned char>> ProcessQueue;
	std::atomic<bool> running;

	thread swizzleThread;
	thread processThread;
	//Calibration information
	double mainFineScale = 35946.0;
	double mainCoarseScale = 3103.4;

	double mainFineResistor = 0.050;
	double mainCoarseResistor = 0.050;
	double factoryResistor = 0.050;

	//TODO:  Create a data structure that records the last x Cal values and averages them.
	int mainFineRefCal = 0;
	int mainCoarseRefCal = 0;
	int mainFineZeroCal = 0;
	int mainCoarseZeroCal = 0;

	int totalSampleCount = 0;

public:
	static const int packetLength = 64; //per firmware spec.
	static const int QueueSize = 64000;//Space for up to 1000 packets.
	unsigned char Packets[QueueSize];
	LVPM() noexcept;
	void setup_usb(int serialno=NULL);
	void setVout(double value);
	void Close();
	void Start(int calTime, int maxTime);
	void Stop();
	void SwizzlePackets(unsigned char* Packets, int numPackets);
	void ProcessPackets();
	void getCalValues();
	bool Calibrated();
	void Enque();
};
