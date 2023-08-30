packet_types = {"acknowledgement" : 0, 
                "update" : 1,
                "account" : 2,
                "identification" : 3,
                "craft" : 5,
                }

flags = {
    "update" : {
        "ITEM" : 0,
        "ENERGY" : 2**1,
        "CPUS" : 2**2,
        "CRAFT" : 2**3,
        "ALL" : 2**4,
    },
    "account" : {
        "SUCCESS" : 0,
        "FAILURE" : 0,
    },
}


def unpack_header(header_packet):
    return header_packet[0], int.from_bytes(header_packet[1:5], byteorder='big'), header_packet[5]

def create_header(type, length, flags):
    packet_bytes = type.to_bytes(1, byteorder='big')
    packet_bytes += length.to_bytes(4, byteorder='big')
    packet_bytes += flags.to_bytes(1, byteorder='big')
    return packet_bytes

def get_packet_type(packet):
    type = packet[0]
    found_type = None
    for key, value in packet_types.items():
        if value == type:
            found_type = key
            break
    if found_type is None:
        print("Received unknown packet type")
    return type

def print_bytes(bytes):
    print(", ".join(hex(b) for b in bytes))

