#!/usr/bin/env sh

if [ "$(id -u)" -eq 0 ]
then
  systemctl stop acyonp
  systemctl disable acyonp
  rm /etc/systemd/system/acyonp.service
  rm /usr/local/sbin/acyonp_py2.py
  rm /etc/acyonp.ini
#  rm /etc/cron.hourly/rtsa
  rm /etc/logrotate.d/acyonp

  echo "rtsa is uninstalled, removing the uninstaller in progress"
  rm /usr/local/bin/uninstall-acyonp.sh
  echo "##### Reboot isn't needed #####"
else
  echo "You need to be ROOT (sudo can be used)"
fi

