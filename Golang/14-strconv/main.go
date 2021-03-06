package main

import (
	"fmt"
	"strconv"
)

func main() {
	var s = "1234"
	a := 10

	// the second is error
	i, _ := strconv.ParseInt(s, 10, 64)

	// compile error: mismatched types int64 and int
	// a = i + a

	a = int(i) + a

	fmt.Println(i)
	fmt.Println(a)

	// print multiple return values with println
	fmt.Println(strconv.Atoi("123"))
}
