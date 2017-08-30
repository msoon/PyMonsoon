#pragma once
#include "stdafx.h"
#include "Operations.h"
#include <future>
#include <iostream>
#include <thread>





LVPM::LVPM()
{
	
	for (int i = 0; i < QueueSize; i++)
	{
		Packets[i] = 0;
	}
}

void LVPM::setup_usb()
	{
		handle = openDevice(VendorID, ProductID);
	}

void LVPM::setVout(float value)
	{
		int conversion = 1048576 * value;
		unsigned char opcode = 0x41;
		sendCommand(handle, opcode, conversion);
	}
void LVPM::Close()
{
	closeDevice(handle);
}

void LVPM::Start(int calTime, int maxTime)
{
	totalSampleCount = 0;
	running = true;
	swizzleThread = thread(&LVPM::Enque,this);
	processThread = thread(&LVPM::ProcessPackets,this);
	startSampling(handle, calTime, maxTime);

}


void LVPM::Stop()
{
	stopSampling(handle);
	running = false;
	swizzleThread.join();
	processThread.join();
}



void LVPM::getCalValues()
{
	mainFineResistor = factoryResistor + getValue(handle, setMainFineResistorOffset, 1) * 0.0001;
	mainCoarseResistor = factoryResistor + getValue(handle, setMainCoarseResistorOffset, 1) * 0.0001;
	
	mainFineScale = 35946.0 * (factoryResistor / mainFineResistor);
	mainCoarseScale = 3103.4 * (factoryResistor / mainCoarseResistor);
}

void LVPM::SwizzlePackets(UCHAR* Packets, int numPackets)
{
	int offset = 0;
	
	for (int i = 0; i < numPackets; i++)
	{
		std::vector<UCHAR> Packet;
		
		int packetStart = i * packetLength;
		Packet.push_back(Packets[packetStart]);
		Packet.push_back(Packets[packetStart+1]);
		Packet.push_back(Packets[packetStart+2]);
		Packet.push_back(Packets[packetStart+3]);
		for (offset = 4; offset < packetLength; offset += 2)
		{
			Packet.push_back(Packets[packetStart + offset + 1]);
			Packet.push_back(Packets[packetStart + offset]);
		}
		QueueAccess.lock();
		ProcessQueue.push(Packet);
		QueueAccess.unlock();
	}
}

void LVPM::Enque()
{
	while (running)
	{
		int count = getSamples(Packets);
		SwizzlePackets(Packets, count);
	}
}

void LVPM::ProcessPackets()
{
	while (running)
	{
		if (!ProcessQueue.empty())
		{
			QueueAccess.lock();
			std::vector<UCHAR> Packet = ProcessQueue.front();
			ProcessQueue.pop();
			QueueAccess.unlock();
			int offset = 0;
			unsigned int dropped = ((Packet[offset] << 8) | Packet[offset + 1]);
			offset += 2;
			int flags = Packet[offset++];
			int numObs = Packet[offset++];


			for (int ob = 0; ob < numObs; ob++)
			{
				totalSampleCount++;
				bool Coarse = false;
				short Raw = 0;
				float res = mainFineResistor;
				float CalRef = mainFineRefCal;
				float CalZero = mainFineZeroCal;
				float scale = mainFineScale;

				short mainCoarse = ((Packet[offset + 1] << 8) | Packet[offset]);
				offset += 2;
				short mainFine = ((Packet[offset + 1] << 8) | Packet[offset]);
				offset += 10; //Skipping USB and Aux channels for now
				short mainVoltage = ((Packet[offset + 1] << 8) | Packet[offset]);
				offset += 4; //Skipping over USB voltage, Main Gain.
				UCHAR PacketType = Packet[offset] & 0x30;
				offset += 2;

				float slope = 0;
				float Current = 0;
				float voltage = 0;
				//printf("StatusType: %d \n", PacketType);
				switch (PacketType)
				{
				case 0x10: //ZeroCal
					mainFineZeroCal = mainFine;
					mainCoarseZeroCal = mainCoarse;
					break;
				case 0x30: //Refcal
					mainFineRefCal = mainFine;
					mainCoarseRefCal = mainCoarse;
					break;
				case 0x00: //Measurement
					if (Calibrated())
					{
						if (mainFine > 30000)
						{
							Coarse = true;
							Raw = mainCoarse;
							scale = mainCoarseScale;
							CalRef = mainCoarseRefCal;
							CalZero = mainCoarseZeroCal;
						}
						else
						{
							Coarse = false;
							Raw = mainFine;
							scale = mainFineScale;
							CalRef = mainFineRefCal;
							CalZero = mainFineZeroCal;
						}
						slope = scale / (CalRef - CalZero);
						Current = slope * (Raw - CalZero);
						if (!Coarse)
						{
							Current /= 1000; //uA -> mA
						}
						voltage = mainVoltage * (62.5 / 1e6) * 2;

						if (totalSampleCount % 1000 == 0)
						{
							printf("Current: %4.2f Voltage: %4.2f Dropped: %d Total Samples: %d \n", Current, voltage, dropped, totalSampleCount);
						}
					}

				default:

					break;
				}

			}
		}
	}

}
bool LVPM::Calibrated()
{
	return mainFineRefCal != 0 &&
		mainCoarseRefCal != 0 &&
		mainFineZeroCal != 0 &&
		mainCoarseZeroCal != 0;
}
