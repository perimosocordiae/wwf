
module Main where

import Data.Char (toUpper)
import Data.List (intercalate)
import Scrabble
import System.Directory (getCurrentDirectory)
import System.Environment

run_solver :: FilePath -> String -> Int -> IO ()
run_solver boardfile hand num_moves = do
  board <- make_board boardfile
  path <- getCurrentDirectory
  dictionary <- read_dictionary path
  mapM_ (show_moves board) $ take num_moves $ top_moves board dictionary hand

show_moves :: Board -> (Int,[String],Move) -> IO ()
show_moves board (score,made_words,move) = do
  putStrLn $ (show score) ++ " " ++ (intercalate ", " made_words)
  putStrLn $ board_to_string $ update_board board move

main :: IO ()
main = do
  args <- getArgs
  case length args of
    2 -> run_solver (args!!0) (map toUpper (args!!1)) 10
    3 -> run_solver (args!!0) (map toUpper (args!!1)) $ read (args!!2)
    _ -> error "Usage: ./scrabble boardfile hand"
