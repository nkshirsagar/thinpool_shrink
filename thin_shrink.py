#!/usr/bin/env python
import argparse
import os
import sys
import time
import subprocess


def calculate_size_in_bytes(size):
    units = size[-1]
    if (units == 'M') or (units == "m"):
        size_without_units = size[:-1]
        size_in_bytes = long(size_without_units) * 1024 * 1024
        return long(size_in_bytes)

    if (units == 'G') or (units == "g"):
        size_without_units = size[:-1]
        size_in_bytes = long(size_without_units) * 1024 * 1024 * 1024
        return long(size_in_bytes)

    if (units == 'T') or (units == "t"):
        size_without_units = size[:-1]
        size_in_bytes = long(size_without_units) * 1024 * 1024 * 1024 * 1024
        return long(size_in_bytes)

    if units == 'k':
        size_without_units = size[:-1]
        size_in_bytes = long(size_without_units) * 1024
        return long(size_in_bytes)
 
def activate_pool(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -ay " + pool_name
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))

def deactivate_pool(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -an " + pool_name
    #print cmd_to_run
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))

def activate_metadata_readonly(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -ay " + pool_name + "_tmeta -y >/dev/null 2>&1"
    #print cmd_to_run
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))


def deactivate_metadata(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -an " + pool_name + "_tmeta "
    #print cmd_to_run
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))

def thin_dump_metadata(pool_name):
    cmd_to_run = "thin_dump /dev/" + pool_name + "_tmeta" + " > /tmp/dump"
    #print cmd_to_run
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))

def thin_rmap_metadata(pool_name, nr_chunks_str):
    cmd_to_run = "thin_rmap --region 0.." + nr_chunks_str + " /dev/" + pool_name + "_tmeta" + " > /tmp/rmap"
    #print cmd_to_run
    #os.system(cmd_to_run)
    result = subprocess.call(cmd_to_run, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd_to_run))

def get_nr_chunks():
    with open('/tmp/dump') as f:
      first_line = f.readline() 
      #print first_line  
      nr_blocks_string = first_line.rpartition("=")[-1]
      #print nr_blocks_string
      nr_blocks_str = nr_blocks_string.rstrip()[1:-2]
      return nr_blocks_str


def create_shrink_device(pool_name):
    split_vg_and_pool = pool_name.split('/')
    vgname = split_vg_and_pool[0]
    poolname = split_vg_and_pool[1]
    #print vgname
    #print poolname
    search_in_dmsetup = vgname + "-" + poolname + "_tdata"
    cmd = "dmsetup table | grep " + search_in_dmsetup 
    #print cmd
    #os.system(cmd)
    result = subprocess.check_output(cmd, shell=True)

    #with open('/tmp/dmsetup_table_grepped', 'r') as myfile:
    #print dmsetup_lines
    #myfile.close()
    dmsetup_lines = result.splitlines()
    dmsetup_cmd = "echo -e " 
    for line_iter in range(0, len(dmsetup_lines)):
        split_dmsetup_line = dmsetup_lines[line_iter].split(':' , 1)
        #print split_dmsetup_line[1]
        dmsetup_table_entry_of_tdata = split_dmsetup_line[1].lstrip()
        #print dmsetup_table_entry_of_tdata
        if (line_iter > 0):
            dmsetup_cmd = dmsetup_cmd + "\\" + "\\" + "n"
        dmsetup_cmd = dmsetup_cmd + "\'" + dmsetup_table_entry_of_tdata.rstrip() + "\'"
            
    dmsetup_cmd = dmsetup_cmd + " |" + " dmsetup create shrink_" + poolname.rstrip()
    #print "running this command.. "
    #print dmsetup_cmd
    #os.system(dmsetup_cmd)
    result = subprocess.call(dmsetup_cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (dmsetup_cmd))

    name_of_device = "shrink_" + poolname.rstrip()
    #print "also running dmsetup table"
    #cmd2 = "dmsetup table"
    #os.system(cmd2)
    return name_of_device


def get_chunksize(pool_name):
    cmd = "lvs -o +chunksize " + pool_name + " | grep -v Chunk" 
    #print "running this cmd now... \n" 
    #print cmd
    #os.system(cmd)

    result = subprocess.check_output(cmd, shell=True)

    #with open('/tmp/chunksize', 'r') as myfile:
    chunk_line = result
    #print chunk_line
    chunksz_string = chunk_line.lstrip().rpartition(" ")[-1].rstrip()
    units = chunksz_string[-1]
    chunksz = chunksz_string[:-1]
    chunksz = chunksz[:chunksz.index('.')]
    # now that we removed the decimal part, add back the units
    chunksz_string = chunksz + units
    return chunksz_string


