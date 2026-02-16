#include <stdlib.h>

char board[3][3];

void init_ttt() {
    for(int i = 0; i < 3; i++)
        for(int j = 0; j < 3; j++)
            board[i][j] = ' ';
}

int place_move(int row, int col, char player) {
    if (board[row][col] == ' ') {
        board[row][col] = player;
        return 1;
    }
    return 0;
}

int check_win() {
    for(int i = 0; i < 3; i++) {
        if(board[i][0] == board[i][1] && board[i][1] == board[i][2] && board[i][0] != ' ') return 1;
        if(board[0][i] == board[1][i] && board[1][i] == board[2][i] && board[0][i] != ' ') return 1;
    }
    if(board[0][0] == board[1][1] && board[1][1] == board[2][2] && board[0][0] != ' ') return 1;
    if(board[0][2] == board[1][1] && board[1][1] == board[2][0] && board[0][2] != ' ') return 1;
    return 0;
}

int check_draw() {
    for(int i = 0; i < 3; i++)
        for(int j = 0; j < 3; j++)
            if(board[i][j] == ' ') return 0;
    return 1;
}

char get_cell(int r, int c) {
    return board[r][c];
}