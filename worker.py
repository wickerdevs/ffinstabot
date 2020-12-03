import os, redis
from ffinstabot.config import secrets
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']
redis_url = secrets.get_var('REDISTOGO_URL', default='redis://localhost:6379')
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()