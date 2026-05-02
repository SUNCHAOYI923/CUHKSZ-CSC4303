#ifndef FUNCTIONS_H
#define FUNCTIONS_H

#include <stdbool.h>
#include <stdint.h> // For int32_t

// --- Basic Data Type Functions ---
// Function prototypes using basic C types
// These are the functions that perform the actual logic.
// The wrappers in main.c will handle JSON conversion.

int32_t add_impl(int32_t a, int32_t b);
char* greet_impl(const char* name);
bool is_positive_impl(float num);
// For echo, the wrapper in main.c can handle returning the cJSON object directly
// For no_return, the wrapper handles returning cJSON_NULL
void no_return_impl();
int32_t divide_impl(int32_t numerator, int32_t denominator, bool *error); // Can have error


// --- Complex Data Type Functions---

struct Person{
    char *name; // Owned by caller or static
    int32_t age;
    bool is_student;
};

// Function prototypes
int32_t sum_array_impl(const int32_t *numbers, int size);
char* process_person_impl(const struct Person *person_data);
char** get_greetings_impl(char** names, int count);


#endif // FUNCTIONS_H
