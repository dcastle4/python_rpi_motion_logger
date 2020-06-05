#!/usr/bin/env python3
# makes sure the script runs in Python3

"""
	File:		imu_csv.py
	Written by: 	Daniel Castle
	For: 		Dr. Kihei's research (secure traffic cabinets)

	Description:
		This Python script was created to track the orientation/motion of the Raspberry Pi
		SenseHat over time, with some context specific implementation for Dr. Kihei's research.

		The idea will be that the Pi will be attached to a door knob, with a person trying to perform
		an action on the door knob (either unlocking it normally, lockpicking it, or leaving it idle).
		The Pi will track the motion of the knob while the person does this, in order to use this data
		for a machine learning model created and run by Dr. Kihei. Hopefully, we can use the data to
		create a machine learning model that can reliably tell the difference between these actions.

	References:
		Since this was my first time really doing a deep dive into Python, I had to use a lot of resources,
		to the point where it wouldn't be viable to put all the links to them in here. Instead, they are all
		linked in a file called "references.txt" in the doc folder of this repo. Check there for resources on
		how I made this script.

"""

# import statements
from signal import signal, SIGINT
import sys, select
from sys import exit, argv
from sense_hat import SenseHat
import csv
from csv import writer
from datetime import datetime
import time

# color definitions for SenseHat 8x8 RGB LED array
red	 = (255,0,0)
green	 = (0,255,0)
blue	 = (0,0,255)
cyan	 = (0,255,255)
pink	 = (255,0,255)
yellow	 = (255,255,0)
black	 = (0,0,0)

# lock pick mode pattern for 8x8 RGB LED array
pick_led_pattern = [
	black, blue, black, black, cyan, cyan, cyan, black,				# first row
	blue, black, blue, black, black, cyan, black, black,				# second row
	blue, blue, black, black, black, cyan, black, black,				# third row
	blue, black, black, black, cyan, cyan, cyan, black,				# fourth row
	black, pink, pink, black, yellow, black, black, black,				# fifth row
	pink, black, black, black, yellow, black, yellow, black,			# sixth row
	pink, black, black, black, yellow, yellow, black, black,			# seventh row
	black, pink, pink, black, yellow, black, yellow, black				# eighth row
]

# key mode pattern for 8x8 RGB LED array
key_led_pattern = [
	black, black, black, black, black, black, black, black,				# first row
	black, black, black, black, black, yellow, yellow, black,			# second row
	black, black, black, black, yellow, black, black, yellow,			# third row
	yellow, yellow, yellow, yellow, yellow, black, black, yellow,			# fourth row
	yellow, black, yellow, black, yellow, black, black, yellow,			# fifth row
	yellow, black, yellow, black, black, yellow, yellow, black,			# sixth row
	black, black, black, black, black, black, black, black, 			# seventh row
	black, black, black, black, black, black, black, black				# eighth row
]

# no key mode pattern for 8x8 RGB LED array
nokey_led_pattern = [
	red, black, black, black, black, black, black, red,				# first row
	black, red, black, black, black, yellow, red, black,				# second row
	black, black, red, black, yellow, red, black, yellow,				# third row
	yellow, yellow, yellow, red, red, black, black, yellow,				# fourth row
	yellow, black, yellow, red, red, black, black, yellow,				# fifth row
	yellow, black, red, black, black, red, yellow, black,				# sixth row
	black, red, black, black, black, black, red, black, 				# seventh row
	red, black, black, black, black, black, black, red				# eighth row
]


def keyboard_handler():

	# pauses when Enter key is hit
	# see https://stackoverflow.com/a/1450063
	i,o,e = select.select([sys.stdin],[],[],0)
	for s in i:
		if s == sys.stdin:
			input = sys.stdin.readline()
			return True
	return False


def sigint_handler(signal_received, frame):

	# print exit message when SIGINT/ctrl-c interrupt is caught
	print("Exiting logger script")

	# clear the RGB LED array
	sense.clear()

	# exit Python
	exit(0)


def set_name():

	name_check = "N"

	# while loop to wait for yes input (run this loop while N/n input is detected)
	while (name_check.find("N") != -1) or (name_check.find("n") != -1):

		# take in name from user input
		name = input("Please type in your name and hit ENTER to confirm: ")

		# ask the user to confirm that the name is right
		name_check = input("Is this name correct? [enter Y/y for yes or N/n for no] --> " + name + ": ")

	# return name
	return name


def select_mode():

	# print mode select message
	print("Please enter the number corresponding to the desired mode and hit ENTER to confirm:\n		[1->pick] [2->key] [3->nokey]")

	# take in first charcter of input
	num_mode = sys.stdin.read(1)

	# make sure first character of input is a digit
	#(there were errors where num_mode would resolve to "\n", so this loop was added to reconcile that)
	while num_mode.isdigit() == False:
		num_mode = sys.stdin.read(1)

	# switch statement to set new mode depending on number given by user
	mode = {
		"1": "pick",
		"2": "key",
		"3": "nokey"
	}[num_mode]

	# return the mode
	return mode


def display_mode(mode):

	# switch statement to set current pattern for current mode
	current_pattern = {
		"pick"	:   pick_led_pattern,
		"key"	:   key_led_pattern,
		"nokey"	:   nokey_led_pattern
	}[mode]

	# set the current pattern on the 8x8 RGB LED array
	sense.set_pixels(current_pattern)



def log_orientation():

	name = set_name()

	mode = select_mode()

	# append start date and time of logging to file name/path
	# (this prevents file from being rewritten on next function call)
	file_path = "./log/" + name + "_" + "log" + "_" + datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + ".csv"

	#fetch the start time using time() function
	start_time = time.time()

	# open the file at the specified path with write permission
	with open(file_path, 'w', newline='') as file:

		# create a list that defines the header for the csv
		csv_header = ['roll', 'pitch', 'yaw', 'x', 'y', 'z', 'timestamp', 'runtime', 'mode', 'name']

		# create and instantiate a csv writer
		writer = csv.writer(file)

		# write the header to the csv file (once)
		writer.writerow(csv_header)

		while True:

			# only execute if the keyboard handler detects input
			if  keyboard_handler():

				# assign new mode from user input
				mode = select_mode()

			else:

				# display the current mode on the 8x8 RGB LED array
				display_mode(mode)

				# create and instantiate orientation object and record orientation to it
				orientation = sense.get_orientation_degrees()

				# create and instantiate raw acceleration object and record raw acceleration to it
				raw_acceleration = sense.get_accelerometer_raw()

				# calculate runtime (fetch current time and subtract start time to get runtime)
				runtime = time.time() - start_time

				# create data list variable and add orientation, current time, and mode
				data = []
				data.append( "%s" % orientation["roll"] )
				data.append( "%s" % orientation["pitch"] )
				data.append( "%s" % orientation["yaw"] )
				data.append( "%s" % raw_acceleration["x"] )
				data.append( "%s" % raw_acceleration["y"] )
				data.append( "%s" % raw_acceleration["z"] )
				data.append(datetime.now().strftime("%m/%d/%Y_%H:%M:%S"))
				data.append(runtime)
				data.append(mode)
				data.append(name)

				# write the data list to the CSV file
				writer.writerow(data)

				# print the data list (for debug)
				print("\n".join(map(str, data)))




# main function
if __name__ == "__main__":

	# create and instantiate sense-hat variable
	sense = SenseHat()

	#  create signal for SIGINT interrupt and handle it with sigint_handler function
	signal(SIGINT, sigint_handler)

	# run the log_orientation function
	log_orientation()


