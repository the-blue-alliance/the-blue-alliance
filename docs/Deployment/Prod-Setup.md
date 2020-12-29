This document lists the items that need to be configured on production Google Cloud in order for The Blue Alliance to run.

## Task Queues

Task queues need to be created in advance. See [this section](https://github.com/the-blue-alliance/the-blue-alliance/wiki/Queues-and-defer#creating-queues) for the queues we need to set up.

### Memorystore (redis)

Roughly, the setup is outlined in [this page](https://cloud.google.com/appengine/docs/standard/python/migrate-to-python3/migrate-to-cloud-ndb#caching). We need the following steps:
 1. Create a [VPC Network](https://cloud.google.com/vpc/docs/vpc)
 2. Create a [VPC Access Connector](https://cloud.google.com/vpc/docs/configure-serverless-vpc-access#creating_a_connector)
 3. Create a [Redis Instance](https://cloud.google.com/memorystore/docs/redis/creating-managing-instances#creating_redis_instances) using the network
 4. Make note of the `REDIS_CACHE_URL` and VPC Connector name to set as deploy secrets