import scipy.stats as sc
import numpy as np
import random
import matplotlib.pyplot as plt


SIZES = ["KB", "MB", "GB"]
DIST = ["exp", "uniform", "zipf"] #TODO: need more
PARAMS = {'virtual_memory_size': [str, "100GB"],
          'hidden_storage_size': [str, "128MB"],
          'visible_storage_size': [str, "10GB"],
          'cell_size': [str, "100KB"],
          'object_size': [str, "100KB"],
          'access_number': [long, 5e7],
          'access_distribution': [str, "exp"],
          'deterministic': [str, 1]
         }


def get_param (key):
  param = PARAMS[key][1]
  if (type(param) == str) and (param[-2:] in SIZES):
    val = int(param[:-2])
    scale = param[-2:]
    for _ in (range(SIZES.index(scale) + 1)):
      val *= 1024
    return val
  return param


virtual_memory_size = get_param("virtual_memory_size")
hidden_storage_size = get_param("hidden_storage_size")
visible_storage_size = get_param("visible_storage_size")
cell_size = get_param("cell_size")
object_size = get_param("object_size")

hs_table_size = hidden_storage_size / cell_size
vs_table_size = visible_storage_size / cell_size
virtual_obj_number = virtual_memory_size / cell_size
print "hs: " + str(hs_table_size) + "   vs: " + str(vs_table_size) + \
  "   va: " + str(virtual_obj_number)

#TODO: virtual address should be: code, data, stack, heap
#get some better data?
hidden_obj_table = {}
visible_obj_table = {}
hidden_storage_table = {}
visible_storage_table = {}

for i in range(hs_table_size):
  hidden_storage_table[i] = -1
for i in range(vs_table_size):
  visible_storage_table[i] = -1

access_number = long(get_param("access_number"))
access_dist = get_param("access_distribution")
if access_dist == "exp":
  import bisect
  EXP_MAX = sc.expon.ppf(0.9999)
  exp_list = list(np.arange(0, EXP_MAX, EXP_MAX/virtual_obj_number))

deterministic = get_param("deterministic")
if deterministic:
  random.seed(deterministic)

assert access_dist in DIST

def swap (c, d):
  """ c in visible storage, d in hidden storage """
  c_val = visible_storage_table[c]
  d_val = hidden_storage_table[d]
  discard(c, visible_storage_table, visible_obj_table)
  discard(d, hidden_storage_table, hidden_obj_table)
  visible_storage_table[c] = d_val
  hidden_storage_table[d] = c_val
  if visible_obj_table.has_key(d_val):
    visible_obj_table[d_val].append(c)
  else: visible_obj_table[d_val] = [c]
  if hidden_obj_table.has_key(c_val):
    hidden_obj_table[c_val].append(d)
  else: hidden_obj_table[c_val] = [d]
  return (c_val, d_val)

def write (a, b, a_storage_table, a_obj_table, b_storage_table, b_obj_table):
  """ write b into a """
  b_val = b_storage_table[b]
  a_storage_table[a] = b_val
  if a_obj_table.has_key(b_val):
    a_obj_table[b_val].append(a)
  else: a_obj_table[b_val] = [a]

def discard_and_write (a, b, a_storage_table, a_obj_table, b_storage_table, 
  b_obj_table):
  pass

def discard (a, storage_table, obj_table):
  a_val = storage_table[a]
  if a_val != -1:
    obj_table[a_val].remove(a)
    if not len(obj_table[a_val]):
      del obj_table[a_val]
  return a_val
  
def get_va ():
  if access_dist == "exp":
    rand_num = random.expovariate(1.0)
    return bisect.bisect_left(exp_list, rand_num)
  else: 
    raise NotImplementedError("A not implemented distribution.") 

read_num = 0
write_num = 0
vs_access = []

for _ in range(access_number):
  # Generate a virtual address
  va = get_va()

  if hidden_obj_table.has_key(va):
    # if hit(x) in hidden storage
    a = random.choice(visible_storage_table.keys())
    while True:
      b = random.choice(hidden_storage_table.keys())
      if hidden_storage_table[b] != va:
        break

    # read from a, discard
    discard(a, visible_storage_table, visible_obj_table)
    vs_access.append(str(a)+'##'+'R')
    # write value b to a (demote from hidden to visible)
    write(a, b, visible_storage_table, visible_obj_table, 
      hidden_storage_table, hidden_obj_table)
    vs_access.append(str(a)+'##'+'W')
    # copy hit(x) into b, so that x appears twice in hidden storage
    discard(b, hidden_storage_table, hidden_obj_table)
    hidden_storage_table[b] = va
    hidden_obj_table[va].append(b)

    c = random.choice(visible_storage_table.keys())
    while True:
      d = random.choice(hidden_storage_table.keys())
      if hidden_storage_table[d] != va:
        break
    # swap c, d
    swap(c, d)
    vs_access.append(str(c)+'##'+'R')
    vs_access.append(str(c)+'##'+'W')

    write_num += 2
    read_num += 2

  elif visible_obj_table.has_key(va):
    # if hit(x) in visible storage
    a = random.choice(visible_obj_table[va])
    b = random.choice(hidden_storage_table.keys())
    swap(a, b)
    vs_access.append(str(a)+'##'+'R')
    vs_access.append(str(a)+'##'+'W')    

    while True:
      c = random.choice(visible_storage_table.keys())
      if visible_storage_table[c] != va:
        break    
    d = random.choice(hidden_storage_table.keys())
    # read from c, discard
    discard(c, visible_storage_table, visible_obj_table)
    vs_access.append(str(c)+'##'+'R')

    # write d to c
    write (c, d, visible_storage_table, visible_obj_table, 
      hidden_storage_table, hidden_obj_table)
    vs_access.append(str(c)+'##'+'W')    
    # write hit(x) into d
    discard(d, hidden_storage_table, hidden_obj_table)
    hidden_storage_table[d] = va
    if hidden_obj_table.has_key(va):
      hidden_obj_table[va].append(d)
    else: hidden_obj_table[va] = [d]

    write_num += 2
    read_num += 2

  else:
    # if miss, look up in remote / disk
    a = random.choice(visible_storage_table.keys())
    b = random.choice(hidden_storage_table.keys())
    # print "$$ 22" + str(a) + "  " + str(b)
    # read a, discard
    vs_access.append(str(a)+'##'+'R')
    discard(a, visible_storage_table, visible_obj_table)
    # write b into a
    write(a, b, visible_storage_table, visible_obj_table, 
      hidden_storage_table, hidden_obj_table)
    vs_access.append(str(a)+'##'+'W')
    # write hit(x) into b
    discard(b, hidden_storage_table, hidden_obj_table)
    hidden_storage_table[b] = va
    hidden_obj_table[va] = [b]

    write_num += 1
    read_num += 1


print read_num
print write_num
# print vs_access
vs_access_int = {}
f = open('vs_access.txt', 'w')
for i in vs_access:
  f.write(str(i) + '\n')
  addr = int(i.split("##")[0])
  if not vs_access_int.has_key(addr):
    vs_access_int[addr] = 1
  else: vs_access_int[addr] += 1
f.close()
vs_access_tuple = vs_access_int.items()
vs_access_tuple = zip(*vs_access_tuple)
# plt.scatter(*vs_access_tuple)
plt.plot(*vs_access_tuple)
plt.savefig('vs_access.jpg')