def get_total_mapped_blocks(pool_name):
    split_vg_and_pool = pool_name.split('/')
    vgname = split_vg_and_pool[0]
    poolname = split_vg_and_pool[1]
    search_in_dmsetup_silently = vgname + "-" + poolname + "-tpool >/dev/null 2>&1"
    search_in_dmsetup = vgname + "-" + poolname + "-tpool"
    cmd = "dmsetup status " + search_in_dmsetup_silently 
    #print cmd
    #os.system(cmd)

    #first test if command will run and not throw CalledProcessError exception

    result = subprocess.call(cmd, shell=True)

    if(result != 0): #no vgname-poolname-tpool in dmsetup status
        print "Warning: No tpool device found, perhaps pool has no thins?"
        search_in_dmsetup = vgname + "-" + poolname 
        search_in_dmsetup_quietly = vgname + "-" + poolname + " >/dev/null 2>&1" 
        cmd = "dmsetup status " + search_in_dmsetup_quietly
        #print cmd
        #os.system(cmd)
        result = subprocess.call(cmd, shell=True)
        if(result==0):
            #print "found pool"
            cmd = "dmsetup status " + search_in_dmsetup
            result = subprocess.check_output(cmd, shell=True)
        else:
            print "did not find pool in dmsetup status"
            exit()

        dmsetup_line = result.splitlines()
        if(len(dmsetup_line)>1): #this should never happen anyway
            print "More than 1 device found in dmsetup status"
            exit()

        # eg: RHELCSB-test_pool: 0 20971520 thin-pool 0 4356/3932160 0/163840 - rw no_discard_passdown queue_if_no_space - 1024 
        split_dmsetup_line = dmsetup_line[0].split(' ')
        dmsetup_status_entry = split_dmsetup_line[5].lstrip()
        used_blocks = dmsetup_status_entry.split('/')[0]


    else: # there is tpool

        cmd = "dmsetup status " + search_in_dmsetup
        result = subprocess.check_output(cmd, shell=True)
        
        dmsetup_line = result.splitlines()
        if(len(dmsetup_line)>1): #this should never happen anyway
            print "More than 1 device found in dmsetup status"
            exit()
        split_dmsetup_line = dmsetup_line[0].split(' ')
        dmsetup_status_entry = split_dmsetup_line[5].lstrip()
        used_blocks = dmsetup_status_entry.split('/')[0]

    #print "used blocks are.."
    #print used_blocks
    return long(used_blocks)
        
