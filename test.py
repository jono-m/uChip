def decoratorName(displayName):
    def inner(func):
        def replacementFunc():
            if displayName is not None:
                print("Injected" + displayName)
            else:
                print("blah")
            func()
        return replacementFunc

    if callable(displayName):
        func = displayName
        displayName = None
        return inner(func)
    return inner


@decoratorName
def hello2():
    print("hello2")

hello2()