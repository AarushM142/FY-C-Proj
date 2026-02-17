#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define SIZE 6
#define MINES 8

typedef struct {
    int isMine;
    int isRevealed;
    int adjacentMines;
} Cell;

typedef struct {
    Cell board[SIZE][SIZE];
    int cellsRevealed;
    int minesHit;
} Game;

void floodFill(Game *game, int r, int c) {
    if (r < 0 || r >= SIZE || c < 0 || c >= SIZE || game->board[r][c].isRevealed) return;
    game->board[r][c].isRevealed = 1;
    game->cellsRevealed++;
    if (game->board[r][c].adjacentMines == 0 && !game->board[r][c].isMine) {
        for (int i = -1; i <= 1; i++)
            for (int j = -1; j <= 1; j++)
                floodFill(game, r + i, c + j);
    }
}

Game* create_game() {
    Game* game = (Game*)malloc(sizeof(Game));
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            game->board[i][j].isMine = 0;
            game->board[i][j].isRevealed = 0;
            game->board[i][j].adjacentMines = 0;
        }
    }
    int placed = 0;
    srand(time(NULL));
    while (placed < MINES) {
        int r = rand() % SIZE, c = rand() % SIZE;
        if (!game->board[r][c].isMine) {
            game->board[r][c].isMine = 1;
            placed++;
        }
    }
    for (int i = 0; i < SIZE; i++) {
        for (int j = 0; j < SIZE; j++) {
            if (game->board[i][j].isMine) continue;
            int count = 0;
            for (int di = -1; di <= 1; di++)
                for (int dj = -1; dj <= 1; dj++) {
                    int ni = i + di, nj = j + dj;
                    if (ni >= 0 && ni < SIZE && nj >= 0 && nj < SIZE && game->board[ni][nj].isMine) count++;
                }
            game->board[i][j].adjacentMines = count;
        }
    }
    game->cellsRevealed = 0;
    game->minesHit = 0;
    return game;
}

int is_cell_revealed(Game *game, int r, int c) { return game->board[r][c].isRevealed; }
int is_cell_mine(Game *game, int r, int c) { return game->board[r][c].isMine; }
int get_adjacent_count(Game *game, int r, int c) { return game->board[r][c].adjacentMines; }

void force_reveal(Game *game, int r, int c) {
    if (game) floodFill(game, r, c);
}

int process_move(Game *game, int r, int c) {
    if (game->board[r][c].isMine) {
        game->minesHit++;
        return (game->minesHit == 1) ? 1 : -1; 
    }
    floodFill(game, r, c);
    if (game->cellsRevealed == (SIZE * SIZE - MINES)) return 2;
    return 0;
}