"""
Microservices API Architecture

A microservices-based API with API Gateway routing requests to multiple
Lambda-based microservices, each with its own dedicated database.
"""

from diagrams import Cluster, Diagram
from diagrams.aws.compute import Lambda
from diagrams.aws.database import Dynamodb
from diagrams.aws.network import APIGateway

with Diagram("Microservices API", show=False, outformat="dot"):
    api = APIGateway("api")

    with Cluster("Microservices"):
        svc1 = Lambda("users")
        svc2 = Lambda("orders")
        svc3 = Lambda("products")

    with Cluster("Data Layer"):
        db1 = Dynamodb("users-db")
        db2 = Dynamodb("orders-db")
        db3 = Dynamodb("products-db")

    api >> [svc1, svc2, svc3]
    svc1 >> db1
    svc2 >> db2
    svc3 >> db3

