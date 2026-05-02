#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>

#include "../rpc_lib/c/include/cJSON.h"
#include "../rpc_lib/c/include/rpc_server_stub.h"
#include "functions.h"

// ============================================================================
// Helper utilities
// ============================================================================

bool parse_int32(cJSON *json, int32_t *out) {
    if (!cJSON_IsNumber(json)) {
        return false;
    }
    *out = json->valueint;
    if (*out < INT32_MIN || *out > INT32_MAX) {
        return false;
    }
    return true;
}

bool parse_double(cJSON *json, double *out) {
    if (!cJSON_IsNumber(json)) {
        return false;
    }
    *out = json->valuedouble;
    return true;
}

cJSON *handle_add(cJSON *args) {
    // TODO: Implementation wrapper for add_impl is provided as reference
    // 1. Validate args: should be a JSON array of exactly two integers.
    // 2. Extract integer arguments.
    // 3. Call add_impl and return the result as cJSON.

    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 2) return NULL;
    cJSON *a_item = cJSON_GetArrayItem (args, 0);
    cJSON *b_item = cJSON_GetArrayItem (args, 1);
    int32_t a, b;
    if (!parse_int32 (a_item, &a) || !parse_int32 (b_item, &b)) return NULL;
    cJSON *result = cJSON_CreateNumber (add_impl (a, b));
    return result;
    
}

cJSON *handle_greet(cJSON *args) {
    // TODO: Implement wrapper for greet_impl
    // 1. Validate args: should be a JSON array containing one string.
    // 2. Extract string argument.
    // 3. Call greet_impl and return the result as cJSON.

    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *name_item = cJSON_GetArrayItem (args, 0);
    if (!cJSON_IsString (name_item)) return NULL;
    char *greeting = greet_impl (name_item->valuestring);
    if (!greeting) return NULL;
    cJSON *result = cJSON_CreateString (greeting);
    free (greeting);
    return result;
}

cJSON *handle_is_positive(cJSON *args) {
    // TODO: Implement wrapper for is_positive_impl
    // 1. Validate args: should be a JSON array containing one numeric value.
    // 2. Extract numeric argument.
    // 3. Call is_positive_impl and return the boolean result as cJSON.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *num_item = cJSON_GetArrayItem (args, 0);
    double num;
    if (!parse_double(num_item, &num)) return NULL;
    cJSON *result = cJSON_CreateBool (is_positive_impl (num));
    return result;
}

cJSON *handle_echo(cJSON *args) {
    // TODO: Implement echo function
    // 1. Validate args: should be a JSON array containing exactly one argument.
    // 2. Return the first argument directly.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *arg = cJSON_GetArrayItem (args, 0);
    if (!arg) return NULL;
    cJSON *copy = cJSON_Duplicate (arg, 1);
    return copy;
}

cJSON *handle_no_return(cJSON *args) {
    // TODO: Implement wrapper for no_return_impl
    // 1. Validate args: should be an empty JSON array.
    // 2. Call no_return_impl.
    // 3. Return JSON null.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 0) return NULL;
    no_return_impl ();
    return cJSON_CreateNull ();
}

cJSON *handle_divide(cJSON *args) {
    // TODO: Implement wrapper for divide_impl
    // 1. Validate args: should be a JSON array containing exactly two integers.
    // 2. Extract integer arguments.
    // 3. Call divide_impl and return the result as cJSON.
    // 4. Handle errors in division.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 2) return NULL;
    cJSON *a_item = cJSON_GetArrayItem (args, 0);
    cJSON *b_item = cJSON_GetArrayItem (args, 1);
    int32_t a, b;
    if (!parse_int32 (a_item, &a) || !parse_int32 (b_item, &b)) return NULL;
    bool err = b == 0;
    cJSON *result = cJSON_CreateNumber (divide_impl (a, b, &err));
    if (err) return NULL;
    return result;
}

cJSON *handle_sum_array(cJSON *args) {
    // TODO: Implement wrapper for sum_array_impl
    // 1. Validate args: should be a JSON array containing one element, which is an array of integers.
    // 2. Extract numbers from the inner JSON array into an int32_t array.
    // 3. Call sum_array_impl with the array.
    // 4. Convert the integer result back to cJSON.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *arr = cJSON_GetArrayItem (args, 0);
    if (!cJSON_IsArray (arr)) return NULL;
    int size = cJSON_GetArraySize (arr);
    int32_t *number = malloc (size * sizeof (int32_t));
    if (!number) return NULL;
    for (int i = 0;i < size;++i)
    {
        cJSON *item = cJSON_GetArrayItem (arr, i);
        if (!parse_int32 (item, &number[i]))
        {
            free (number);
            return NULL;
        }
    }
    int32_t result = sum_array_impl (number, size);
    free (number);
    return cJSON_CreateNumber (result);
}

