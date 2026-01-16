def sumof_no_and_reverse(m):
    reverse_m = str(m)[::-1]
    total = int(reverse_m) + m
    return total

def is_palindrome(k):
    reverse_k = str(k)[::-1]
    return str(k) == reverse_k


n = int(input("Enter a number: "))
p = sumof_no_and_reverse(n)
steps = 1
while not is_palindrome(p) and steps<50:
    p = sumof_no_and_reverse(p)
    steps += 1

if is_palindrome(p):
    print("We have found a palindrome", p)
else:
    print("Not a palindrome. Could be a lychrel number")










