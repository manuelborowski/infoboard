import datetime


l = []
for i in xrange(10):
    l.append(datetime.date.today() + datetime.timedelta(days=i))

l.pop(3)
l.pop(3)
l.pop(3)
l.pop(3)

print l

n = datetime.date.today() + datetime.timedelta(days=4)

print n

for i, v in enumerate(l):
    print n, i, v
    if n <= v:
        l = l[i:]
        break

print l

for i, v in enumerate(l):
    print n, i, v
    if n <= v:
        l = l[i:]
        break

print l

n = datetime.date.today() + datetime.timedelta(days=10)

print n

if n > l[-1]:
    l = []
for i, v in enumerate(l):
    print n, i, v
    if n <= v:
        l = l[i:]
        break

print l
