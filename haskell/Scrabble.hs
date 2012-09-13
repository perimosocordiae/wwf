
module Scrabble (
  make_board,top_moves,read_dictionary,update_board,board_to_string,Board,Move
  ) where

import Control.Monad (filterM)
import qualified Data.ByteString.Char8 as B
import Data.Char (toUpper,isSpace)
import qualified Data.Map as Map
import Data.Maybe
import Data.List
import qualified Data.Set as Set
import GHC.Exts (groupWith)
import System.FilePath

--import Debug.Trace (trace)

type WordList = Set.Set B.ByteString
type Pos = (Int,Int)
type Play = [Pos]
type Letter = (Char,Int,Int)
type Move = [Letter]
data Board = Board [[Space]]
data Space = Blank | WordBonus Bonus | LetterBonus Bonus | Tile Char
data Bonus = Dbl | Tpl  -- named to avoid conflict with Double

space_to_char :: Space -> Char
space_to_char Blank = '_'
space_to_char (WordBonus Dbl) = '@'
space_to_char (WordBonus Tpl) = '#'
space_to_char (LetterBonus Dbl) = '2'
space_to_char (LetterBonus Tpl) = '3'
space_to_char (Tile c) = c

char_to_space :: Char -> Space
char_to_space '_' = Blank
char_to_space '@' = WordBonus Dbl
char_to_space '#' = WordBonus Tpl
char_to_space '2' = LetterBonus Dbl
char_to_space '3' = LetterBonus Tpl
char_to_space c   = Tile (toUpper c)

board_to_string :: Board -> String
board_to_string (Board b) = unlines $ [map space_to_char row | row <- b]

string_to_board :: String -> Board
string_to_board s = Board [map char_to_space line | line <- lines s]

get_space :: Board -> Int -> Int -> Space
get_space (Board b) r c = (b !! r) !! c

board_size :: Int
board_size = 15

bingo_bonus :: Int
bingo_bonus = 35

is_letter :: Space -> Bool
is_letter (Tile x) = (x >= 'A') && (x <= 'Z')
is_letter _ = False

base_value :: Space -> Int
base_value (Tile 'X') = 8
base_value (Tile x)
  | x `elem` "DLNU" = 2
  | x `elem` "GHY" = 3
  | x `elem` "BCFMPW" = 4
  | x `elem` "KV" = 5
  | x `elem` "JQZ" = 10
  | x `elem` "AEIORST" = 1
base_value _ = 0

word_to_string :: Move -> B.ByteString
word_to_string move = B.pack [toUpper x | (x,_,_) <- move] 

score_one_move :: Board -> Move -> Int
score_one_move board move = word_score * word_mult where
  word_score = sum $ map score_letter move
  word_mult = product $ map letter_multiplier move
  score_letter (x,r,c) = case get_space board r c of
    LetterBonus Dbl -> (base_value (Tile x)) * 2
    LetterBonus Tpl -> (base_value (Tile x)) * 3
    _               -> (base_value (Tile x))
  letter_multiplier (_,r,c) = case get_space board r c of
    WordBonus Dbl -> 2
    WordBonus Tpl -> 3
    _             -> 1

default_board :: Board
default_board = string_to_board $ unlines [
  "___#__3_3__#___",
  "__2__@___@__2__",
  "_2__2_____2__2_",
  "#__3___@___3__#",
  "__2___2_2___2__",
  "_@___3___3___@_",
  "3___2_____2___3",
  "___@_______@___",
  "3___2_____2___3",
  "_@___3___3___@_",
  "__2___2_2___2__",
  "#__3___@___3__#",
  "_2__2_____2__2_",
  "__2__@___@__2__",
  "___#__3_3__#___"]

make_board :: FilePath -> IO Board
make_board filename = do
  raw <- readFile filename
  --assert len(data) == board_size and len(data[0]) == board_size
  return $ merge_boards default_board (string_to_board raw)

merge_boards :: Board -> Board -> Board
merge_boards (Board orig) (Board new) = Board $ map merge_rows $ zip orig new where
  merge_rows (orow, nrow) = map merge_spaces $ zip orow nrow
  merge_spaces (o,n)
    | is_letter n = n
    | otherwise   = o

update_board :: Board -> Move -> Board
update_board board [] = board
update_board (Board b) ((x,r,c):ls) = update_board new_board ls where
  (top, row:bot) = splitAt r b
  (left, _:right) = splitAt c row
  new_board = Board $ top ++ (left ++ (Tile x):right):bot

takeWhileJust :: [Maybe a] -> [a]
takeWhileJust [] = []
takeWhileJust (x:xs) = case x of
  Nothing -> []
  Just a  -> a:(takeWhileJust xs)