def replace_chunk_numbers_in_xml(chunks_to_shrink_to, all_changes):
    search_snapshots = 0
    count = 0
    #logfile.write("length of list of changes required is..\n")
    #logfile.write(len(changed_list))
    new_xml = open('/tmp/changed.xml', 'w')
    split_ranges_changed_list = all_changes[0]

    changed_list = all_changes[1]
    wroteline = 0

    with open('/tmp/dump') as f:
        for line in f:
            if (count == 0): # only do this for the first line, change nr_chunks
                count=1
                first_line = line
                first_line_fields = first_line.split()
                #print first_line_fields
                nr_blocks_field = first_line_fields[7]
                #print nr_blocks_field
                new_line_first_part=""
                for element in first_line_fields[0:-1]:
                    new_line_first_part = new_line_first_part + " " + element
                #print new_line_first_part
                complete_first_line = new_line_first_part + " " + "nr_data_blocks=" + "\"" + str(chunks_to_shrink_to) + "\"" + ">" + "\n"
                #print complete_first_line
                complete_first_line = complete_first_line.lstrip()
                new_xml.write(complete_first_line)

            else:
                data_found = line.find("data_")

                if (data_found > 0):
                    split_line = line[data_found:]
                    last_quotes = split_line.index(" ")
                    blocknum = split_line[12:last_quotes-1]
                    int_block = int(blocknum)
                   
                    if(split_ranges_changed_list.get(int_block,0) == 0): # is this block number not a key in split ranges ?
		        if(changed_list.get(int_block,0) == 0): #is this block number not a key in changed list ?

                            if(search_snapshots==1):
                            # it may also be a snapshot mapping pointing to inside a range that we may be moving!
                                if(len(changed_list)>0):
                                    #print changed_list
                                    
                                    candidates = []
                                    for keys in changed_list:
                                        #print "integer value of keys is"
                                        #print int(keys)
                                        #print "and in_block is"
                                        #print int_block
                                        if( int(keys) < int_block):
                                            candidates.append(keys)
                                    
                                    if(len(candidates)>0):
                                        closest_earlier = max(candidates)
                                        closest_smaller_key = changed_list[closest_earlier]
                                        #print closest_smaller_key

                                        #return d[str(max(key for key in map(int, d.keys()) if key <= k))]
                                        #return sample[str(max(x for x in sample.keys() if int(x) < int(key)))]

                                        closest_range = changed_list[closest_smaller_key]

                                        # if this block lies inside the range we are moving to another range
                                        if( (int_block > closest_range[0]) and ( int_block < ( int(closest_range[0]) + int(closest_range[1]) ) )):
                                            #if(int_block < (int(closest_range[0]) + int(closest_range[1])):
                                            # yes this is a snapshot mapping pointing to inside a range we are moving
			                    first_part_string = line[0:data_found+12]
		    	                    last_part_string = split_line[last_quotes+1:]
                                            changed_snap_blocknum = int(closest_range[0]) + (int_block - int(closest_smaller_key))
                                            new_string = first_part_string +  str(changed_snap_blocknum) + "\" " + last_part_string
			                    new_xml.write(line)
                                            wroteline = 1
 
                                # it may also be a snapshot mapping pointing to inside a SPLIT range we are moving !! 
                                if( (len(split_ranges_changed_list)>0) and (wroteline == 0)):
                                    candidates = []
                                    for keys in split_ranges_changed_list:
                                        if( int(keys) < int_block):
                                            candidates.append(keys)
                                    if(len(candidates)>0):
                                        closest_smaller_key = split_ranges_changed_list[max(candidates)]
                                        closest_range = split_ranges_changed_list[closest_smaller_key]
                                        if((int_block > closest_range[0]) and (int_block < (int(closest_range[0]) + int(closest_range[1])))):

                                            # yes this is a snapshot mapping pointing to inside a split range we are moving
			                    first_part_string = line[0:data_found+12]
		    	                    last_part_string = split_line[last_quotes+1:]
                                            changed_snap_blocknum = int(closest_range[0]) + (int_block - int(closest_smaller_key))
                                            new_string = first_part_string +  str(changed_snap_blocknum) + "\" " + last_part_string
			                    new_xml.write(line)
                                            wroteline = 1

                                if(wroteline == 0):    
			            # write the unmodified line as it is
			            new_xml.write(line)

                            else:    
                                # dont bother with snapshots, assume none exist 
			        # write the unmodified line as it is
			        new_xml.write(line)

		        else: # its in changed list
			    to_change = changed_list[int_block]
			    first_part_string = line[0:data_found+12]
		    	    last_part_string = split_line[last_quotes+1:]
			    new_string = first_part_string +  str(to_change[0]) + "\" " + last_part_string 
			    #print new_string
			    new_xml.write(new_string)

                    else: #its in the split ranges
                        # change line of xml for first and generates lines for all lookaheads

                        #  <range_mapping origin_begin="63962" data_begin="817969" length="26" time="0"/>
                        

                        to_change = split_ranges_changed_list[int_block]
                        first_part_string = line[0:data_found+12]
                        last_part_string = split_line[last_quotes+1:]
                        #   last_part_string is now looking like 
                        #   length="26" time="0"/>
                        
                        #length needs reducing
                        split_last_line = last_part_string.split(" ")
                        
                        new_string = first_part_string +  str(to_change[0]) + "\" " + "length=\"" + str(to_change[1])  + "\" " + split_last_line[1]
                        #print new_string
                        new_xml.write(new_string)
                       
                        # now do the lookaheads
                        new_block = int_block 
                        origin_block =0
                        split_first_part = first_part_string.split("=")
                       
                        origin_string = split_first_part[1].split(" ")[0] # "63962"
                        origin = origin_string[1:-1]
                        int_origin = int(origin)
                        #print int_origin
                        time_string = line.split(" ")[-1]
                        new_origin = int_origin
                        spaces_before_string = line[0:line.index('<')]
                        #print to_change
                        while to_change[2]==1: #while lookahead
                            new_block = new_block + to_change[1] 
                            new_origin = new_origin + int(to_change[1])
                            to_change = split_ranges_changed_list[new_block]

                            #     <range_mapping origin_begin="63962" data_begin="817969" length="26" time="0"/>
                            #     <single_mapping origin_block="63960" data_block="767381" time="0"/>

                            if(to_change[1]>1): #range mapping
                                new_string = spaces_before_string +  "<range_mapping origin_begin=\"" + str(new_origin) + " data_begin=\"" + str(new_block) + "\" length=" + "\"" + str(to_change[1]) + "\" " + time_string
                                new_xml.write(new_string) 
                            else:
                                if(to_change[1]==1): #single mapping
                                    new_string = spaces_before_string + "<single_mapping origin_block=\"" + str(new_origin) + " data_block=\"" + str(new_block) + "\" " + time_string
                                    new_xml.write(new_string) 
                                else:
                                    print "This should never happen. size of mapping seems 0"


                else:
                    new_xml.write(line)


        new_xml.close()
        f.close()

