Overview
This project involves developing and testing network protocols using a custom simulator. The protocols implemented include Stop-And-Wait, Sliding Window, and AIMD, as well as the computation of retransmission timeouts using the EWMA-based algorithm. The project explores protocol behavior under various network conditions, including packet loss and congestion collapse.

Requirements
This project requires Python 3 and Matplotlib. Matplotlib can be installed by following the instructions on the Matplotlib installation page.

Project Structure and Usage
Moving Averages and Retransmission Timeouts

Implemented the TimeoutCalculator to compute mean RTT and standard deviation using the EWMA-based algorithm. To run the timeout simulation:
python3 run_timeout_simulation.py -a <ALPHA> -b <BETA> -k <K> <SCENARIO>
python3 run_timeout_simulation.py -a 0.125 -b 0.25 -k 1.5 permanent-change

Developed Stop-And-Wait and Sliding Window protocols for reliable data transmission. To run the reliability simulation:
python3 run_reliability_simulation.py --seed <SEED> --rtt-min <RTT_MIN> --ticks <TICKS> <PROTOCOL>

Example for Stop-And-Wait:
python3 run_reliability_simulation.py --seed 1 --rtt-min 10 --ticks 50 stop-and-wait

Example for Sliding Window:
python3 run_reliability_simulation.py --seed 1 --rtt-min 2 --ticks 10 sliding-window --window-size 5

Congestion Collapse
Simulated congestion collapse using the Sliding Window protocol. Analyzed transport-layer throughput as a function of the window size, demonstrating the classic congestion collapse pattern.
AIMD (Additive Increase Multiplicative Decrease)

Implemented the AIMD algorithm, incorporating additive increase and multiplicative decrease rules. Ran simulations to observe the evolution of the window size over time. To run the AIMD protocol:
python3 run_reliability_simulation.py --seed 1 --rtt-min 20 --ticks 10000 --queue-limit 10 aimd
