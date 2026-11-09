import dataclasses
from operator import invert
import os
import subprocess
import sys
import tempfile
from typing import Callable

TESTS_SIGNATURE = "tests :: [(String, [(Int, String, Bool)])]"
TESTS_DEFINITION = "tests ="

MODULE_RULES = """
{-# LANGUAGE ExtendedDefaultRules #-}
"""

HELP_MESSAGE = """Haskell tester script
Usage: {0} [OPTIONS] HS_FILE TEST_FILE

OPTIONS:
        --hs    <str>   Sets the Haskell source code file
        --hst   <str>   Sets the test case code file
    -t, --tests <list>  Sets specific cases to test (list without spaces separated by commas)
                        Format: FUNCTION[/TESTS] (if TESTS is omitted, all cases are tested for that function)
                        TESTS formats: 
                            single number
                            range (first-last, inclusive, e.g.: 2-5, 3-, -7)
                            list (dot separated, e.g.: 2.3.7, 1, 5.6)

                            If TESTS is prefixed with '^', the inverse of the given cases will be tested    
                            Test cases are indexed/numbered from 1
                            
                        Only the last occurrence of a test entry is kept
                        If this parameter is not specified, all cases in the test file will be run
                        Examples: 
                            someFunction/5,otherFunction/^2-4,anotherFunction/6.8.9
                            function/5
                            
    -o, --others        Includes test cases for functions not in the --tests list (useful for omitting a single test case: -t func/^3 -o)
    -b, --bin <str>     Sets the path of the runhaskell/runghc binary (if omitted, the one in the in PATH will be run)
    -h, --help          Prints this help message

Test file format: a list of the testcases separated by newlines, which should all evalute to the Bool type in Haskell
    Grouping by function: testcases can be grouped by a function name (it doesn't need to match the name of the function tested - any name is allowed)
    Syntax: inline Haskell comment immediately followed by an 'f' character
        --f functionName
        functionName 2 == 4
        functionName 4 == 8
        ...
    Normal Haskell comments are allowed in this file - so an unwanted testcase can be temporarily removed this way (but it can also be excluded via the --tests and --others options/flags)
    Other Haskell language features are not supported in this file
"""

def panic(msg: str):
    print(f"\033[31mERROR: {msg}\033[0m")
    sys.exit(1)


def panic_print_help(msg: str):
    print(f"\033[31mERROR: {msg}\033[0m")
    #print(HELP_MESSAGE.format(sys.argv[0]))
    print(f"Run \"{sys.argv[0]} --help\" for more info")
    sys.exit(1)


def exit_print_help():
    print(HELP_MESSAGE.format(sys.argv[0]))
    sys.exit(0)


@dataclasses.dataclass
class CLIArguments:
    hs_file: str | None
    hst_file: str | None
    tests: dict[str, Callable[[int], bool]]
    include_other_functions: bool
    bin: str | None
    

def parse_tests(tests: str) -> dict[str, Callable[[int], bool]]:
    out = {}
    for test in tests.split(","):
        test_segments = test.split("/")
        function = test_segments[0]

        if len(test_segments) == 1:
            out[function] = lambda i: True
            continue

        inverted = False
        cases = test_segments[1]
        if cases.startswith("^"):
            cases = cases[1:]
            inverted = True

        if "-" in cases:
            case_segments = cases.split("-")
            if case_segments[0] == "":
                index = case_segments[1]
                if not index.isdigit():
                    panic_print_help(f"Invalid test case notation: {cases}")
                    
                out[function] = lambda i, local_index=index: i <= int(local_index)
                continue
            elif case_segments[1] == "":
                index = case_segments[0]
                if not index.isdigit():
                    panic_print_help(f"Invalid test case notation: {cases}")
                    
                out[function] = lambda i, local_index=index: i >= int(local_index)
                continue

            index1 = case_segments[0]
            index2 = case_segments[1]

            if not index1.isdigit() or not index2.isdigit():
                panic_print_help(f"Invalid test case notation: {cases}")

            out[function] = lambda i, local_index1=index1, local_index2=index2: i >= int(local_index1) and i <= int(local_index2)
        elif "." in cases:
            case_segments = cases.split(".")

            case_indices = []
            for case_segment in case_segments:
                if not case_segment.isdigit():
                    panic_print_help(f"Invalid test case notation: {cases}")

                case_indices.append(int(case_segment))

            out[function] = lambda i, local_indices=case_indices: i in local_indices
        else:
            if not cases.isdigit():
                panic_print_help(f"Invalid test case notation: {cases}")

            index = cases
            out[function] = lambda i, local_index=index: i == int(local_index)

        if inverted:
            predicate = out[function]
            out[function] = lambda i, local_predicate=predicate: not local_predicate(i)
            
    return out