find_words :: Board -> Map.Map Pos Char -> Pos -> [Move]
find_words board@(Board b) playdict (r,c) = filter ((>=2).length) $ catMaybes [horiz_word, vert_word] where
  --TODO: DRY this up
  horiz_word :: Maybe Move
  horiz_word = do
    let row = b !! r
    start_c <- case c of
      0 -> Just 0
      _ -> case dropWhile (\x -> is_letter (row!!x)) [c-1,c-2..0] of
        [] -> Nothing
        (left_c:_) -> Just (left_c+1)
    res <- case (start_c > 0) && ((r,start_c-1) `Map.member` playdict) of
      True -> Nothing
      False -> Just $ takeWhileJust $ map make_letter [start_c..board_size-1] where
        make_letter :: Int -> Maybe Letter
        make_letter x = case (row!!x) of
          Tile l -> Just (l,r,x)
          _ -> do 
            l <- (r,x) `Map.lookup` playdict
            return (l,r,x)
    return res
  vert_word :: Maybe Move
  vert_word = do
    let col = [get_space board x c | x <- [0..board_size-1]]
    start_r <- case r of
      0 -> Just 0
      _ -> case dropWhile (\x -> is_letter (col!!x)) [r-1,r-2..0] of
        [] -> Nothing  -- all spaces in this column are used
        (top_r:_) -> Just (top_r+1)
    res <- case start_r > 0 && (start_r-1,c) `Map.member` playdict of
      True -> Nothing
      False -> Just $ takeWhileJust $ map make_letter [start_r..board_size-1] where
        make_letter :: Int -> Maybe Letter
        make_letter x = case (col!!x) of
          Tile l -> Just (l,x,c)
          _ -> do
            l <- (x,c) `Map.lookup` playdict
            return (l,x,c)
    return res

valid_plays :: Board -> Map.Map Int [Play]
valid_plays board = Map.fromList $ map (\xs->(length (xs!!0),xs)) $ groupWith length (nub all_plays) where
  board_letter r c = is_letter $ get_space board r c
  -- precompute possible play locations
  all_plays :: [Play]
  all_plays = concatMap h_plays open_inds ++ concatMap v_plays open_inds
  open_inds = [(r,c) | r<-[0..board_size-1], c<-[0..board_size-1], not (board_letter r c)]
  plays :: [Play] -> [Play]
  -- scanl1 (++) turns [[a],[b],[c]] into [[a],[a,b],[a,b,c]]
  plays pos = filter (next_to_existing board) $ scanl1 (++) $ take 7 pos
  h_plays (r,c) = plays [[(r,ci)] | ci<-[c..board_size-1], not (board_letter r ci)]
  v_plays (r,c) = plays [[(ri,c)] | ri<-[r..board_size-1], not (board_letter ri c)]

-- "all words" doesn't mean they're in the dictionary
all_words :: Board -> Move -> [Move]
all_words board move = concatMap (find_words board pd) [(r,c) | (_,r,c)<-move]
  where pd = Map.fromList [((r,c),x) | (x,r,c) <- move]

score_move :: Board -> WordList -> Move -> Int
score_move board wordlist move = score + bonus where
  score = if made_strings `Set.isSubsetOf` wordlist
          then sum $ map (score_one_move board) made_words
          else 0
  made_words = all_words board move
  made_strings = Set.fromList $ map word_to_string made_words
  bonus = if length move == 7 then bingo_bonus else 0

next_to_existing :: Board -> Play -> Bool
next_to_existing board play = any next_to play where
  mid = board_size `div` 2
  board_letter r c = is_letter $ get_space board r c
  next_to (r,c)
    | r > 0 && board_letter (r-1) c = True
    | c > 0 && board_letter r (c-1) = True
    | r < board_size-1 && board_letter (r+1) c = True
    | c < board_size-1 && board_letter r (c+1) = True
    | (r == mid) && (c == mid) = True  -- first word always counts
    | otherwise = False

powerset :: [a] -> [[a]]
powerset = filterM (const [True, False])

letter_combos :: String -> [(Int,String)]
letter_combos hand = nub $ concatMap letter_combos' (all_hands hand) where
  all_hands :: String -> [String]
  all_hands h = all_hands' $ break ('.'==) h
  all_hands' (h,"") = [h]
  all_hands' (a,'.':b) = [(a++[x]++b') | x<-['A'..'Z'], b'<- all_hands b]
  all_hands' _ = error "Should never get here"
  letter_combos' h = [(length c, c) | combo<-(nub.powerset) h, c<-(nub.permutations) combo, c /= ""]

valid_moves :: Map.Map Int [Play] -> String -> [Move]
valid_moves v_plays hand = Set.toList valid_moves' where
  letter_plays :: (Int, String) -> Set.Set Move
  letter_plays (i,letters) = case Map.lookup i v_plays of
    Just plays -> Set.fromList $ map (make_move letters) plays
    Nothing    -> Set.empty
  make_move letters play = [(l,r,c) | (l,(r,c)) <- zip letters play]
  valid_moves' = Set.unions $ map letter_plays (letter_combos hand)

positive_scoring_moves :: Board -> WordList -> String -> [(Int,Move)]
positive_scoring_moves board wordlst hand = filter ((>0).fst) scored_plays where
  scored_plays = [(score_move board wordlst play, play) | play <- moves]
  moves = valid_moves (valid_plays board) hand

words_file :: FilePath
words_file = "../words.txt"

read_dictionary :: FilePath -> IO WordList
read_dictionary path = do
  file <- B.readFile $ combine path words_file
  return $ Set.fromList $ (map process_line) $ B.lines file where
    process_line line = B.map toUpper $ B.takeWhile (not.isSpace) line

top_moves :: Board -> WordList -> String -> [(Int,[String],Move)]
top_moves board wordlist hand = reverse $ sort moves where
  moves = [(s, made_words play, play)
           | (s,play)<-(positive_scoring_moves board wordlist (map toUpper hand))]
  made_words play = map (B.unpack.word_to_string) $ all_words board play
