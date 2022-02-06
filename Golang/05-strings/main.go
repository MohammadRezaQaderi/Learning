package main

import "fmt"

func main() {
	var s1 string = "The Good World"
	s2 := "MohammadReza Qaderi"
	s3 := "سلام دنیا"

	fmt.Printf("%d (len(s3)) !=10 \n", len(s3))

	fmt.Println([]byte(s3))
	fmt.Println(s1[0])
	fmt.Println(s2)
	fmt.Println(s3[1])

	fmt.Printf("%c \n", s3[1])

	// index , char
	for _, c := range s3 {
		fmt.Printf("%c", c)
	}

	fmt.Println()
}
