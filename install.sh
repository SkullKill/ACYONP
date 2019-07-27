#!/usr/bin/env sh

systemctl -q is-active acyonp  && { echo "ERROR: acyonp service is still running. Please run \"sudo systemctl stop acyonp\" to stop it."; exit 1; }
[ "$(id -u)" -eq 0 ] || { echo "You need to be ROOT (sudo can be used)"; exit 1; }

# 
mkdir -p /usr/local/sbin/
mkdir -p /var/log/acyonp/
install -m 644 acyonp.service /etc/systemd/system/acyonp.service
install -m 755 acyonp_py2.py /usr/local/sbin/acyonp_py2.py
install -m 644 acyonp.ini /etc/acyonp.ini
install -m 644 uninstall.sh /usr/local/sbin/uninstall-acyonp.sh
systemctl daemon-reload
systemctl enable acyonp
systemctl start acyonp

# cron
#install -m 755 rtsa.hourly /etc/cron.hourly/rtsa
install -m 644 acyonp.logrotate /etc/logrotate.d/acyonp

echo "#####             acyonp installed             #####"
echo "##### edit /etc/acyonp.ini to configure options ####"
