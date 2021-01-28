import resultaTask

api = resultaTask.APISingleton.getInstance()
oneLine = input(
    "Would you like one JSON line to use as you please? (individual lines per game by default)(Y/N): ").lower() == "y"
while (True):

    d1 = input("Enter Start Date(YYYY-MM-DD):")
    d2 = input("Enter End Date(YYYY-MM-DD):")
    try:
        foo = api.getSolution(d1, d2)
    except ValueError:
        print("There most likely was an error with the dates you types! please try again")
        foo = "\n"
    if (oneLine):
        foo = str(foo).replace("'", '"')
        # dicts use single quotations, and this is the fastest way to fix that.
        print(foo)
    else:
        for x in foo:
            bar = str(x).replace("'", '"')
            print(bar)
