There are 2 reasons why lvm thin pools cannot be shrunk today.

a) The pool may not have written data linearly, and so there might be data at 
the end, i.e data chunks may be allocated at the end of the pool device 
and dm-thin does not provide scrubbing to free it up

b) lvm doesn't support reduction of the thin pool data lv (tdata)

Assuming b) will be available in upcoming lvm2 features, this tool makes thinpool shrink possible, and the ability for lvm2 to
use the freed up space for other logical volumes. It examines thin pool metadata mappings and moves single and range 
mappings beyond the new size, to free space within the new limit. 

Once the mappings are moved to free ranges or blocks inside the new  limit, the pool can be safely reduced. 

The script changes the thinpool meta data as well as the VG metadata. (Changing the VG metadata will not be necessary once there is 
lvm2 support for reduction of the tdata LV)

Run this script on inactive pools with all its thinlvs unmounted.

Usage:
./thin_shrink -L new_size -t vgname/poolname

At the end of the run, you will have a deactivated thin pool reduced to the size you specified, if reduce was possible [1]

[1] The pool will not reduce in size if the new size is lesser than the number of
mapped blocks in the pool. The pool will also not reduce in size if there are no contiguous extents that 
are available for moving the range mappings outside the new limit. 

-----------------------------------

