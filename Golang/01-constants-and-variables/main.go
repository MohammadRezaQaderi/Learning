package main

import "fmt"

// these are global variables which are accessible from functions

const (
	c1       = 10.1
	c2 int64 = 11
)

var v1 = 10
var v2 uint64 = 10

func main() {
	x := 10 // it`s like this var x = 10

	// Or we can don`t have initial value
	var y int
	fmt.Println(c1)
	fmt.Println(c2)
	fmt.Printf("%d\n", y)
	fmt.Printf("%d %d\n", v1, v2)
	fmt.Println(x)
	//pointer
	var a int
	p := &a
	fmt.Println(p)
	*p = 10
	fmt.Println(a)

	// assignment
	j, k := 12, 15
	fmt.Println(j)
	fmt.Println(k)

}
