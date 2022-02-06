package main

import "fmt"

func main() {
	var a [10]int
	var b = [...]int{1, 2, 3, 4}
	c := [4]int{2, 4, 6, 8}
	for index, value := range a {
		fmt.Printf("a[%d] = %d \n", index, value)
	}
	for index, value := range b {
		fmt.Printf("a[%d] = %d \n", index, value)
	}

	// a = c compile error the type is not ok (size is type)

	b = c // b here is copy of the c

	b[0] = 10 // here just b changed
}
