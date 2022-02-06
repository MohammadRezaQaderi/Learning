package main

import "fmt"

func Fibonacci(n int) int {
	// use if
	if n == 0 || n == 1 {
		return 1
	}
	return Fibonacci(n-1) + Fibonacci(n-2)
}

func main() {
	const n = 10

	fmt.Printf("%d\n", Fibonacci(n))

	// use switch

	switch n {
	case 10:
		fmt.Printf("n is equal to 10\n")
		// if we want to run next case
		// fallthrough
	case 11:
		fmt.Printf("in c we have run this because last case is equal")
	default:
		fmt.Printf("this shouldn`t be happen")
	}
}
