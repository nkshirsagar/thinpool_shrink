There are 2 reasons why lvm thin pools cannot be shrunk today.

a) The pool may not have written data linearly, and so there might be data at 
the end, i.e data chunks may be allocated at the end of the pool device 
and dm-thin does not provide scrubbing to free it up

b) lvm doesn't support reduction of the thin pool data lv (tdata)

This script examines thin pool metadata mappings and moves single and range 
mappings from the end of the size to reduce to, towards the beginning. It is not
really a true "defrag" since it only does this for the mappings outside the 
limit specified by the new size.

However, once the mappings are moved to free ranges or blocks inside the new 
limit, the pool can be safely reduced. 

The script takes care of changing the thinpool  as well as the VG metadata, 
and does the necessary thin and VGcfg restores.

Run this script on deactivated and unmounted thin pools, this is an offline
reduction, not online.

At the end of the run, you will have a deactivated thin pool (hopefully) 
reduced to the size you specified.

Usage:
./thin_shrink -L new_size -t vgname/poolname

The pool will not reduce in size if the new size is lesser than the number of
mapped blocks in the pool.

The pool will also not reduce in size if there is no contiguous extents that 
are available for moving the range mappings outside the new limit. 
thin_shrink will not break up range mappings and convert them to single mappings
to overcome this constraint. (Maybe in future versions)

The new_size specified with -L doesn't take decimals, so use M, G or T appropriately to come 
close to the size you want to reduce to. Also, the size needs to be a multiple of PV extent size.


