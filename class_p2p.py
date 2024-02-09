import serial
import time

class P2P():
    def __init__(self, port_name: str, baud_rate: int) -> None:
        self.port = serial.Serial(xonxoff=False, rtscts=False,
                                  dsrdtr=False)
        self.port_name = port_name
        self.baud_rate = baud_rate

    def open_com_port(self) -> None:
        self.port.setRTS(False)
        self.port.setDTR(False)
        self.port = serial.Serial(self.port_name, self.baud_rate, timeout=0.3, xonxoff=False, rtscts=False,
                                  dsrdtr=False)
        if self.port.isOpen() == True:
            print()
            # self.port.close()
        # self.port = serial.Serial(self.port_name, self.baud_rate, timeout=0.3, xonxoff=False, rtscts=False,
        #                           dsrdtr=False)
        # self.port.setRTS(False)
        # self.port.setDTR(False)

    def close_com_port(self) -> None:
        if self.port.isOpen() == True:
            self.port.close()

    def __calc_crc(self, packet: bytearray) -> int:
        crc = 0
        # for ik in range(0,packet[2]+2):
        for ik in range(0, len(packet)):
            crc += packet[ik]
        # crc = ~crc
        crc &= 0xFF
        # print(f'crc: {crc}')
        return crc

    def __verify_response(self, response: bytearray, response_length: int) -> int:
        if len(response) < response_length+2:
            return 1
        crc = self.__calc_crc(response[:-1])
        if crc != response[-1]:
            return 1
        return 0

    def send_request(self, cmd: int, data: bytearray) -> None:
        start_byte = ord('!')
        request = bytearray([start_byte, cmd]) + data
        request += bytearray([self.__calc_crc(request[1:])])
        # print(request)
        self.port.flushInput()
        self.port.write(request)

    def receive_response(self, data_length: int):
        response = self.port.read(data_length + 3)
        # print(response)
        # print(f'len of response: {len(response)}')
        error = self.__verify_response(response[1:], data_length)
        return error, response[2:-1]

    def receive_response_while(self, data_length: int, timeout = 0.5):
        _timeout = time.time() + timeout
        while True:
            start_temp = self.port.read(1)
            if start_temp == b'!':
                break
            if time.time() > _timeout:
                return 1, bytearray()
        response = self.port.read(data_length + 2)
        error = self.__verify_response(response, data_length)
        return error, response[1:-1]

    def parse_responses(self, data_length: int, amount: int):
        byte_list = []
        error_list = []
        self.port.flushInput()
        start_temp = b''

        for i in range(amount):
            error, response = self.receive_response_while(data_length)
            if error:
                error_list.append(error)
            else:
                byte_list.append(response)
        return error_list, byte_list

