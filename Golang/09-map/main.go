package main

import "fmt"

func main() {
	var m map[int]string
	m = make(map[int]string)

	m[1378] = "Muhmad"
	m[1373] = "Parham"

	for index, value := range m {
		fmt.Println(index, value)
	}

	var v string
	v = m[1378]
	fmt.Printf("m[%d] = %s \n", 1378, v)

	v = m[1400]
	fmt.Printf("m[%d] = %s \n", 1400, v)

	// make the set in go by map
	s := make(map[int]bool)

	for i := 0; i < 3; i++ {
		var n int
		fmt.Scanf("%d", &n)

		if s[n] {
			fmt.Printf("%d is already exist\n", n)
		} else {
			s[n] = true
			fmt.Printf("%d saved\n", n)
		}
	}

	opinions := make(map[string]bool)

	opinions["Muhmad"] = true
	opinions["Parham"] = false

	// ok say is exist or not
	if opinion, ok := opinions["Ali"]; ok {
		fmt.Printf("opinions[%s] = %v \n", "Ali", opinion)
	}
}
