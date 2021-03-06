package main

import "fmt"

func swap(a, b int) {
	a, b = b, a
}

func swapWithPointer(a, b *int) {
	*a, *b = *b, *a
}

func main() {
	x, y := 10, 12
	fmt.Printf("before \"swap(%d, %d)\": %d, %d \n", x, y, x, y)
	swap(x, y)
	fmt.Printf("after \"swap(%d, %d)\": %d, %d \n", x, y, x, y)

	fmt.Printf("before \"swapPointer(%d, %d)\": %d, %d \n", x, y, x, y)
	swapWithPointer(&x, &y)
	fmt.Printf("after \"swapPointer(%d, %d)\": %d, %d \n", x, y, x, y)

	var a int
	a = 10
	fmt.Printf("%d\n", a)

	// home address initial value is home
	b := new(int)
	*b = 10
	fmt.Printf("b = %p, *b = %d\n", b, *b)

	// initial value nil
	var c *int
	fmt.Printf("c = %v\n", c)

}
