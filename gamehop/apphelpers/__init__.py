import os
import sys
import inspect
from gamehop import inlining, verification
from gamehop import gametests

separator = "---------------------------------------------------------------"
Separator = "==============================================================="

def parseArgs(argv):
    # First, make sure that the arguments are all sane
    if len(argv) < 2:
        print("Missing directory")
        sys.exit(1)

    if len(argv) > 2:
        print("Too many arguments")
        sys.exit(1)

    dirname = argv[1]
    if not os.path.isdir(dirname):
        print("Directory does not exist")
        sys.exit(1)

    if not os.path.isfile(dirname + "/proof.py"):
        print("proof.py does not exist in " + dirname)
        sys.exit(1)

    return dirname

def isGameTest(val):
    if not callable(val): return false
    return val.__name__ in dir(gametests)


def checkProof(experiment, steps, debugging):
    games = []
    originalFunctions = []
    advantages = []
    lastStep = None
    isValid = True

    step = steps[0]
    if step[0] != experiment[0]:
        print("First step function does not match experiment game 0")
        isValid = False
        if not debugging:
            sys.exit(1)

    for i in range(0, len(steps)):
        step = steps[i]
        if debugging:
            print(Separator)
            print('Processing step: ' + str(i))
        if isGameTest(step[0]) :
            print('Noted game test "' + step[0].__name__ + '"')
            if isGameTest(lastStep[0]) :
                print('Error: two non-function steps in a row.')
                sys.exit(1)
            lastStep = step
        elif not callable(step[0]):
            print('Error: step is not game test or function')
            sys.exit(1)
        else:
            if type(step[1]) == list:
                inlined = step[0]
                for i in step[1]:
                    if type(i) == tuple:
                        inlined = inlining.inline_class(inlined, i[0], i[1])
                    else:
                        inlined = inlining.inline_function(inlined, i)
                if debugging:
                    print(inlined)
                    print(separator)
            else:
                if len(step) == 3:
                    inlined = inlining.inline_class(step[0], step[1], step[2])
                else:
                    inlined = inlining.inline_function(step[0], step[1])
                if debugging:
                    print(inlined)
                    print(separator)

            r = verification.canonicalize_function(inlined)
            games.append(verification.canonicalize_function(inlined))
            originalFunctions.append(step[0])

            if debugging:
                print(r)

            if lastStep == None:
                pass
            elif not isGameTest(lastStep[0]):
                # must be a function step
                if debugging: print(separator)
                advantage, testResult = gametests.equal(games[-1], games[-2], debugging, None)
                isValid = isValid and testResult
                advantages.append(advantage)
            else:
                if debugging: print(separator)
                advantage, testResult = lastStep[0](games[-1], games[-2], debugging, lastStep[1])
                isValid = isValid and testResult
                advantages.append(advantage)
            lastStep = step
    return isValid, advantages
