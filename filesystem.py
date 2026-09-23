import struct #To convert high level python concepts such as integers into raw bytes
from disk import BLOCK_SIZE, TOTAL_BLOCKS

HEADER_BLOCK = 0

FILE_TABLE_START = 1
FILE_TABLE_BLOCKS = 10

DATA_START = FILE_TABLE_START + FILE_TABLE_BLOCKS #Or the 11th block

FILE_ENTRY_SIZE = 64

class FileSystem:

    def __init__(self, disk):
        self.disk = disk

    def format(self):
        self.write_header()

    def write_header(self):
        header = bytearray(BLOCK_SIZE) #Temporary buffer in our RAM filled with zeroes matching our BLOCK_SIZE

        #Filesystem identifier
        header[0:6] = b"SimpFS"

        #Version
        #< indicates little endian format
        #H unsigned short translates the number into 2 byte integer
        #6 is your byte offset
        #1 is the value you are inserting
        struct.pack_into("<H", header, 6, 1) #Translates a value and injects it in buffer

        #Block Size
        struct.pack_into("<H", header, 8, BLOCK_SIZE) 

        #Total Blocks
        struct.pack_into("<I", header, 10, TOTAL_BLOCKS)

        #This has used Block 0 in our disk
        self.disk.write_block(HEADER_BLOCK, header)

    # def clear_file_table(self):
    #     empty_block = bytes(BLOCK_SIZE) #Acts as your eraser and fills it up with null
  
    #     for block in range(FILE_TABLE_BLOCKS): #Triggers to write 512B of nulls in every block
    #         self.disk.write_block(
    #             FILE_TABLE_START + block,
    #             empty_block
    #         )

    def create_file_entry(
            self,
            name,
            size,
            start_block,
            block_count
    ):
        entry = bytearray(FILE_ENTRY_SIZE)

        #Filename
        name_bytes = name.encode('utf-8')

        if len(name_bytes)>32:
            raise ValueError("Filename is too long!")

        entry[0:32] = name_bytes.ljust(32, b"\x00")

        #File size
        struct.pack_into('<I', entry, 32, size)

        #Starting block
        struct.pack_into('<I', entry, 36, start_block)

        #Number of blocks
        struct.pack_into('<I', entry, 40, block_count)

        #Used flag
        entry[44] = 1

        return entry

    def find_free_file_entry(self):
        total_entries = (FILE_TABLE_BLOCKS * BLOCK_SIZE) // FILE_ENTRY_SIZE #80 available slots

        for index in range(total_entries):
            entry = self.read_file_entry(index)

            if entry[44] == 0:
                return index

        return None

    def write_file_entry(self, entry, index):
        if len(entry) != FILE_ENTRY_SIZE:
            raise ValueError("Invalid entry size")

        offset = index*FILE_ENTRY_SIZE #Global byte offset

        block = FILE_TABLE_START + (offset // BLOCK_SIZE) #Which block to write into
        block_offset = offset % BLOCK_SIZE  #Where to put the data in the block
 
        data = bytearray(self.disk.read_block(block)) #Reads the entire block

        data[block_offset:block_offset+FILE_ENTRY_SIZE] = entry #Write into the exact 64 byte slot

        self.disk.write_block(block, data) #Finally save the changes

    #Retrieve the entries
    def read_file_entry(self, index):
        offset = index * FILE_ENTRY_SIZE

        block = FILE_TABLE_START + (offset // BLOCK_SIZE)
        block_offset = offset % BLOCK_SIZE

        data = self.disk.read_block(block)

        return data[block_offset:block_offset+FILE_ENTRY_SIZE]

    #Convert the entries into human readable form
    def parse_file_entry(self, entry):

        name = entry[0:32].split(b"\x00", 1)[0].decode("utf-8")

        size = struct.unpack_from("<I", entry, 32)[0]

        start_block = struct.unpack_from("<I", entry, 36)[0]

        block_count = struct.unpack_from("<I", entry, 40)[0]

        used = entry[44] == 1

        return {
            "name": name,
            "size": size,
            "start_block": start_block,
            "block_count": block_count,
            "used": used
        }

    def is_block_used(self, block_number):
        total_entries = (FILE_TABLE_BLOCKS * BLOCK_SIZE) // FILE_ENTRY_SIZE

        for index in range(total_entries):
            entry = self.read_file_entry(index)

            if(entry[44] == 0):
                continue

            start_block = struct.unpack_from('<I', entry, 36)[0]
            block_count = struct.unpack_from('<I', entry, 40)[0]

            end_block = start_block + block_count

            if start_block <= block_number < end_block:
                return True

        return False

    def find_free_blocks(self, count):
        consecutive = 0
        start_block = None

        for block in range(DATA_START, TOTAL_BLOCKS):

            if not self.is_block_used(block):

                if consecutive == 0:
                    start_block = block

                consecutive += 1

                if consecutive == count:
                    return start_block

            else:
                consecutive = 0
                start_block = None

        return None

    #Break the data into 512B and write into consecutive blocks
    def write_file_data(self, data, start_block):
        for i in range(0, len(data), BLOCK_SIZE):
            block_number = start_block + (i // BLOCK_SIZE)

            chunk = data[i:i + BLOCK_SIZE]

            self.disk.write_block(block_number, chunk)

    def blocks_needed(self, size):
        return (size + BLOCK_SIZE - 1)//BLOCK_SIZE

    def create_file(self, name, data):
        #Find a free entry
        entry_index = self.find_free_file_entry()

        if entry_index is None:
            raise RuntimeError("File table is full")

        #Calculate how many blocks is needed
        block_count = self.blocks_needed(len(data))

        #Find blocks
        start_block = self.find_free_blocks(block_count)

        if start_block is None:
            raise RuntimeError("Not enough contigous space")

        #Write the data
        self.write_file_data(data, start_block)

        #Create the file's metadata
        entry = self.create_file_entry(
            name,
            len(data),
            start_block,
            block_count
        )

        #Store the metadata
        self.write_file_entry(entry, entry_index)

    def find_file(self, name):

        total_entries = (FILE_TABLE_BLOCKS * BLOCK_SIZE) // FILE_ENTRY_SIZE

        for index in range(total_entries):

            entry = self.read_file_entry(index)

            # Skip empty entries
            if entry[44] == 0:
                continue

            file_info = self.parse_file_entry(entry)

            if file_info["name"] == name:
                return file_info

        return None

    def read_file(self, name):

        file_info = self.find_file(name)

        if file_info is None:
            raise FileNotFoundError("File not found")

        start_block = file_info["start_block"]
        block_count = file_info["block_count"]
        size = file_info["size"]

        data = b""

        for i in range(block_count):
            block_number = start_block + i

            data += self.disk.read_block(block_number)

        return data[:size].decode('utf-8')

    def list_files(self):

        files = []

        total_entries = (FILE_TABLE_BLOCKS * BLOCK_SIZE) // FILE_ENTRY_SIZE

        for index in range(total_entries):

            entry = self.read_file_entry(index)

            if entry[44] == 0:
                continue

            file_info = self.parse_file_entry(entry)
            files.append(file_info)

        return files


    def delete_file(self, name):
        total_entries = (FILE_TABLE_BLOCKS * BLOCK_SIZE)//FILE_ENTRY_SIZE

        for index in range(total_entries):
            entry = self.read_file(index)

            if entry[44] == 1:
                continue

            files_info = self.parse_file_entry(entry)

            if files_info['name'] == name:

                entry = bytearray(entry)
                entry[44] = 0

                self.write_file_entry(entry, index)

                return

        return FileNotFoundError("File does not exist")

    def storage_used(self):
        used_blocks = 0
        used_blocks += DATA_START

        for block in range(DATA_START, TOTAL_BLOCKS):
            if self.is_block_used(block):
                used_blocks+=1

        return used_blocks * BLOCK_SIZE