cJSON *handle_process_person(cJSON *args) {
    // TODO: Implement wrapper for process_person_impl
    // 1. Validate args: should be a JSON array containing one element, which is an object.
    // 2. Validate the object has "name" (C string), "age" (int), "is_student" (bool) fields.
    // 3. Create a Person struct from the JSON object.
    // 4. Call process_person_impl with the struct.
    // 5. Convert the C string result back to cJSON.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *obj = cJSON_GetArrayItem (args, 0);
    if (!cJSON_IsObject (obj)) return NULL;
    cJSON *name_item = cJSON_GetObjectItemCaseSensitive (obj, "name");
    cJSON *age_item = cJSON_GetObjectItemCaseSensitive (obj, "age");
    cJSON *is_student_item = cJSON_GetObjectItemCaseSensitive (obj, "is_student");
    if (!cJSON_IsString (name_item) || !cJSON_IsNumber (age_item) || !cJSON_IsBool (is_student_item)) return NULL;
    struct Person p;
    size_t name_len = strlen(name_item->valuestring) + 1;
    p.name = malloc (name_len);
    if (!p.name) return NULL;
    memcpy (p.name, name_item->valuestring, name_len);
    p.age = age_item->valueint;
    p.is_student = cJSON_IsTrue (is_student_item);
    char *result_str = process_person_impl (&p);
    if (!result_str) return NULL;
    cJSON *result = cJSON_CreateString (result_str);
    free (result_str);
    return result;
}

cJSON *handle_get_greetings(cJSON *args) {
    // TODO: Implement wrapper for get_greetings_impl
    // 1. Validate args: should be a JSON array containing one element, which is an array of strings.
    // 2. Extract names from the inner JSON array into a C string array.
    // 3. Call get_greetings_impl with the array.
    // 4. Convert the resulting C string array back to a JSON array of strings.
    
    if (!cJSON_IsArray (args) || cJSON_GetArraySize (args) != 1) return NULL;
    cJSON *names_arr = cJSON_GetArrayItem (args, 0);
    if (!cJSON_IsArray (names_arr)) return NULL;
    int size = cJSON_GetArraySize (names_arr);
    char **name = malloc (size * sizeof (char*));
    if (!name) return NULL;
    for (int i = 0;i < size;++i)
    {
        cJSON *item = cJSON_GetArrayItem (names_arr, i);
        if (!cJSON_IsString (item)) {free (name);return NULL;}
        size_t len = strlen (item->valuestring) + 1;
        name[i] = malloc (len);
        if (!name[i]) {free (name);return NULL;}
        memcpy (name[i], item->valuestring, len);
    }
    char **greetings = get_greetings_impl (name, size);
    free (name);
    if (!greetings) return NULL;
    cJSON *result_arr = cJSON_CreateArray ();
    if (!result_arr)
    {
        for (int i = 0;i < size;++i) free (greetings[i]);
        free (greetings);
        return NULL;
    }
    for (int i = 0;i < size;++i)
    {
        cJSON_AddItemToArray (result_arr, cJSON_CreateString (greetings[i]));
        free (greetings[i]);
    }
    free (greetings);
    return result_arr;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: server <port>\n");
        return 1;
    }

    int port = atoi(argv[1]);
    if (port <= 0 || port > 65535) {
        fprintf(stderr, "Invalid port number: %s\n", argv[1]);
        return 1;
    }

    rpc_server_t *server = rpc_server_create(port);
    if (!server) {
        fprintf(stderr, "Failed to create RPC server on port %d\n", port);
        return 1;
    }

    // Register all RPC handlers
    rpc_server_register_function(server, "add", handle_add);
    rpc_server_register_function(server, "greet", handle_greet);
    rpc_server_register_function(server, "is_positive", handle_is_positive);
    rpc_server_register_function(server, "echo", handle_echo);
    rpc_server_register_function(server, "no_return", handle_no_return);
    rpc_server_register_function(server, "divide", handle_divide);
    rpc_server_register_function(server, "sum_array", handle_sum_array);
    rpc_server_register_function(server, "process_person", handle_process_person);
    rpc_server_register_function(server, "get_greetings", handle_get_greetings);

    // Start server (blocking call)
    rpc_server_start(server);
    
    // Cleanup (reached only if server stops gracefully)
    rpc_server_destroy(server);
    free(server);
    printf("Server exiting.\n");
    return 0;
}

