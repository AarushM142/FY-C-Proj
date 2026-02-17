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

// core score logic with automatic Ace adjustment
int calculate_score(int *cards, int count) {
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

int dealer_logic(int *hand, int current_count) {
    int count = current_count;
    while (calculate_score(hand, count) < 17 && count < 10) {
        hand[count] = draw_card();
        count++;
    }
    return count;
}

// --- ADDED BACK FOR YOUR PYTHON UI ---

int calculate_score_with_ace(int *cards, int count, int ace_value) {
    int score = 0;
    int other_aces = 0;

    for (int i = 0; i < count; i++) {
        int rank = cards[i] % 13;
        if (rank == 0) {
            score += ace_value;
            if (ace_value == 11) other_aces++;
        } else if (rank >= 9) {
            score += 10;
        } else {
            score += rank + 1;
        }
    }
    // Simple logic to prevent this specific helper from busting if multiple aces exist
    while (score > 21 && other_aces > 0) {
        score -= 10;
        other_aces--;
    }
    return score;
}

int can_split(int card1, int card2) {
    return (card1 % 13 == card2 % 13);
}

int get_rank(int card) {
    return card % 13;
}

int has_ace(int *cards, int count) {
    for (int i = 0; i < count; i++) {
        if (cards[i] % 13 == 0) return 1;
    }
    return 0;
}

int is_blackjack(int *cards, int count) {
    if (count != 2) return 0;
    return calculate_score(cards, 2) == 21;
}

void init_engine() {
    srand(time(NULL));
    shuffle_deck();
}