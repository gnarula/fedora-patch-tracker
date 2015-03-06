from rq import Worker, Queue, Connection
from tracker import conn

listen = ['default']

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(list(map(Queue, listen)))
        worker.work()
