package main

import "fmt"

func main() {
	s1 := make([]int, 10)

	s1[0] = 1
	s1[1] = 2

	fmt.Printf("s1: %v\n", s1)

	// create new slice by operator
	// the new slice pointed to the prev slice
	s2 := s1[0:2]
	s2[0] = 10

	fmt.Printf("s2: %v\n", s2)
	fmt.Printf("s1 after change s2: %v\n", s1)

	// array
	a1 := [3]int{1, 2, 3}
	s3 := a1[1:3]
	s3[0] = 20

	fmt.Printf("s3: %v\n", s3)
	fmt.Printf("a1 after change s3: %v\n", a1)

	s4 := s3
	fmt.Printf("s4: %v\n", s4)

	// panic: runtime error: index out of range [3] with length 2
	//fmt.Printf("invalid access to slice %d", s4[3])

	// compile error because size of array is type of this
	//fmt.Printf("invalid access to array %d", a1[3])
}
