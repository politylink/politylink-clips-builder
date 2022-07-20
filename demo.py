from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from multiprocessing import freeze_support
from time import time

def gcd(pair):
    a, b, = pair
    low = min(a, b)
    for i in range(low, 0, -1):
        if a % i == 0 and b % i == 0:
            return i

def main():
    numbers = [(1963309, 2265973), (2030677, 3814172),
              (1551645, 2229620), (2039045, 2020802)]
    start = time()
    pool = ThreadPoolExecutor(max_workers=2)
    #pool = ProcessPoolExecutor(max_workers=2)
    results = list(pool.map(gcd, numbers))
    end = time()
    print(end - start)

if __name__ == '__main__':
    main()
