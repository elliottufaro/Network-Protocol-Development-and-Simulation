from abc import ABC

from host.host import Host
from network.network_interface import NetworkInterface
from network.packet import Packet
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator

"""
This host implements the stop and wait protocol. Here the host only
sends one packet in return of an acknowledgement.
"""


class StopAndWaitHost(Host, ABC):

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received.
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.
        self.acks_received = set() # maintains a set of the acknowledgments received, each element is the sequence number of a packet
        self.curr_seq = 0 # maintains the sequence number of the last packet transmitted. 
        self.in_flight = False # allows for the ability to track if a the last packet sent is in flight
        self.last_transmit_timestamp = 0 # tracks the timestamp of the last packet sent out



    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.

        packets_received = self.network_interface.receive_all()
        
        if packets_received:
            recieved_packet_seq = packets_received[0].sequence_number
            self.timeout_calculator.add_data_point(current_time - packets_received[0].sent_timestamp)
            if (recieved_packet_seq not in self.acks_received):
                packets_received[0].ack_flag = True
                self.acks_received.add(recieved_packet_seq)
                self.in_flight = False
                self.curr_seq += 1

        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if the inflight message's timeout has already passed.
        #  - If the packet did time out, construct a new packet and transmit
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet


        #   Check to see if a packet is still in_flight as well as if that packet has timed out by subtracting the last transmit timestamp
        #   from the current current timestamp. If that value is greater than or equal to the current timeout than retransmit 
        if (self.in_flight and ((current_time - self.last_transmit_timestamp) >=  self.timeout_calculator.current_timeout)):
            packet = Packet(current_time, self.curr_seq)
            packet.retransmission_flag = True
            self.network_interface.transmit(packet)
            self.last_transmit_timestamp = current_time


        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit a packet (in steps 2 and 3), you should track that message as inflight
        #  - If you don't have a message inflight, we should send the next message
        #  - Construct and transmit the packet
        #      - The packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet
        

        #   If the in_flight status is false than we know it was turned off by a recently acked packet and we can therefore transmit the
        #   next packet.
        elif(not self.in_flight):
            packet = Packet(current_time, self.curr_seq)
            self.network_interface.transmit(packet)
            self.last_transmit_timestamp = current_time
            self.in_flight = True

        
        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed

        #If the acks_received set is populated at all we can return it's max which will be the sequence number to the last acked packet 
        if self.acks_received:
            return max(self.acks_received)
