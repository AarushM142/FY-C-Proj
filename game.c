#include <stdlib.h>
#include <time.h>

int deck[52];
int top_card = 0;

void shuffle_deck()
{
    for (int i = 0; i < 52; i++)
        deck[i] = i;
    for (int i = 51; i > 0; i--)
    {
        int j = rand() % (i + 1);
        int temp = deck[i];
        deck[i] = deck[j];
        deck[j] = temp;
    }
    top_card = 0;
}

int draw_card()
{
    if (top_card >= 52)
        shuffle_deck();
    return deck[top_card++];
}

int card_to_value(int card)
{
    int rank = card % 13;
    if (rank == 0)
        return 11; // Ace
    if (rank >= 9)
        return 10; // 10, J, Q, K
    return rank + 1;
}

int calculate_score(int *cards, int count)
{
    int score = 0, aces = 0;
    for (int i = 0; i < count; i++)
    {
        int val = card_to_value(cards[i]);
        score += val;
        if (val == 11)
            aces++;
    }
    while (score > 21 && aces > 0)
    {
        score -= 10;
        aces--;
    }
    return score;
}

int dealer_logic(int *hand, int current_count)
{
    int count = current_count;
    while (calculate_score(hand, count) < 17 && count < 10)
    {
        hand[count] = draw_card();
        count++;
    }
    return count;
}

// Check if hand is a natural blackjack (21 with exactly 2 cards)
int is_blackjack(int *cards, int count)
{
    if (count != 2)
        return 0;
    return calculate_score(cards, 2) == 21;
}

// Check if two cards can be split (same rank)
int can_split(int card1, int card2)
{
    int rank1 = card1 % 13;
    int rank2 = card2 % 13;
    return rank1 == rank2;
}

// Get card rank for display
int get_rank(int card)
{
    return card % 13;
}

// Check if hand contains an Ace
int has_ace(int *cards, int count)
{
    for (int i = 0; i < count; i++)
    {
        if (cards[i] % 13 == 0)
            return 1;
    }
    return 0;
}

// Calculate score treating Ace as specified value (1 or 11)
int calculate_score_with_ace(int *cards, int count, int ace_value)
{
    int score = 0;
    int aces = 0;

    for (int i = 0; i < count; i++)
    {
        int rank = cards[i] % 13;
        int val;

        if (rank == 0)
        { // Ace
            val = ace_value;
            aces++;
        }
        else if (rank >= 9)
        {
            val = 10;
        }
        else
        {
            val = rank + 1;
        }
        score += val;
    }

    // Adjust other aces if needed (keep only one ace as 11)
    while (score > 21 && aces > 1)
    {
        score -= 10;
        aces--;
    }
    return score;
}

void init_engine()
{
    srand(time(NULL));
    shuffle_deck();
}