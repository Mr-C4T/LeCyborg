#!/bin/bash
sudo rfcomm release all
sudo rfcomm bind 0 78:21:84:8D:65:2A
sudo chmod 777 /dev/rfcomm0
