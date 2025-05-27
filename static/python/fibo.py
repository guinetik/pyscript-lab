from pyscript import display
# Fibonacci sequence
def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)
# Display the first 10 numbers in the Fibonacci sequence
fibo = [fibonacci(i) for i in range(10)]
display(fibo)