"""
Event-Driven Architecture

An event processing system using SNS topics, SQS queues, and Lambda functions
with persistent state storage in DynamoDB.
"""

from diagrams import Cluster, Diagram
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.integration import SNS, SQS

with Diagram("Event-Driven Architecture", show=False, outformat="dot", graph_attr={"splines": "ortho"}):
    source = EC2("event source")

    with Cluster("Event Processing"):
        topic = SNS("topic")
        queue = SQS("queue")
        workers = [Lambda("handler1"), Lambda("handler2"), Lambda("handler3")]

    db = Dynamodb("state")

    source >> topic >> queue >> workers >> db