###########################
        #cleanup()
        #exit()
###########################
    
        
def change_xml(chunks_to_shrink_to, chunksize_in_bytes, needs_dd=0):
    #print "in change xml"
    if (needs_dd == 0):
        # we only need to change the nr_blocks in the xml
        with open('/tmp/dump') as f:
            first_line = f.readline()
            first_line_fields = first_line.split()
            #print first_line_fields
            nr_blocks_field = first_line_fields[7]
            #print nr_blocks_field
            new_line_first_part=""
            for element in first_line_fields[0:-1]:
                new_line_first_part = new_line_first_part + " " + element
            #print new_line_first_part
            complete_first_line = new_line_first_part + " " + "nr_data_blocks=" + "\"" + str(chunks_to_shrink_to) + "\"" + ">" + "\n"
            #print complete_first_line
            complete_first_line = complete_first_line.lstrip()
            new_xml = open('/tmp/changed.xml', 'w')     
            new_xml.write(complete_first_line)
            remaining = f.readlines()
            type(remaining)
            for i in range(0, len(remaining)):       
                new_xml.write(remaining[i]) 
            new_xml.close()
    else:
        # we need to dd blocks, change the numbers in the xml, etc            
        print "Checking if blocks can be copied"
        allocated_ranges = []
        free_ranges = []
        earlier_element=[]
        ranges_requiring_move = []

        #changed_list = [] # [(old, new, length) , (old, new, length), ... ]

        split_ranges_changed_list= {} # {old:[new,len,lookahead} note that lookahead is bool i.e 1 or 0
        changed_list = {} # {old: [new,len] , old: [new,len], ... }
        total_blocks_requiring_copy = 0

        with open('/tmp/rmap') as f:
            entire_file = f.readlines()
            type(entire_file)
            for i in range(0,len(entire_file)):
                mapping = entire_file[i].split()[1]
                split_mapping = mapping.split(".")
                start_block = split_mapping[0]
                end_block = split_mapping[-1]
                length_of_mapping = int(end_block) - int(start_block)
                range_to_add = []
                range_to_add.append(int(start_block))
                range_to_add.append(length_of_mapping)
                allocated_ranges.append(range_to_add)
                if(int(start_block) + length_of_mapping > chunks_to_shrink_to):
                    ranges_requiring_move.append(range_to_add)

                if (i == 0): # first iteration 
                    earlier_element = range_to_add
                    if(start_block > 0):
                        if(int(start_block) < chunks_to_shrink_to): #if starting block is within the new size
                            free_range_element = []
                            free_range_element.append(0)
                            free_range_element.append(int(start_block))
                            if((free_range_element[0] + free_range_element[1]) < chunks_to_shrink_to): #if entire free range is within new size
                                free_ranges.append(free_range_element)    
                                #earlier_element = range_to_add
                            else:
                                free_range_element.pop(1) #get rid of older length, needs trimming
                                free_range_element.append(chunks_to_shrink_to - (earlier_element[0])) #length of free range that will fit within new size
                                free_ranges.append(free_range_element)

                else: 

                    #iteration 1 onwards, start creating free_ranges list also

                    if (int(start_block) > (earlier_element[0] + earlier_element[1]) ):
                        if(int(start_block) < chunks_to_shrink_to): #if starting block is within the new size
                            # we have a free range, so add it to the free_ranges list
                            free_range_element = []
                            free_range_element.append(earlier_element[0] + earlier_element[1]) #start of free range
                            free_range_element.append(int(start_block) - (earlier_element[0] + earlier_element[1])) #length of free range

                            if((free_range_element[0] + free_range_element[1]) < chunks_to_shrink_to): #if entire free range is within new size
                                free_ranges.append(free_range_element)    
                                #earlier_element = range_to_add
                            else:
                                free_range_element.pop(1) #get rid of older length, needs trimming
                                free_range_element.append(chunks_to_shrink_to - (earlier_element[0])) #length of free range that will fit within new size
                                free_ranges.append(free_range_element)
                earlier_element = range_to_add                  

            #print "\nallocated ranges are.."
            #print allocated_ranges 

            ##########################################
            # used for testing split ranges
            #free_ranges = [[1,1],[200,300],[700,400],[1200,500]]
            #ranges_requiring_move = [[3000,600], [5000,550]]
            ##########################################

            free_ranges.sort(key=lambda x: x[1])
            #print "\nsorted free ranges are"
            #print free_ranges
            
            ranges_requiring_move.sort(key=lambda x: x[1], reverse=True)
            #print "\nranges requiring move are"
            #print ranges_requiring_move

            #print "length of list of free ranges is..\n"
            #print len(free_ranges)
  

            total_needing_copy = sum(need_copy[1] for need_copy in ranges_requiring_move)
            total_free = sum(available_free[1] for available_free in free_ranges)
            #print "total needing copy is"
            #print total_needing_copy
            #print "total free is"
            #print total_free

            if(total_needing_copy > total_free):
                print "this pool cannot be shrunk because not enough free blocks available" 
                print "total needing copy is"
                print total_needing_copy
                print "total free is"
                print total_free
                changed_list = {}
                return changed_list


            # at this point, we know that we can shrink the pool 

            #print "free ranges are"
            #print free_ranges
            #print "ranges requiring move are"
            #print ranges_requiring_move

            for each_range in ranges_requiring_move:
                len_requiring_move = each_range[1]
                #print len_requiring_move
                could_split=0
                this_range_has_fit=0   
                # find out if it needs splitting
 
                if(len_requiring_move > free_ranges[-1][1]):
                    print "This one will need splitting. the range to move is"
                    print each_range
                    print "the free ranges "
                    print free_ranges
                    #old_block = each_range[0]
                    reversed_free_ranges = reversed(free_ranges) 
                    moved = 0
                    split_range = []
                    for iterate_free_backwards in reversed_free_ranges:
                        if(iterate_free_backwards[1] < len_requiring_move): #if we must use this entire range
                            split_range.append(iterate_free_backwards[0]) 
                            split_range.append(iterate_free_backwards[1])
                            split_range.append(1)

                            index = each_range[0]  + moved
                            split_ranges_changed_list[index]=split_range

                            # split_ranges_changed_list looks like this
                            # [old: new,len,lookahead] , lookahead is 0 or 1 and specifies to look ahead to generate xml for next
                            #  element in split_ranges_changed_list too because you wont find that one in the xml in blocks to change since its 
                            # from the  middle of a range that you split.

                            total_blocks_requiring_copy = total_blocks_requiring_copy + split_range[1]
                            moved = moved + split_range[1]

                            free_ranges.pop()
                            len_requiring_move = len_requiring_move - split_range[1]

                        else:
                            this_range_has_fit = 1
                            # partial free range to accomodate last remaining part of large range
                            split_range = []
                            split_range.append(iterate_free_backwards[0])
                            split_range.append(len_requiring_move)
                            split_range.append(0)
                            index = each_range[0] + moved
                            split_ranges_changed_list[index]=split_range

                            #adjust the free ranges
                            #remove first from free ranges
                            last_one = free_ranges.pop()
                            #add back with changed free map unless it was completely consumed
 
                            if(len_requiring_move < last_one[1]):
                                temp_free_range = []
                                blknum = last_one[0]
                                new_blknum = blknum + len_requiring_move
                                print new_blknum

                                temp_free_range.append(new_blknum)
                                len_changed = last_one[1]
                                changed_len = len_changed - len_requiring_move
                                #print changed_len
                                temp_free_range.append(changed_len)
                                print "temp free range is is."
                                print temp_free_range
                                print free_ranges
                                free_ranges.append(temp_free_range)
                                print free_ranges
                                #sort it again, so this element is put in proper place
                                free_ranges.sort(key=lambda x: x[1])
                                total_blocks_requiring_copy = total_blocks_requiring_copy + len_requiring_move
                                print "done splitting this range"
                                print "free ranges are now"
                                print free_ranges
                                print "and split ranges changed list is "
                                print split_ranges_changed_list
                                break
                
                else: 
                    #find closest fitting free range I can move this to
                    for i in range(len(free_ranges)):
                        if free_ranges[i][1] > len_requiring_move:
                            #found free range to move this range to
                            #print "range mapping of size"
                            #remove that entry from the free ranges list, we will add it back with the reduced length later
                            changed_element = []
                            #changed_element.append(each_range[0])
                            changed_element.append(free_ranges[i][0])
                            changed_element.append(len_requiring_move)
                            total_blocks_requiring_copy = total_blocks_requiring_copy + len_requiring_move
                            changed_list[each_range[0]] = changed_element
                            #changed_list.append(changed_element)

                            if((free_ranges[i][1] - len_requiring_move) > 0):
                                new_free_range = []
                                new_free_range_block = free_ranges[i][0]+len_requiring_move
                                new_range_length = free_ranges[i][1] - len_requiring_move
                                new_free_range.append(new_free_range_block)
                                new_free_range.append(new_range_length)
                                free_ranges.pop(i)
                                free_ranges.append(new_free_range)
                                #sort it again, so this element is put in proper place
                                free_ranges.sort(key=lambda x: x[1])
                                break

            print "\nlength of change list is.."
            print len(changed_list)                         
            print "\nlength of split range list is.."
            print len(split_ranges_changed_list)                         

            #make a list that stores both the lists, split_ranges_changed_list and changed_list
            all_changes = []
            all_changes.append(split_ranges_changed_list)
            all_changes.append(changed_list)

            #if(len(changed_list) == len(ranges_requiring_move)):
            print "This pool can be shrunk, but blocks will need to be moved."
            total_gb = ( float(total_blocks_requiring_copy) * float(chunksize_in_bytes) ) / 1024 / 1024 /1024
            print ("Total amount of data requiring move is %.2f GB. Proceed ? Y/N" % (total_gb))
            if sys.version_info[0]==2:
                inp = raw_input()
            else: # assume python 3 onward
                inp = input()

            if(inp.lower() == "y"):
                
                replace_chunk_numbers_in_xml(chunks_to_shrink_to ,all_changes) 
                return all_changes
            else:
                print "Aborting.."
                zero_list = [] 
                return zero_list

