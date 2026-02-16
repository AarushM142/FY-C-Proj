#include <stdlib.h>
#include <time.h>

int deck[52];
int top_card = 0;

void shuffle_deck() {
    for (int i = 0; i < 52; i++) deck[i] = i;
    for (int i = 51; i > 0; i--) {
        int j = rand() % (i + 1);
        int temp = deck[i];
        deck[i] = deck[j];
        deck[j] = temp;
    }
    top_card = 0;
}

int draw_card() {
    if (top_card >= 52) shuffle_deck();
    return deck[top_card++];
}

int card_to_value(int card) {
    int rank = card % 13;
    if (rank == 0) return 11; // Ace
    if (rank >= 9) return 10; // 10, J, Q, K
    return rank + 1;
}

int calculate_score(int* cards, int count) {
    int score = 0, aces = 0;
    for (int i = 0; i < count; i++) {
        int val = card_to_value(cards[i]);
        score += val;
        if (val == 11) aces++;
    }
    while (score > 21 && aces > 0) {
        score -= 10;
        aces--;
    }
    return score;
}

int dealer_logic(int* hand, int current_count) {
    int count = current_count;
    while (calculate_score(hand, count) < 17 && count < 10) {
        hand[count] = draw_card();
        count++;
    }
    return count;
}

void init_engine() {
    srand(time(NULL));
    shuffle_deck();
}