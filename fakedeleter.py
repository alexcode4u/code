import argparse
from time import sleep, time
import threading

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--number', required=True, type=str)
parser.parse_args()


def success():
    t = time()
    while True:
        if time() - t > 5:
            break
        sleep(0.25)
        print('.', end='')


v = 0
while v != 100:
    sleep(0.5)
    v += 2
    print(f'\r[{v}%-100%]', end='')
t = threading.Thread(target=success)
t.start()
t.join()
print('\n[+] Virus from phone was successfully removed')
