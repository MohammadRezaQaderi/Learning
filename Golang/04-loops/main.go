package main

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
		n, m = m, n%m
	}
	return m
}
