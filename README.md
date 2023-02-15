lvm thin pools cannot be shrunk today.

lvreduce -L1g thinvg/p1

  Thin pool volumes thinvg/p1_tdata cannot be reduced in size yet.

This is because lvm doesn't support reduction of the thin pool data lv (tdata), since) 
the pool may not have written data linearly, and so there might be data at 
the end, i.e data chunks may be allocated at the end of the pool device 
and dm-thin does not provide defrag or some process to free it up and place it all linearly. 


This tool makes thinpool shrink possible, since it examines thin pool metadata mappings and moves single and range mappings beyond the new size, to free space within the new limit. Once the mappings are moved to free ranges or blocks inside the new  limit, the pool can be safely reduced.

Run this script on inactive pools with all its thinlvs unmounted.

Usage:
./thin_shrink -L new_size -t vgname/poolname

At the end of the run, you will have a deactivated thin pool reduced to the size you specified, if reduce was possible [1]

[1] The pool will not reduce in size if the new size is lesser than the number of
mapped blocks in the pool. The pool will also not reduce if there is a lack of equal contiguous extents to 
accomodate range mappings that needs moving. (range mappings will be split in the future - TODO)

---------------------

This work has been used as a reference for a rust based implementation of thin_shrink https://github.com/jthornber/thin-provisioning-tools/blob/main/src/commands/thin_shrink.rs

(upstream commit mentioning this project - https://github.com/jthornber/thin-provisioning-tools/commit/b67b587a109ccdab49f9d5ca1ed90a5a8fcc9467 )
