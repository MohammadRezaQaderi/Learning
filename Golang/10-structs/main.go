package main

import "fmt"

type Student struct {
	Name   string
	Family string // if first letter is capital is public
	age    int    //else is private
}

// string returns the string for printed

func (s *Student) String() string {
	return fmt.Sprintf("Name: %s, Family: %s, age: %d \n", s.Name, s.Family, s.age)
}

// if we want change struct we usr the receiver

func (s *Student) IncreaseAge(inc int) {
	s.age += inc
}

func (s *Student) Hello(s1 Student) string {
	return fmt.Sprintf("Hello %s, I am %s %s", s.Name, s1.Name, s1.Family)
}
func main() {
	s := &Student{
		Name:   "Muhmad",
		Family: "Qaderi",
		age:    22,
	}

	fmt.Println(s)
	s.IncreaseAge(1)
	fmt.Println(s)
	fmt.Println(s.Hello(Student{
		Name:   "Ali",
		Family: "Abassi",
	}))
}
