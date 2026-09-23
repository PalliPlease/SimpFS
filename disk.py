BLOCK_SIZE = 512 #Block size of 512 Bytes
DISK_SIZE = 1024 * 1024 #Disk size of 1MB
TOTAL_BLOCKS = DISK_SIZE // BLOCK_SIZE # 2048 Blocks

class VirtualDisk:

    def __init__(self, filename):
        self.filename = filename

    #Create file
    def create(self):
        with open(self.filename, "wb") as file: #Open in binary write mode
            file.write(b"\x00" * DISK_SIZE)

    #Read from file
    def read_block(self, block_number):
        with open(self.filename, "rb") as file: #Open in binary read mode
            file.seek(block_number * BLOCK_SIZE) #Move the cursor to the specific byte location 
            return file.read(BLOCK_SIZE) #Returning the entire block

    #Write to the file
    def write_block(self, block_number, data):
        if len(data) > BLOCK_SIZE:
            raise ValueError("Data is too large to process")

        data = data.ljust(BLOCK_SIZE, b"\x00") #Fill the rest with nulls

        with open(self.filename, "r+b") as file: #Read and write in binary
            file.seek(block_number*BLOCK_SIZE)
            file.write(data)

