#!/bin/bash
while true; do
  IPADDR=$(cat ipaddr) authbind --deep npm start
done
