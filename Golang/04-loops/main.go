package main

import "fmt"

func IsPrime(n int) bool {
	for i := 2; i < n; i++ {
		if n%i == 0 {
			return false
		}
	}

	return true
}

func NthPrime(n int) int {
	i := 2
	counter := 2
	// unbounded for
	for {
		if IsPrime(i) {
			counter++

			if counter == n {
				return i
			}
		}

		i++
	}
}
func GCD(n, m int) int {
	for n%m != 0 {
		n, m = m, n%m // multiple assignment
	}
	return m
}

func main() {
	var n int

	fmt.Printf("please enter the number: \n")
	//call by ref to edit n
	fmt.Scanf("%d", &n)

	fmt.Printf("is %d prime? %t \n", n, IsPrime(n))
	fmt.Printf("%d is  %d prime \n", n, NthPrime(n))

	fmt.Println("gcd", 10, 20, "is", GCD(10, 20))
	fmt.Println("gcd", 13, 15, "is", GCD(13, 15))
}
