board = [
    [7,8,0,4,0,0,1,2,0],
    [6,0,0,0,7,5,0,0,9],
    [0,0,0,6,0,1,0,7,8],
    [0,0,7,0,4,0,2,6,0],
    [0,0,1,0,5,0,9,3,0],
    [9,0,4,0,6,0,0,0,5],
    [0,7,0,3,0,0,0,1,2],
    [1,2,0,0,0,7,4,0,0],
    [0,4,9,2,0,6,0,0,7]
]


def solve(bo): #recursive algorithm with backtracking
    find = find_empty(bo)
    if not find:
        return True
    else:
        row, col = find
#loop through values from 1-9 and try them in the solution
    for i in range(1,10):
        if valid(bo, i, (row, col)):
            bo[row][col] = i #plug in the value if valid

            if solve(bo): #if the solution doesnt fit, use backtracking
                return True

            bo[row][col] = 0 #backtracking. if there is a mistake, we will reset it to blank and go back and try another number

    return False


def valid(bo, num, pos):#check if the board is valid
    # Check row
    for i in range(len(bo[0])):
        if bo[pos[0]][i] == num and pos[1] != i:#checks though each position in the row and see if it can insert a value
            return False

    # Check column
    for i in range(len(bo)):
        if bo[i][pos[1]] == num and pos[0] != i:#loops through every row going down to see the position
            return False

    # Check the little square within the smaller grids
    #determine which box we're in:
    box_x = pos[1] // 3
    box_y = pos[0] // 3
    #loop through all 9 elements in the box and make sure that the numbers are not repeated:
    for i in range(box_y*3, box_y*3 + 3): #to get to exact index
        for j in range(box_x * 3, box_x*3 + 3):
            if bo[i][j] == num and (i,j) != pos:
                return False

    return True #if we found a valid position


def print_board(bo):
    for i in range(len(bo)):
        if i % 3 == 0 and i != 0:
            print("- - - - - - - - - - - - - ")

        for j in range(len(bo[0])):
            if j % 3 == 0 and j != 0:
                print(" | ", end="")

            if j == 8:
                print(bo[i][j])
            else:
                print(str(bo[i][j]) + " ", end="")


def find_empty(bo):
    for i in range(len(bo)):
        for j in range(len(bo[0])):
            if bo[i][j] == 0:
                return (i, j)  # row, col

    return None #if there are no blank squares

print(print_board(board))
print(solve(board))
print("____________________")
print(print_board(board))

#use this file to check and see if the entry is valid when people use the GUI