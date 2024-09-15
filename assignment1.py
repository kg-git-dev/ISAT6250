import statistics

def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n**0.5) + 1): 
        if n % i == 0:
            return False
    return True

def get_numbers():
    numbers_list = []
    prime_numbers_list = []
    
    while len(numbers_list) < 4:
        user_input = input("Input a number: ")
        try:
            number = float(user_input)
            numbers_list.append(number)
            if number.is_integer() and is_prime(int(number)):  
                prime_numbers_list.append(int(number))
        except ValueError:
            print("Not a number. Please try again!")
            
    return numbers_list, prime_numbers_list

def compute_median(numbers):
    median_value = statistics.median(numbers)
    print(f"Median is {median_value}")

def print_prime_numbers(primes):
    if primes:
        primes_str = ", ".join(map(str, primes))
        print(f"{primes_str} are prime numbers")
    else:
        print("There are no prime numbers in the list")

numbers_list, prime_numbers_list = get_numbers()
compute_median(numbers_list)
print_prime_numbers(prime_numbers_list)
