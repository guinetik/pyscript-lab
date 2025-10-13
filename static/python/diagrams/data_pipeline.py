"""
Data Analytics Pipeline Architecture

A data processing pipeline that transforms raw data stored in S3,
processes it through Lambda ETL functions, and makes it queryable
via Athena with Redis caching.
"""

from diagrams import Cluster, Diagram
from diagrams.aws.analytics import Athena
from diagrams.aws.compute import Lambda
from diagrams.aws.database import ElastiCache
from diagrams.aws.storage import S3

with Diagram("Data Analytics Pipeline", show=False, outformat="dot", graph_attr={"splines": "ortho"}):
    source = S3("raw-data")

    with Cluster("Processing"):
        etl = Lambda("transform")
        processed = S3("processed")

    analytics = Athena("analytics")
    cache = ElastiCache("cache")

    source >> etl >> processed >> analytics
    analytics >> cache

