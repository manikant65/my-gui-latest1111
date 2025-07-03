/*
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#ifdef _WIN32
    #include <windows.h>
    #define sleep_ms(ms) Sleep(ms)
#else
    #include <unistd.h>
    #define sleep_ms(ms) usleep((ms) * 1000)
#endif

void generate_key(char *key) {
    for (int i = 0; i < 256; i++) {
        key[i] = (rand() % 2) == 0 ? '0' : '1';
    }
    key[256] = '\0';
}

int main() {
    srand((unsigned int)time(NULL));

    FILE *output_file = fopen("output.txt", "w");
    if (output_file == NULL) {
        perror("Failed to open output.txt");
        return 1;
    }

    char key[257];
    int session_number = 0;
    char *var_val;
    scanf("%s",&var_val);

    while (session_number<200) {
        fprintf(output_file, "SESSION_NUMBER:%d\n", session_number);
        printf("SESSION_NUMBER:%d\n", session_number);
        fflush(stdout);
        fflush(output_file);

        fprintf(output_file, "SPD1_VALUES:\n");
        printf("SPD1_VALUES:\n");
        for (int i = 0; i < 40; i++) {
            int timestamp_spd1 = rand() % 10000;
            fprintf(output_file, "%d\n", timestamp_spd1);
            printf("%d\n", timestamp_spd1);
            fflush(stdout);
            fflush(output_file);
        }
        
        float spd1_decoy_randomness = (float)(rand() % 10000) / 10000.0;
        fprintf(output_file, "DECOY_STATE_RANDOMNESS_AT_SPD1:%.4f\n", spd1_decoy_randomness);
        printf("DECOY_STATE_RANDOMNESS_AT_SPD1:%.4f\n", spd1_decoy_randomness);
        fflush(stdout);
        fflush(output_file);

        fprintf(output_file, "SPD2_VALUES:\n");
        printf("SPD2_VALUES:\n");
        for (int i = 0; i < 40; i++) {
            int timestamp_spd2 = rand() % 10000;
            fprintf(output_file, "%d\n", timestamp_spd2);
            printf("%d\n", timestamp_spd2);
            fflush(stdout);
            fflush(output_file);
        }

        float visibility = (float)(rand() % 10000) / 10000.0;
        fprintf(output_file, "VISIBILITY_RATIO_IS:%.4f\n", visibility);
        printf("VISIBILITY_RATIO_IS:%.4f\n", visibility);
        fflush(stdout);
        fflush(output_file);

        float qber = (float)(rand() % 1000) / 100.0;
        fprintf(output_file, "SPD1_QBER_VALUE_IS:%.2f\n", qber);
        printf("SPD1_QBER_VALUE_IS:%.2f\n", qber);
        fflush(stdout);
        fflush(output_file);

        if (session_number % 2 == 0) {
            generate_key(key);
            fprintf(output_file, "NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:%d\n", 256);
            printf("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:%d\n", 256);
            fprintf(output_file, "KEY_BITS:%s\n", key);
            printf("KEY_BITS:%s\n", key);
            fflush(stdout);
            fflush(output_file);
        }

        if (session_number % 2 == 1) {
            float kbps = (float)(rand() % 1000) / 100.0;
            fprintf(output_file, "KEY_RATE_PER_SECOND_IS:%.2f\n", kbps);
            printf("KEY_RATE_PER_SECOND_IS:%.2f\n", kbps);
            fflush(stdout);
            fflush(output_file);
        }

        fprintf(output_file, "\n");
        printf("\n");
        fflush(stdout);
        fflush(output_file);

        session_number++;
        sleep_ms(500);
    }

    fclose(output_file);
    return 0;
}*/



#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

#ifdef _WIN32
    #include <windows.h>
    #define sleep_ms(ms) Sleep(ms)
#else
    #include <unistd.h>
    #define sleep_ms(ms) usleep((ms) * 1000)
#endif

void generate_key(char *key) {
    for (int i = 0; i < 256; i++) {
        key[i] = (rand() % 2) == 0 ? '0' : '1';
    }
    key[256] = '\0';
}

int main(int argc, char *argv[]) {

    srand((unsigned int)time(NULL));

    FILE *output_file = fopen("output.txt", "w");
    if (output_file == NULL) {
        perror("Failed to open output.txt");
        return 1;
    }

    // Check for command-line argument
    const char *var_val = (argc > 1 && argv[1] != NULL) ? argv[1] : "default_input";
    // Output the input string
    fprintf(output_file, "INPUT_STRING:%s\n", var_val);
    printf("INPUT_STRING:%s\n", var_val);
    fflush(stdout);
    fflush(output_file);

    char key[257];
    int session_number = 0;

    while (session_number < 200) {
        fprintf(output_file, "SESSION_NUMBER:%d\n", session_number);
        printf("SESSION_NUMBER:%d\n", session_number);
        fflush(stdout);
        fflush(output_file);


        fprintf(output_file, "SPD1_VALUES:\n");
        printf("SPD1_VALUES:\n");
        for (int i = 0; i < 40; i++) {
            int timestamp_spd1 = rand() % 10000;
            fprintf(output_file, "%d\n", timestamp_spd1);
            printf("%d\n", timestamp_spd1);
            fflush(stdout);
            fflush(output_file);
        }
        
        float spd1_decoy_randomness = (float)(rand() % 10000) / 10000.0;
        fprintf(output_file, "DECOY_STATE_RANDOMNESS_AT_SPD1:%.4f\n", spd1_decoy_randomness);
        printf("DECOY_STATE_RANDOMNESS_AT_SPD1:%.4f\n", spd1_decoy_randomness);
        fflush(stdout);
        fflush(output_file);

        fprintf(output_file, "SPD2_VALUES:\n");
        printf("SPD2_VALUES:\n");
        for (int i = 0; i < 40; i++) {
            int timestamp_spd2 = rand() % 10000;
            fprintf(output_file, "%d\n", timestamp_spd2);
            printf("%d\n", timestamp_spd2);
            fflush(stdout);
            fflush(output_file);
        }

        float visibility = (float)(rand() % 10000) / 10000.0;
        fprintf(output_file, "VISIBILITY_RATIO_IS:%.4f\n", visibility);
        printf("VISIBILITY_RATIO_IS:%.4f\n", visibility);
        fflush(stdout);
        fflush(output_file);

        float qber = (float)(rand() % 1000) / 100.0;
        fprintf(output_file, "SPD1_QBER_VALUE_IS:%.2f\n", qber);
        printf("SPD1_QBER_VALUE_IS:%.2f\n", qber);
        fflush(stdout);
        fflush(output_file);

        if (session_number % 2 == 0) {
            generate_key(key);
            fprintf(output_file, "NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:%d\n", 256);
            printf("NUMBER_OF_RX_KEY_BITS_AFTER_PRIVACY_AMPLIFICATION_IS:%d\n", 256);
            fprintf(output_file, "KEY_BITS:%s\n", key);
            printf("KEY_BITS:%s\n", key);
            fflush(stdout);
            fflush(output_file);
        }

        if (session_number % 2 == 1) {
            float kbps = (float)(rand() % 1000) / 100.0;
            fprintf(output_file, "KEY_RATE_PER_SECOND_IS:%.2f\n", kbps);
            printf("KEY_RATE_PER_SECOND_IS:%.2f\n", kbps);
            fflush(stdout);
            fflush(output_file);
        }

        fprintf(output_file, "\n");
        printf("\n");
        fflush(stdout);
        fflush(output_file);

        session_number++;
        //sleep_ms(500);
    }

    fclose(output_file);
    return 0;
}