# coding=utf-8
from time import time


class Cache:
    '''simple cache'''

    def __init__(self):
        self.mem = {}
        self.time = {}

    def set(self, key, data, age=-1):
        self.mem[key] = data
        if age == -1:
            self.time[key] = -1
        else:
            self.time[key] = time() + age
        return True

    def get(self, key):
        if key in self.mem.keys():
            if self.time[key] == -1 or self.time[key] > time():
                return self.mem[key]
            else:
                self.delete(key)
                return None
        else:
            return None

    def delete(self, key):
        del self.mem[key]
        del self.time[key]
        return True

    def clear(self):
        self.mem.clear()
        self.time.clear()


if __name__ == "__main__":
    t = time()
    print(t)
    print(t + 60)
    print(t + 100)
