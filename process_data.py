import matplotlib.pyplot as plt

p = "vs_access.txt"
vs_access = []

with open(p, "rb") as fp:
  for i in fp.readlines():
	i = i.split('\n')[0]
	x, y = i.split(', ')
	x = int(x.split('(')[1])
	y = int(y.split(')')[0])
	vs_access.append((x, y))

s = 0
for i in vs_access:
  s += i[1]
print "last item: " + str(vs_access[-1])
print "avg: " + str(s/len(vs_access))

i = 0
vs_access_compressed = []
while i < len(vs_access):
  vs_slice = vs_access[i: i+20]
  sum_x = 0
  sum_y = 0
  for ii in vs_slice:
  	sum_x += ii[0]
  	sum_y += ii[1]
  avg_x = sum_x / 20
  avg_y = sum_y / 20
  vs_access_compressed.append((avg_x, avg_y))
  i += 20

# vs_access_int = {}
# f = open('vs_access_compressed.txt', 'w')
# for i in vs_access_compressed:
#   f.write(str(i) + '\n')
# f.close()
vs_compressed_tuple = zip(*vs_access_compressed)
plt.plot(*vs_access_compressed)
plt.savefig('vs_access_compressed.jpg')
