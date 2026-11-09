colorize :: Bool -> String -> String
colorize success msg = (if success then "\ESC[32m" else "\ESC[31m") ++ msg ++ "\ESC[0m"

colorizedResult :: Bool -> String
colorizedResult passed = colorize passed (if passed then "PASSED" else "FAILED")

printTest :: (Int, String, Bool) -> IO()
printTest (i, test, passed) = do
    putStrLn $ "    => " ++ (colorizedResult passed) ++ " " ++ (show i) ++ " " ++ "{ " ++ test ++ " }"

printTestList :: [(Int, String, Bool)] -> IO()
printTestList ts = aux ts
    where
    aux [] = return ()
    aux (t:ts) = do
        printTest t
        aux ts

printFunction :: (String, [(Int, String, Bool)]) -> IO()
printFunction (fn, ts) = do
    let nTotal = length ts
    let nPassed = foldr (\(_, _, x) -> (+) $ if x then 1 else 0) 0 ts
    let passed = nTotal == nPassed

    putStrLn $ concat [colorizedResult passed, " [", show nPassed, "/", show nTotal, "] ", fn]
    printTestList ts
    putStrLn ""

printFunctionList :: [(String, [(Int, String, Bool)])] -> IO()
printFunctionList fs = sequence_ [ printFunction f | f <- fs ]

printSummary :: [Bool] -> IO()
printSummary ts = do
    let passed = and ts
    let nt = length ts
    let np = foldr (\x -> (+) (if x then 1 else 0)) 0 ts
    putStrLn $ "Summary: " ++ (colorizedResult passed) ++ " [" ++ (show np) ++ "/" ++ (show nt) ++ "]"

main :: IO()
main = do
    printFunctionList tests
    printSummary [ tst | (f, ts) <- tests, (tsi, tss, tst) <- ts ]
