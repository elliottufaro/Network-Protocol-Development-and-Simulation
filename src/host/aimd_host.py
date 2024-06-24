from typing import List
from matplotlib import pyplot as plt

from network.network_interface import NetworkInterface
from simulation.clock import Clock
from util.timeout_calculator import TimeoutCalculator
from simulation import simulation_logger as log
from network.packet import Packet

"""
This class implements a host that follows the AIMD protocol.
"""


class AimdHost:

    def __init__(self, clock: Clock, network_interface: NetworkInterface, timeout_calculator: TimeoutCalculator):
        # Host configuration
        self.timeout_calculator: TimeoutCalculator = timeout_calculator
        self.network_interface: NetworkInterface = network_interface
        self.clock: Clock = clock

        # RTT-min tracking
        self.RTT = 20

        #Track the window sizes for plotting
        self.window_sizes =[1]

        # This will allow for altering the window_size. 
        self.curr_window_size = 1.0  

        # This dict will hold the sequence number for unacked packets as key values and the timestamps for when those packets 
        # were transmitted as the pair values
        self.unAcked = {}

        # maintains a set of the acknowledgments received, each element is the sequence number of a packet
        self.acks_received = set() 

        # maintains the sequence number of the last packet transmitted.
        self.curr_seq = 0 

        # allows for the ability to track how many packets sent are in flight
        self.in_flight = 0

        # Allows us to track whether or not slow start is still in effect. 
        self.slow_start = True

        # Allows us to track the last decrease and ensure we are not doing it more than once an RTT. 
        self.dec_cooldown = 0.0

        # TODO: Add any stateful information you might need to track the progress of this protocol as packets are
        #  sent and received. Your sliding window should be initialized to a size of 1, and should use the slow start
        #  algorithm until you hit your first timeout
        #    - Feel free to create new variables and classes, just don't delete any existing infrastructure.
        #    - In particular, you should make use of the network interface to interact with the network.

    def set_window_size(self, new_window_size: float, old_window_size: float):
        if new_window_size < old_window_size:
            log.add_event(type="Shrinking Window", desc=f"Old: {old_window_size}, New: {new_window_size}")
        if old_window_size < new_window_size:
            log.add_event(type="Expanding Window", desc=f"Old: {old_window_size}, New: {new_window_size}")
        # TODO: Update the sliding window
        self.window_sizes.append(new_window_size)
        self.curr_window_size = new_window_size

    @staticmethod
    def plot(window_sizes: List[int]):
        plt.plot(window_sizes, label="Window Sizes", color="red", linewidth=2, alpha=0.5)
        plt.ylabel("Window Size")
        plt.xlabel("Tick")
        plt.legend()
        plt.savefig("aimd-window-sizes.png")
        plt.close()


    def shutdown_hook(self):
        # TODO: Save the window sizes over time so that, when the simulation finishes, we can plot them over time.
        #  Then, pass those values in here
        self.plot(self.window_sizes)

    def run_one_tick(self) -> int | None:
        current_time = self.clock.read_tick()
        if (not self.slow_start):
            #increment the cooldown every tick when not in slow start by 1/W
            self.dec_cooldown += (1/self.curr_window_size)
            
        

        # TODO: STEP 1 - Process newly received messages
        #  - These will all be acknowledgement to messages this host has previously sent out.
        #  - You should mark these messages as successfully delivered.
        #  - You should also increase the size of the window
        #      - You should start in "slow-start" mode to quickly ramp up to the bandwidth capacity.
        #      - Exit "slow-start" mode once your first timeout occurs
        packets_received = self.network_interface.receive_all()

        #only process packets if they're received 
        if packets_received:
            
            #iterate through each received packet
            for packet in packets_received:
                self.timeout_calculator.add_data_point(current_time - packet.sent_timestamp)

                #if packet is a new ack, acknowledge it
                if (packet.sequence_number not in self.acks_received):
                    packet.ack_flag = True
                    self.acks_received.add(packet.sequence_number)

                #remove it from the hashmap
                if packet.sequence_number in self.unAcked:
                    del self.unAcked[packet.sequence_number]
                    self.in_flight -= 1
                #depending on whether it is slow start or not will determine how the window is increased. (+1 for slow start and +1/W for congestion control)
                if self.slow_start:
                    self.set_window_size(self.curr_window_size + 1, self.curr_window_size)
                else:
                    self.set_window_size(self.curr_window_size + (1/self.curr_window_size), self.curr_window_size)
                    


        # TODO: STEP 2 - Retry any messages that have timed out
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see if there are any inflight messages who's timeout has already passed
        #  - If you find a timed out message, create a new packet and transmit it
        #      - The new packet should have the same sequence number
        #      - You should set the packet's retransmission_flag to true
        #      - The sent time should be the current timestamp
        #      - Use the transmit() function of the network interface to send the packet
        #  - Shrink the sliding window
        #      - This should happen at most once per RTT
        #      - The window size should not go below 1


        #iterate through the hashmap to detect timeouts
        for key in self.unAcked:
            if ((current_time - self.unAcked[key]) >=  self.timeout_calculator.current_timeout):
                #retransmit the packet
                self.unAcked[key] = current_time
                packet = Packet(current_time, key)
                packet.retransmission_flag = True
                self.network_interface.transmit(packet)

                #switch from slow start to congestion control if that has not yet been done
                if (self.slow_start):
                    self.slow_start = False
                #Only set the window if the appropriate cool-down period of an RTT has occured
                if self.dec_cooldown >= 1:
                    self.dec_cooldown = 0
                    self.set_window_size(self.curr_window_size/2, self.curr_window_size)
                
                #don't let the window size go below 1
                if self.curr_window_size < 1:
                    self.set_window_size(1.0, self.curr_window_size)

        # TODO: STEP 3 - Transmit new messages
        #  - When you transmit each packet (in steps 2 and 3), you should track that message as inflight
        #  - Check to see how many additional packets we can put inflight based on the sliding window spec
        #  - Construct and transmit the packets
        #      - Each new packet represents a new message that should have its own unique sequence number
        #      - Sequence numbers start from 0 and increase by 1 for each new message
        #      - Use the transmit() function of the network interface to send the packet

        #only transmit a packet when there are less in flight than the size of the window
        while self.in_flight < int(self.curr_window_size):
            #set the hashmap to have the current time of the newly sequnced packet for tracking the timeout
            self.unAcked[self.curr_seq] = current_time
            #give the new packet the current time and it's sequence number
            packet = Packet(current_time, self.curr_seq)
            #transmit
            self.network_interface.transmit(packet)
            self.in_flight +=1
            self.curr_seq += 1

            

        # TODO: STEP 4 - Return
        #  - Return the largest in-order sequence number
        #      - That is, the sequence number such that it, and all sequence numbers before, have been ACKed


        if self.acks_received:
            x = 0
            while x in self.acks_received:
                x +=1
            return (x-1)