def check_pool_shrink_without_dd(chunks_to_shrink_to):
    if(os.path.exists('/tmp/rmap')):
        if(os.path.getsize('/tmp/rmap') > 0):
            with open('/tmp/rmap') as f:
              for line in f:
                pass
              last_line = line 
              #print last_line
              last_range = last_line.split()[1]
              #print last_range
              last_block = last_range.split(".")[2]
              last_block_long = long(last_block)
              if ((last_block_long - 1) < chunks_to_shrink_to):
                  print "Pool can be shrunk without moving blocks. Last mapped block is %d and new size in chunks is %d\n" % ((last_block_long - 1), chunks_to_shrink_to )
                  return 1
              else:
                  print "Last mapped block is %d and new size in chunks is %d\n" % ((last_block_long - 1), chunks_to_shrink_to )
                  return 0
            
        print "no valid /tmp/rmap file found. Perhaps this pool has no data mappings ?"
        return 1
            
def restore_xml_and_swap_metadata(pool_to_shrink):
    #need to create a new lv as large as the metadata
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    lvname = vg_and_lv[1]
    #print vgname
    #print lvname
    #search for the tmeta size in lvs -a
    cmd = "lvs -a | grep " + "\"" + " " + vgname + " \" " + "|" + " grep " + "\"" + "\\" +  "[" + lvname + "_tmeta]\"" 
    #print cmd
    #os.system(cmd)
    result = subprocess.check_output(cmd, shell=True)
    tmeta_line = result
    #print tmeta_line
    size_of_metadata = tmeta_line.split()[-1]
    #print size_of_metadata
    units = size_of_metadata[-1]
    meta_size = size_of_metadata[:-1]
    meta_size = meta_size[:meta_size.index('.')]
    meta_size_str = meta_size + units
    #print meta_size_str
    cmd = "lvcreate -n shrink_restore_lv -L" + meta_size_str + " " + vgname + " >/dev/null 2>&1"
    print cmd
    #os.system(cmd)

    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))
    else:
        print "ran the command"

    cmd = "thin_restore -i /tmp/changed.xml -o " + "/dev/" + vgname + "/" + "shrink_restore_lv"
    print cmd
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))

    #os.system(cmd)
    cmd = "lvconvert --thinpool " + pool_to_shrink + " --poolmetadata " + "/dev/" + vgname + "/shrink_restore_lv -y"
    #print cmd
    #os.system(cmd)
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))
    
