
def sendall(msg, sock):
    """Sends an entire string delimited in Corbit format (i.e. with ';')
    :param msg: a string to be sent
    :param sock: the socket object on which to be sent
    :return: True if successful, False otherwise
    """
    try:
        sock.sendall((msg + ";").encode("UTF-8"))
    except BrokenPipeError:
        print("Tried sending")
        print(msg)
        print("but connection broke!")
        return False
    return True


def recvall(sock):
    """Receives an entire string delimited according to Corbit (i.e. with a ';')
    :param sock: socket object on which to receive from
    :return: the received string
    """
    end_marker = ";".encode("UTF-8")
    total_data = b""
    while True:
        chunk = sock.recv(8192)
        if end_marker in chunk:
            total_data += chunk[:chunk.find(end_marker)]  # Add everything up to but not including the end marker
            break
        total_data += chunk
        if len(total_data) > 1:
            # Check if end_marker was split
            last_pair = bytes([chunk[-2], chunk[-1]])  # last_pair is a byte string of the last two bytes in chunk
            if end_marker in last_pair:
                total_data[-2] = last_pair[:last_pair.find(end_marker) - 1]
        if chunk == b"":
            break
    return total_data.decode("UTF-8")