def parse_args() -> CLIArguments:
    if len(sys.argv) < 2:
        panic_print_help("Not enough arguments were given")
    
    args = sys.argv[1:]
    config = CLIArguments(hs_file=None, hst_file=None, tests={}, include_other_functions=False, bin=None)
    posarg = 0
    index = 0

    def safe_string():
        nonlocal index

        if index + 1 >= len(args):
            panic_print_help(f"No argument given for {args[index]}")

        result = args[index+1]
        index += 2
        
        return result
            

    while index < len(args):
        arg = args[index]

        if arg == "--hs":
            config.hs_file = safe_string()
        elif arg == "--hst":
            config.hst_file = safe_string()
        elif arg == "-t" or arg == "--tests":
            config.tests = { **config.tests, **parse_tests(safe_string()) }
        elif arg == "-o" or arg == "--others":
            config.include_other_functions = True
            index += 1
        elif arg == "-b" or arg == "--bin":
            config.bin = safe_string()
        elif arg == "-h" or arg == "--help":
            exit_print_help()
        else:
            if posarg == 0:
                config.hs_file = arg
                posarg += 1
                index += 1
            elif posarg == 1:
                config.hst_file = arg
                posarg += 1
                index += 1
            else:
                panic_print_help(f"Extra argument was given: {arg}")

    if config.hs_file is None:
        panic_print_help("No Haskell source code file was given")
    if config.hst_file is None:
        panic_print_help("No test case file was given")
                
    return config
    

def main():
    config = parse_args()

    with open(config.hs_file or "", "r", encoding="UTF-8") as r:
        hs_content = r.read()

    raw_tests = parse_hst_file(hst_file=config.hst_file or "")
    filtered_tests = filter_tests(raw_tests, config.tests, config.include_other_functions)
    generated_tests = generate_tests(functions=filtered_tests)

    runnable_tester_hs = f"{MODULE_RULES}\n{hs_content}\n{generated_tests}\n{TESTER_BOILERPLATE}"

    with tempfile.TemporaryDirectory() as tempdir:
        os.makedirs(tempdir, exist_ok=True)

        with open(os.path.join(tempdir, "test.hs"), "w", encoding="UTF-8") as w:
            w.write(runnable_tester_hs)

        subprocess.call([
            config.bin or "runghc",
            "-Wno-x-partial",
            os.path.join(tempdir, "test.hs")
        ])


def filter_tests(functions: dict[str, list[str]], filters: dict[str, Callable[[int], bool]], include_other_functions: bool) -> dict[str, list[tuple[int, str]]]:
    out = {}

    filtered = len(filters) != 0
    for function, tests in functions.items():
        if not filtered or (function not in filters and include_other_functions):
            out[function] = [ (i+1, test_code) for (i, test_code) in enumerate(tests) ]
            continue

        if function not in filters:
            continue

        filtered_tests = []
        predicate = filters[function]
        for i, test_code in enumerate(tests):
            test_i = i+1
            if predicate(test_i):
                filtered_tests.append((test_i, test_code))

        out[function] = filtered_tests

    return out
        

def generate_tests(functions: dict[str, list[tuple[int, str]]]) -> str:
    lines = []

    lines.append("[")
    for i, function in enumerate(functions.keys()):
        tests = functions[function]

        if i != 0:
            lines.append(",")
        lines.append("(")
        lines.append(f"\"{function}\",")
        lines.append("[")

        for j, test in enumerate(tests):
            (test_i, test_code) = test
            start = "  " if j == 0 else ", "
            lines.append(start + "(" + str(test_i) + ", \"" + test_code.replace("\"", "\\\"") + "\"" + ", " + test_code + ")")
            # lines.append(f" {start}(\"{test.replace("\"", "\\\"")}\", {test})")
        
        lines.append("]")
        lines.append(")")
    lines.append("]")
        
    return "\n".join([TESTS_SIGNATURE, TESTS_DEFINITION] + [" " + line for line in lines])
    

def parse_hst_file(hst_file: str) -> dict[str, list[str]]:
    with open(hst_file, "r", encoding="UTF-8") as r:
        hst_content = r.read()

    hst_lines = hst_content.split("\n")

    current_function = ""
    tests: dict[str, list[str]] = {}

    for i, hst_line in enumerate(hst_lines):
        if hst_line.strip() == "":
            continue

        if hst_line.startswith("--f"):
            hst_line_parts = hst_line.split(" ")
            if len(hst_line_parts) < 2:
                panic(f"Invalid testfile: function name on line {i+1} cannot be parsed!")
            
            current_function = hst_line_parts[1]
            continue

        if hst_line.startswith("--"):
            continue

        if current_function == "":
            panic("Invalid testfile: testcase found before a function name is given!")

        if current_function not in tests:
            tests[current_function] = []

        tests[current_function].append(hst_line.strip())

    return tests


if __name__ == "__main__":
    main()
