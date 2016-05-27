import os
import sys

start, end = int(sys.argv[1]), int(sys.argv[2])

dir_ = os.getcwd()

print (hash(dir_) % (end - start)) + start

