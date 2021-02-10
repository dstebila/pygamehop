import difflib

def equal(a, b, debugging, moreargs):
    if debugging:
        print('Checking for equality with previous game')
    if a != b:
        if debugging:
            print("Strings differ")
            differences = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
            diffl = []
            for difference in differences:
                diffl.append(difference)
            print(''.join(diffl), end="\n")
        return False
    else:
        if debugging:
            print("Strings identical")
        return None, True
