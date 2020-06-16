#!/usr/bin/env python
import argparse
import os

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
    os.system(cmd_to_run)

def deactivate_pool(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -an " + pool_name
    print cmd_to_run
    os.system(cmd_to_run)

def activate_metadata_readonly(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -ay " + pool_name + "_tmeta -y"
    print cmd_to_run
    os.system(cmd_to_run)


def deactivate_metadata(pool_name):
    #print pool_name
    cmd_to_run = "lvchange -an " + pool_name + "_tmeta "
    print cmd_to_run
    os.system(cmd_to_run)

def thin_dump_metadata(pool_name):
    cmd_to_run = "thin_dump /dev/" + pool_name + "_tmeta" + " > /tmp/dump"
    print cmd_to_run
    os.system(cmd_to_run)

def thin_rmap_metadata(pool_name, nr_chunks_str):
    cmd_to_run = "thin_rmap --region 0.." + nr_chunks_str + " /dev/" + pool_name + "_tmeta" + " > /tmp/rmap"
    print cmd_to_run
    os.system(cmd_to_run)

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
    cmd = "dmsetup table | grep " + search_in_dmsetup + " > /tmp/dmsetup_table_grepped"
    #print cmd
    os.system(cmd)
    with open('/tmp/dmsetup_table_grepped', 'r') as myfile:
      dmsetup_line = myfile.read()
    #print dmsetup_line
    myfile.close()
    os.remove('/tmp/dmsetup_table_grepped')
    split_dmsetup_line = dmsetup_line.split(':' , 1)
    #print split_dmsetup_line[1]
    dmsetup_table_entry_of_tdata = split_dmsetup_line[1].lstrip()
    #print dmsetup_table_entry_of_tdata
    dmsetup_cmd = "dmsetup create shrink_" + poolname.rstrip() + " --table " + "\'" + dmsetup_table_entry_of_tdata.rstrip() + "\'"
    #print "running this command.. "
    print dmsetup_cmd
    os.system(dmsetup_cmd)
    name_of_device = "shrink_" + poolname.rstrip()
    return name_of_device


def get_chunksize(pool_name):
    cmd = "lvs -o +chunksize " + pool_name + " | grep -v Chunk" + " > /tmp/chunksize"
    #print "running this cmd now... \n" 
    print cmd
    
    os.system(cmd)
    with open('/tmp/chunksize', 'r') as myfile:
      chunk_line = myfile.read()
    #print chunk_line
    chunksz_string = chunk_line.lstrip().rpartition(" ")[-1].rstrip()
    units = chunksz_string[-1]
    chunksz = chunksz_string[:-1]
    chunksz = chunksz[:chunksz.index('.')]
    # now that we removed the decimal part, add back the units
    chunksz_string = chunksz + units
    return chunksz_string


def get_total_mapped_blocks():
    thin_dumped_xml_file = open("/tmp/dump", "r")
    thin_dumped_xml = thin_dumped_xml_file.read()
    
    lines_containing_mapped_blocks = [line for line in thin_dumped_xml.split('\n') if "mapped_blocks" in line]
    #print lines_containing_mapped_blocks
    #print "now calculating total mapped blocks"
    total_mapped_blocks = 0
    for line in lines_containing_mapped_blocks:
        split_line = line.split()
        mapped_blocks = split_line[2] 
        #print mapped_blocks
        num_mapped_blocks = mapped_blocks.split("=")[1] 
        #print num_mapped_blocks
        
        trimmed_mapped_blocks = num_mapped_blocks[1:-1]
        #print trimmed_mapped_blocks
        trimmed_mapped_blocks_int = int(trimmed_mapped_blocks)
        total_mapped_blocks = total_mapped_blocks + trimmed_mapped_blocks_int
        
    #print total_mapped_blocks
    return total_mapped_blocks
        
def replace_chunk_numbers_in_xml(chunks_to_shrink_to, changed_list):
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

        for xml_iter in range(0, len(remaining)):
            wrote_line = 0
            for changed_iter in changed_list:
                whether_found = remaining[xml_iter].find(str(changed_iter[0]))
                if (whether_found > 0):
                    #print "relevant line of xml is\n"
                    #print remaining[xml_iter]
                    #print whether_found
                    
                    #check if previous 12 characers are "data_begin" or "data_block=" so we rule out that number appearing in origin mappings
                    data_begin_or_block = remaining[xml_iter][whether_found-12:whether_found -1 ]
                    #print data_begin_or_block
                    if((data_begin_or_block == "data_begin=") or (data_begin_or_block == "data_block=")):
                        #we need to change the figure now after verifying
                        first_part_string = remaining[xml_iter][0:whether_found]
                        if(data_begin_or_block == "data_begin="):
                            second_index_string = remaining[xml_iter].find("length")
                        else:
                            second_index_string = remaining[xml_iter].find("time")
                        second_part_string = remaining[xml_iter][second_index_string:]
                        new_string = first_part_string +  str(changed_iter[1]) + "\" " + second_part_string 
                        #print new_string
                        new_xml.write(new_string)
                        wrote_line = 1
                        break
            if(wrote_line == 0):
                new_xml.write(remaining[xml_iter])

        new_xml.close()
        f.close()
    
        
def change_xml(chunks_to_shrink_to, needs_dd=0):
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
        print "Changes needed to metadata and blocks will be copied"
        allocated_ranges = []
        free_ranges = []
        earlier_element=[]
        ranges_requiring_move = []

        changed_list = [] # [(old, new, length) , (old, new, length), ... ]

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

                else: 
                    #print start_block
                    #print end_block
                    #print "\n printing earlier element"
                    #print earlier_element

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
                            #earlier_element = range_to_add
                    #else:
                        #earlier_element = range_to_add
                earlier_element = range_to_add                  

            print "\nallocated ranges are..\n"
            print allocated_ranges 
            #print "\nfree ranges are..\n"
            #print free_ranges
            free_ranges.sort(key=lambda x: x[1])
            print "\nsorted free ranges are\n"
            print free_ranges
            
            ranges_requiring_move.sort(key=lambda x: x[1], reverse=True)
            print "\nreverse sorted ranges requiring move are\n"
            print ranges_requiring_move
 
            for each_range in ranges_requiring_move:
                #find closest fitting free range I can move this to
                len_requiring_move = each_range[1]
                #print len_requiring_move
                #print "length of list of free ranges is..\n"
                #print len(free_ranges)
                for i in range(len(free_ranges)):
                    if free_ranges[i][1] > len_requiring_move:
                        #found free range to move this range to
                        #print "range mapping of size"
                        #remove that entry from the free ranges list, we will add it back with the reduced length later
                        changed_element = []
                        changed_element.append(each_range[0])
                        changed_element.append(free_ranges[i][0])
                        changed_element.append(len_requiring_move)
                        changed_list.append(changed_element)

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

            print "\nchange list is.."
            print changed_list                         

            if(len(changed_list) == len(ranges_requiring_move)):
                replace_chunk_numbers_in_xml(chunks_to_shrink_to ,changed_list) 
                return changed_list
            else:
                print "Cannot fit every range requiring move to free ranges. Aborting.."
                print "\nThis pool cannot be shrunk"
                changed_list = []
                return changed_list

def check_pool_shrink_without_dd(chunks_to_shrink_to):
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
            print "Yes, this pool can be shrunk. Last mapped block is %d and new size in chunks is %d\n" % ((last_block_long - 1), chunks_to_shrink_to )
            return 1
            
def restore_xml_and_swap_metadata(pool_to_shrink):
    #need to create a new lv as large as the metadata
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    lvname = vg_and_lv[1]
    #print vgname
    #print lvname
    #search for the tmeta size in lvs -a
    cmd = "lvs -a | grep " + "\"" + " " + vgname + " \" " + "|" + " grep " + "\"" + "\\" +  "[" + lvname + "_tmeta]\"" + " > /tmp/metadata_lv"
    print cmd
    os.system(cmd)
    with open('/tmp/metadata_lv', 'r') as myfile:
      tmeta_line = myfile.read()
    #print tmeta_line
    myfile.close()
    os.remove('/tmp/metadata_lv')
    size_of_metadata = tmeta_line.split()[-1]
    #print size_of_metadata
    units = size_of_metadata[-1]
    meta_size = size_of_metadata[:-1]
    meta_size = meta_size[:meta_size.index('.')]
    meta_size_str = meta_size + units
    #print meta_size_str
    cmd = "lvcreate -n restore_lv -L" + meta_size_str + " " + vgname
    print cmd
    os.system(cmd)
    cmd = "thin_restore -i /tmp/changed.xml -o " + "/dev/" + vgname + "/" + "restore_lv"
    #TODO put a check here to ensure the restore is successful
    print cmd
    os.system(cmd)
    cmd = "lvconvert --thinpool " + pool_to_shrink + " --poolmetadata " + "/dev/" + vgname + "/restore_lv -y"
    print cmd
    os.system(cmd)
    
def change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    lvname = vg_and_lv[1]
    #print vgname
    #print lvname
    cmd = "vgcfgbackup -f /tmp/vgmeta_backup " + vgname 
    print cmd
    os.system(cmd)

    with open('/tmp/vgmeta_backup') as f:
        new_vgmeta = open('/tmp/changed_vgmeta', 'w')

        remaining = f.readlines()
        type(remaining)
        search_string = " " + lvname + " {"
        extent_size_string = "extent_size = "
        extent_size_in_bytes=0
        dont_look_any_more = 0
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
                if ((remaining[i].find(search_string) != -1) and (found_logical_volumes == 1)):
                    found_search_string = 1
                if (remaining[i].find("extent_count") != -1):
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
    cmd = "vgcfgrestore -f /tmp/changed_vgmeta " + vgname + " --force -y"
    os.system(cmd)



def move_blocks(changed_list,shrink_device,chunksize_string):
    for changed_entry in changed_list:
        old_block = changed_entry[0]
        new_block = changed_entry[1]
        len = changed_entry[2]
        print ("moving %d blocks at %d to %d" % (len , old_block , new_block) )
        cmd = "dd if=/dev/mapper/" + shrink_device + " of=/dev/mapper/" + shrink_device + " bs=" + chunksize_string + " skip=" + str(old_block) + " seek=" + str(new_block) + " count=" + str(len) + " conv=notrunc"
        #print cmd
        os.system(cmd)

def cleanup(shrink_device, pool_to_shrink):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    cmd = "dmsetup remove " + shrink_device
    os.system(cmd)
    cmd = "lvremove " + vgname + "/restore_lv"
    os.system(cmd)
    cmd = "vgchange -an " + vgname
    os.system(cmd)
    
def delete_restore_lv(pool_to_shrink):
    vg_and_lv = pool_to_shrink.split("/")
    vgname = vg_and_lv[0]
    cmd = "lvremove " + vgname + "/restore_lv"
    os.system(cmd)

#TODO close opened files

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-L", "--size",  required=True, help="size to shrink to")
    ap.add_argument("-t", "--thinpool", required=True, help="vgname/poolname")
    args = vars(ap.parse_args())

    size_in_chunks=0L
    pool_to_shrink = args['thinpool']
   
    #delete_restore_lv(pool_to_shrink)
    activate_pool(pool_to_shrink)
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
  
    total_mapped_blocks = get_total_mapped_blocks()
    size_to_shrink = args['size']
    size_to_shrink_to_in_bytes = 0L
    size_to_shrink_to_in_bytes = calculate_size_in_bytes(size_to_shrink)
    #print size_to_shrink_to_in_bytes
    chunks_to_shrink_to = size_to_shrink_to_in_bytes/chunksize_in_bytes
    print "Need to shrink pool to this number of chunks   ---- " + str(chunks_to_shrink_to)

    if(chunks_to_shrink_to > int(nr_chunks)):
        print "This thin pool cannot be shrunk. The pool is already smaller than the size provided."
        cleanup(shrink_device,pool_to_shrink)
        exit()

    if (total_mapped_blocks > chunks_to_shrink_to):
        print "This thin pool cannot be shrunk. The mapped chunks are more than the lower size provided. Discarding allocated blocks from the pool may help."
        cleanup(shrink_device,pool_to_shrink)
        exit()

    if( check_pool_shrink_without_dd(chunks_to_shrink_to) == 1):
        change_xml(chunks_to_shrink_to)
        restore_xml_and_swap_metadata(pool_to_shrink)
        change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes)
        restore_vg_metadata(pool_to_shrink)
        cleanup(shrink_device,pool_to_shrink)
        print("This pool has been shrunk to the specified size of %s" % (size_to_shrink))
    else:
        changed_list = change_xml(chunks_to_shrink_to,1)
        if(len(changed_list) > 0):
            move_blocks(changed_list,shrink_device,chunksz_string)
            restore_xml_and_swap_metadata(pool_to_shrink)
            change_vg_metadata(pool_to_shrink, chunks_to_shrink_to,nr_chunks,chunksize_in_bytes)
            restore_vg_metadata(pool_to_shrink)
            print("This pool has been shrunk to the specified size of %s" % (size_to_shrink))
        cleanup(shrink_device,pool_to_shrink)

if __name__=="__main__": 
    main() 
