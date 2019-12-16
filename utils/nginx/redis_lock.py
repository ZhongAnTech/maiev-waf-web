# !/usr/bin/env python
# coding=utf-8

from multiprocessing import Process
import os
import time
import redis
from config import REDIS_CONFIG, ENV


class RedisLock(object):
    def __init__(self, key):
        self.rdcon = redis.Redis(host=REDIS_CONFIG[ENV]['host'],
                                 port=REDIS_CONFIG[ENV]['port'],
                                 password=REDIS_CONFIG[ENV]['password'],
                                 db=REDIS_CONFIG[ENV]['db'])
        self._lock = 0
        self.lock_key = "%s_dynamic_test" % key

    @staticmethod
    def get_lock(cls, timeout=10):
        while cls._lock != 1:
            timestamp = time.time() + timeout + 1
            cls._lock = cls.rdcon.setnx(cls.lock_key, timestamp)

            if cls._lock == 1 or (
                    time.time() > cls.rdcon.get(cls.lock_key) and
                    time.time() > cls.rdcon.getset(cls.lock_key, timestamp)):
                print "get lock"
                break
            else:
                # print 'wait lock'
                time.sleep(0.8)

    @staticmethod
    def release(cls):
        if time.time() < cls.rdcon.get(cls.lock_key):
            print "release lock"
            cls.rdcon.delete(cls.lock_key)


def deco(cls):
    def _deco(func):
        def __deco(*args, **kwargs):
            print "before %s called [%s]." % (func.__name__, cls)
            cls.get_lock(cls)
            try:
                return func(*args, **kwargs)
            finally:
                cls.release(cls)
        return __deco
    return _deco


@deco(RedisLock("112234"))
def myfunc(num):
    print '---------------'
    print "myfunc() called.--", str(os.getpid()), str(os.getppid())
    time.sleep(5)


def main():
    print 'Parent process %s.' % os.getpid()
    processes = list()
    for i in range(5):
        p = Process(target=myfunc, args=(i,))
        print 'Process will start.'
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
    print 'Process end.'


def test():
    for i in range(5):
        myfunc(i)


if __name__ == "__main__":

    main()
    # test()
    # ngx_t(1)