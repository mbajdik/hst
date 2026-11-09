# Haskell tester
Script used to run a sequence of test cases for functions in a Haskell source file. This was made to quickly test university tasks/assignments against the given cases.

# Installation
To download just the script:
```sh
mkdir .bin
curl sh.mbajdik.me/hst > .bin/hst
chmod u+x ./bin/hst
```

Or manually download the repository and generate/build it yourself

# Test file syntax
```haskell
--f functionName (first word of a comment starting with --f starts a new block)
functionName 2 == 4
functionName 4 == 8

-- comments still work
```
This syntax is made really simple, because for its purpose it's perfectly sufficient. The only thing that matters is to be able to paste the given test cases and check them quickly.
Blocks can be started with whatever name - it doesn't need to be the function's name (the sole use of this feature is organization), the only requirement is that it should not contain whitespace (other words are disregarded)

# Builtin documentation
```
Haskell tester script
Usage: hst [OPTIONS] HS_FILE TEST_FILE

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
```
