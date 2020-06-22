#!/bin/bash
lvcreate -T -L 1100G -V1000G -n t1 --thinpool p1 thinvg
lvcreate -T -V1000G -n t2 thinvg/p1

mkfs.xfs /dev/thinvg/t2 
mkfs.xfs /dev/thinvg/t1 

mount /dev/thinvg/t1 /home/nkshirsa/formt/t1
mount /dev/thinvg/t2 /home/nkshirsa/formt/t2/

mkdir /home/nkshirsa/formt/t1/folder1
mkdir /home/nkshirsa/formt/t1/folder2
mkdir /home/nkshirsa/formt/t2/folder2
mkdir /home/nkshirsa/formt/t2/folder1

fio --name=randwrite --rw=randwrite --direct=1 --ioengine=libaio --bs=4m  --group_reporting  --nrfiles=1000  --directory=/home/nkshirsa/formt/t2/folder1/ --size=10G
fio --name=randwrite --rw=randwrite --direct=1 --ioengine=libaio --bs=4m  --group_reporting  --nrfiles=1000  --directory=/home/nkshirsa/formt/t2/folder2/ --size=10G
fio --name=randwrite --rw=randwrite --direct=1 --ioengine=libaio --bs=4m  --group_reporting  --nrfiles=1000  --directory=/home/nkshirsa/formt/t1/folder2/ --size=10G
fio --name=randwrite --rw=randwrite --direct=1 --ioengine=libaio --bs=4m  --group_reporting  --nrfiles=1000  --directory=/home/nkshirsa/formt/t1/folder1/ --size=10G

dd if=/dev/urandom of=/home/nkshirsa/formt/t2/somefile bs=1M count=5000 
dd if=/dev/urandom of=/home/nkshirsa/formt/t1/somefile bs=1M count=5000

rm -rf /home/nkshirsa/formt/t2/somefile
rm -rf /home/nkshirsa/formt/t2/folder1
rm -rf /home/nkshirsa/formt/t1/folder1
fstrim /home/nkshirsa/formt/t1
fstrim /home/nkshirsa/formt/t2

umount /home/nkshirsa/formt/t1
umount /home/nkshirsa/formt/t2

vgchange -an thinvg