def change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    lvname = vg_and_lv[1]
    #print vgname
    #print lvname
    cmd = "vgcfgbackup -f /tmp/vgmeta_backup " + vgname  + " >/dev/null 2>&1"
    #print cmd
    #os.system(cmd)
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))

    with open('/tmp/vgmeta_backup') as f:
        new_vgmeta = open('/tmp/changed_vgmeta', 'w')

        remaining = f.readlines()
        type(remaining)
        search_string = " " + lvname + " {"
        #print search_string
        #print "***"
        extent_size_string = "extent_size = "
        extent_size_in_bytes=0
        dont_look_any_more = 0
        found_search_string = 0
        found_logical_volumes = 0
        for i in range(0, len(remaining)):
            if dont_look_any_more == 0:
                if ( remaining[i].find(extent_size_string) != -1 ):
                    extent_elements = remaining[i].split()
                    #print extent_elements

                    extent_size_figure = extent_elements[-2]
                    extent_size_units = extent_elements[-1][0]
                    extent_size = extent_size_figure+extent_size_units
                    #print "extent size is.. "
                    #print extent_size
                    #print "\n and in bytes .. "
                    extent_size_in_bytes = calculate_size_in_bytes(extent_size)
                    #print extent_size_in_bytes
             
                if (remaining[i].find("logical_volumes {") != -1): 
                    found_logical_volumes = 1
                    #print "found the logical volumes"
                
                if ((" " + remaining[i].lstrip()).find(search_string) != -1): 
                    if(found_logical_volumes == 1):
                      found_search_string = 1
                      #print "found the search string"

                if (remaining[i].find("extent_count") != -1): 
                    if(found_search_string == 1):
                        #print "found the extent count"
                        num_tabs = remaining[i].count('\t')
                        #print "number of tabs is "
                        #print num_tabs
                        
                        num_whitespaces = len(remaining[i]) - len(remaining[i].lstrip())
                        #print num_whitespaces
                        elements = remaining[i].split()
                        new_size = (chunks_to_shrink_to * chunksize_in_bytes) / extent_size_in_bytes
                        #print "number of extents to shrink to is "
                        #print new_size
                        new_string = "extent_count = " + str(new_size) + "\n" 
                        #new_string_len = len(new_string) + num_whitespaces
                        #new_string_with_trailing_spaces = new_string.rjust(new_string_len)
                        new_string_with_tabs=new_string
                        for x in range(0,num_tabs-1):
                            new_string_with_tabs = "\t" + new_string_with_tabs 
                        new_vgmeta.write(new_string_with_tabs)
                        dont_look_any_more = 1
                        continue

            new_vgmeta.write(remaining[i])
        new_vgmeta.close()



