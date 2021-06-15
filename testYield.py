def test():
    while True:
        yield


for t in test():
    print(t)
