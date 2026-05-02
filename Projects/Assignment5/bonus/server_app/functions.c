#include "functions.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// ============================================================================
// Basic Data Type Function Implementations
// ============================================================================

// Simple function that adds two integers
int32_t add_impl(int32_t a, int32_t b) {
    return a + b;
}

// Function that concatenates "Hello, " with the provided name and returns a new string
char* greet_impl(const char *name) {
    // Calculate needed buffer size: "Hello, " + name + "!" + null
    size_t len = strlen(name) + 9;
    
    char *result = malloc(len);
    
    snprintf(result, len, "%s%s%s", "Hello, ", name, "!");
    return result;
}

// Function that checks if a number is positive
bool is_positive_impl(float num) {
    return num > 0;
}

// echo is handled directly in the main.c wrapper

// Function that takes no arguments and returns nothing
void no_return_impl() {
    // Function that does something but returns nothing
    puts("Executing no_return_impl()...");
}

// Function that divides two integers and handles division by zero
int32_t divide_impl(int32_t numerator, int32_t denominator, bool *error) {
    if (denominator == 0) {
        *error = 1;
        return 0;
    }
    return numerator / denominator;
}

// ============================================================================
// Complex Data Type Function Implementations
// ============================================================================

// Function that sums an array of integers
int32_t sum_array_impl(const int32_t *numbers, int size) {
    int32_t sum = 0;
    for (int i = 0; i < size; i++) {
        sum += numbers[i];
    }
    return sum;
}

// Function that processes a Person struct and returns a string summary
char* process_person_impl(const struct Person *person_data) {
    const char *status = person_data->is_student ? "a student" : "not a student";
    // Estimate buffer size: fixed parts + name + age digits + null
    // Age: max 10 digits for int32 + sign
    // Not a student: 13
    size_t len = 55 + strlen(person_data->name);
    char *result = malloc(len);

    snprintf(result, len, 
        "Processed person: %s, age %d, is %s.",
        person_data->name, 
        person_data->age, 
        status);
    return result;
}

// Function that takes an array of names and returns an array of greetings
char** get_greetings_impl(char** names, int count) {
    char **greetings = malloc(count * sizeof(char*));
    
    for (size_t i = 0; i < (size_t)count; i++) {
        greetings[i] = greet_impl(names[i]);
    }

    return greetings;
}