def restore_vg_metadata(pool_to_shrink):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    lvname = vg_and_lv[1]
    cmd = "vgcfgrestore -f /tmp/changed_vgmeta " + vgname + " --force -y >/dev/null 2>&1"
    #os.system(cmd)
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))


def move_blocks(combined_changed_list,shrink_device,chunksize_string):
    progress=0
    percent_done = 0
    previous_percent = 0
    counter = 0
    print "Generated new metadata map. Now copying blocks to match the changed metadata."        
    split_ranges_list = combined_changed_list[0]
    changed_list = combined_changed_list[1]

    for changed_entry in split_ranges_list: # move split ranges first
        progress=progress+1
        counter = counter + 1
    
        old_block = changed_entry
        new_block = split_ranges_list[changed_entry][0]
        length = split_ranges_list[changed_entry][1]
        bs = chunksize_string[0:-1]
        units = chunksize_string[-1].upper()
        bs_with_units = bs + units
        #if(length>1):
         #   print ("moving %d blocks at %d to %d" % (length , old_block , new_block) )
        #else:
         #   print ("moving %d block at %d to %d" % (length , old_block , new_block) )

        cmd = "dd if=/dev/mapper/" + shrink_device + " of=/dev/mapper/" + shrink_device + " bs=" + bs_with_units + " skip=" + str(old_block) + " seek=" + str(new_block) + " count=" + str(length) + " conv=notrunc >/dev/null 2>&1"
        #print cmd
        #os.system(cmd)
        result = subprocess.call(cmd, shell=True)
        if(result != 0):
            print ("could not run cmd %s" % (cmd))

        one_tenth = len(split_ranges_list) / 10
        if(progress  == one_tenth):
            print("%d moved of %d elements" % (counter, len(split_ranges_list)))
            progress=0


    for changed_entry in changed_list:

        progress=progress+1
        counter = counter + 1
        
        old_block = changed_entry
        new_block = changed_list[changed_entry][0]
        length = changed_list[changed_entry][1]
        bs = chunksize_string[0:-1]
        units = chunksize_string[-1].upper()
        bs_with_units = bs + units
        #if(length>1):
         #   print ("moving %d blocks at %d to %d" % (length , old_block , new_block) )
        #else:
         #   print ("moving %d block at %d to %d" % (length , old_block , new_block) )

        cmd = "dd if=/dev/mapper/" + shrink_device + " of=/dev/mapper/" + shrink_device + " bs=" + bs_with_units + " skip=" + str(old_block) + " seek=" + str(new_block) + " count=" + str(length) + " conv=notrunc >/dev/null 2>&1"
        #print cmd
        #os.system(cmd)
        result = subprocess.call(cmd, shell=True)
        if(result != 0):
            print ("could not run cmd %s" % (cmd))

        one_tenth = len(changed_list) / 10 
        if(progress  == one_tenth):
            print("%d moved of %d elements" % (counter, len(changed_list)))
            progress=0

    print "Done with data copying"        

