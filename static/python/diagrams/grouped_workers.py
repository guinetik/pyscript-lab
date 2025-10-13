"""
Grouped Workers Architecture

A simple load balancer pattern distributing traffic to multiple worker instances
that write to a shared database.
"""

from diagrams import Diagram
from diagrams.aws.compute import EC2
from diagrams.aws.database import RDS
from diagrams.aws.network import ELB

with Diagram("Grouped Workers", show=False, direction="TB", outformat="dot"):
    ELB("lb") >> [
        EC2("worker1"),
        EC2("worker2"),
        EC2("worker3"),
        EC2("worker4"),
        EC2("worker5")
    ] >> RDS("events")

