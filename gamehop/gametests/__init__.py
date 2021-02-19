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
        return None, False
    else:
        if debugging:
            print("Strings identical")
        return None, True


def advantage(a, b, debugging, moreargs):
    if debugging:
        print('Checking that games match experiment: TODO')
    
    (experiment, schemename) = moreargs
    ename = experiment
    r = "Adv(" + schemename + ")"
    print('Advantage is: ' + r)

    return r, True