def cleanup(shrink_device, pool_to_shrink):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    cmd = "dmsetup remove " + shrink_device
    #os.system(cmd)
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))

    cmd = "lvremove " + vgname + "/shrink_restore_lv >/dev/null 2>&1"
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))

    #os.system(cmd)
    cmd = "lvchange -an " + pool_to_shrink
    #os.system(cmd)
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))

    
def delete_restore_lv(pool_to_shrink):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    cmd = "lvremove " + vgname + "/shrink_restore_lv"
    result = subprocess.call(cmd, shell=True)
    if(result != 0):
        print ("could not run cmd %s" % (cmd))
    #os.system(cmd)

#TODO close opened files


def main():

    #logfile = open("/tmp/shrink_logs", "w")
    #logfile.write("starting logs")
    ap = argparse.ArgumentParser()
    ap.add_argument("-L", "--size",  required=True, help="size to shrink to")
    ap.add_argument("-t", "--thinpool", required=True, help="vgname/poolname")
    args = vars(ap.parse_args())

    size_in_chunks=0L
    pool_to_shrink = args['thinpool']
   
    #delete_restore_lv(pool_to_shrink)
    activate_pool(pool_to_shrink)
    total_mapped_blocks = get_total_mapped_blocks(pool_to_shrink)

    shrink_device = create_shrink_device(pool_to_shrink)

    chunksz_string = get_chunksize(pool_to_shrink)
    chunksize_in_bytes =  calculate_size_in_bytes(chunksz_string)

    deactivate_pool(pool_to_shrink)
    activate_metadata_readonly(pool_to_shrink)
    thin_dump_metadata(pool_to_shrink)

    nr_chunks = get_nr_chunks()
    #print nr_chunks

    thin_rmap_metadata(pool_to_shrink, nr_chunks)
    deactivate_metadata(pool_to_shrink)
  
    size_to_shrink = args['size']
    size_to_shrink_to_in_bytes = 0L
    size_to_shrink_to_in_bytes = calculate_size_in_bytes(size_to_shrink)
    #print size_to_shrink_to_in_bytes
    chunks_to_shrink_to = size_to_shrink_to_in_bytes/chunksize_in_bytes
    print "Need to shrink pool to number of chunks - " + str(chunks_to_shrink_to)

    if(chunks_to_shrink_to >= int(nr_chunks)):
        print "This thin pool cannot be shrunk. The pool is already smaller than the size provided."
        cleanup(shrink_device,pool_to_shrink)
        exit()

    if (total_mapped_blocks >= chunks_to_shrink_to):
        print "This thin pool cannot be shrunk. The mapped chunks are more than the lower size provided. Discarding allocated blocks from the pool may help."
        cleanup(shrink_device,pool_to_shrink)
        exit()

    if( check_pool_shrink_without_dd(chunks_to_shrink_to) == 1):
        change_xml(chunks_to_shrink_to, chunksize_in_bytes)
        restore_xml_and_swap_metadata(pool_to_shrink)
        change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes)
        restore_vg_metadata(pool_to_shrink)
        cleanup(shrink_device,pool_to_shrink)
        print("\nThis pool has been shrunk to the specified size of %s" % (size_to_shrink))

    else:

        changed_list = change_xml(chunks_to_shrink_to, chunksize_in_bytes, 1)
        if(len(changed_list) > 0):
            move_blocks(changed_list,shrink_device,chunksz_string)
            restore_xml_and_swap_metadata(pool_to_shrink)
            change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes)
            restore_vg_metadata(pool_to_shrink)
            print("\nThis pool has been shrunk to the specified size of %s" % (size_to_shrink))
        cleanup(shrink_device,pool_to_shrink)

    #change_xml(114688,65536,1)

if __name__=="__main__": 
    main() 
