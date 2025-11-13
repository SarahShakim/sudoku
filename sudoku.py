import random
import copy

DIFFICULTY = {
    "easy":   {"min_clues": 40, "max_clues": 45},
    "medium": {"min_clues": 32, "max_clues": 38},
    "hard":   {"min_clues": 26, "max_clues": 31},
}

N = 9

def board_copy(board):
    return [row[:] for row in board]

def make_symmetry_pairs():
    pairs = []
    seen = set()
    for r in range(N):
        for c in range(N):
            r2, c2 = (N-1-r, N-1-c)
            a, b = (r, c), (r2, c2)
            key = tuple(sorted([a, b]))
            if key in seen:
                continue
            seen.add(key)
            is_pair = (a != b)
            pairs.append((a[0], a[1], b[0], b[1], is_pair))
    random.shuffle(pairs)
    return pairs

def generate_puzzle(difficulty="medium", symmetric=True, max_attempts=10):
    """
    Generate a unique-solution puzzle.
    - difficulty: 'easy' | 'medium' | 'hard'
    - symmetric: remove cells in rotational symmetry pairs for aesthetics
    """

    difficulty = difficulty if difficulty in DIFFICULTY else "medium"
    full = generate_full_board()
    puzzle = board_copy(full)

    # How many clues we want to keep
    target = random.randint(DIFFICULTY[difficulty]["min_clues"], DIFFICULTY[difficulty]["max_clues"])
    clues = N * N
    
    attempts = 0

    # Precompute cell order
    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)

    def symmetric_pair(r, c):
        return (8 - r, 8 - c)

    idx = 0
    while clues > target and attempts < 2000 and idx < len(cells):
        r, c = cells[idx]
        idx += 1

        if puzzle[r][c] == 0:
            continue

        if symmetric:
            r2, c2 = symmetric_pair(r, c)
        else:
            r2, c2 = r, c

        v1 = puzzle[r][c]
        v2 = puzzle[r2][c2]

        puzzle[r][c] = 0
        removed = 1
        if (r2, c2) != (r, c) and puzzle[r2][c2] != 0:
            puzzle[r2][c2] = 0
            removed = 2

        test = copy.deepcopy(puzzle)
        if solve_count(test, limit=2) == 1:
            clues -= removed
            attempts = 0
        else:
            puzzle[r][c] = v1
            if removed == 2:
                puzzle[r2][c2] = v2
            attempts += 1
            if attempts > max_attempts:
                symmetric = False
                attempts = 0

    return puzzle

def generate_full_board():
    board = [[0 for _ in range(9)] for _ in range(9)]
    solve_randomized(board)
    return board

def solve(board):
    """Standard backtracking solver (mutates board)."""
    find = find_empty(board)
    if not find:
        return True
    r, c = find
    for n in range(1, 10):
        if valid(board, n, (r, c)):
            board[r][c] = n
            if solve(board):
                return True
            board[r][c] = 0
    return False

def solve_randomized(board):
    """Backtracking with randomized number order (for generator)."""
    find = find_empty(board)
    if not find:
        return True
    r, c = find
    nums = list(range(1, 10))
    random.shuffle(nums)
    for n in nums:
        if valid(board, n, (r, c)):
            board[r][c] = n
            if solve_randomized(board):
                return True
            board[r][c] = 0
    return False

def solve_count(board, limit=2):
    """Count solutions up to 'limit' to test uniqueness. Returns count (<=limit)."""
    count = 0

    def backtrack():
        nonlocal count
        if count >= limit:
            return
        find = find_empty(board)
        if not find:
            count += 1
            return
        r, c = find
        for n in range(1, 10):
            if valid(board, n, (r, c)):
                board[r][c] = n
                backtrack()
                board[r][c] = 0
                if count >= limit:
                    return

    backtrack()
    return count

def find_empty(bo):
    for i in range(9):
        for j in range(9):
            if bo[i][j] == 0:
                return (i, j)
    return None

def valid(bo, num, pos):
    r, c = pos
    # row
    for j in range(9):
        if bo[r][j] == num and j != c:
            return False
    # col
    for i in range(9):
        if bo[i][c] == num and i != r:
            return False
    # box
    box_x = c // 3
    box_y = r // 3
    for i in range(box_y * 3, box_y * 3 + 3):
        for j in range(box_x * 3, box_x * 3 + 3):
            if bo[i][j] == num and (i, j) != (r, c):
                return False
    return True