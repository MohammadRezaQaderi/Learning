package main

import (
	"fmt"
	"github.com/Learning/Golang/booking-app/helper"
	"sync"
	"time"
)

const conferenceTickets int = 50

var conferenceName = "Go conference"
var RemainingTickets uint = 50
var bookings = make([]UserData, 0)

type UserData struct {
	firstName       string
	lastName        string
	email           string
	numberOfTickets uint
}

var wg = sync.WaitGroup{}

func main() {

	fmt.Printf("Welcome to %v booking aplication\n", conferenceName)
	fmt.Printf("We have total of %v tickets and %v are still available.\n", conferenceTickets, RemainingTickets)
	fmt.Println("Get your tickets here to attend")

	//for {
	firstName, lastName, email, userTickets := getUserInput()
	isValidName, isValidEmail, isValidTicketNumber := helper.ValidateUserInput(firstName, lastName, email, userTickets, RemainingTickets)
	if isValidName && isValidEmail && isValidTicketNumber {
		bookTicket(userTickets, firstName, lastName, email)
		// the num of thread we need to wait for it
		wg.Add(1)
		go sendTicket(userTickets, firstName, lastName, email)
		firstNames := getFirstName()
		fmt.Printf("These are all our booking: %v\n", firstNames)
		if RemainingTickets == 0 {
			fmt.Println("Our conference is booked out. Come back next year.")
			//break
		}
	} else {
		if !isValidName {
			fmt.Println("Your entered Name is very short")
		}
		if !isValidEmail {
			fmt.Println("your email address is not correct")
		}
		if !isValidTicketNumber {
			fmt.Printf("We have only %v tickets remaining, so you can't book %v tickets\n", RemainingTickets, userTickets)
		}
	}
	//}
	// after finish of the all work before exit the program we wait for the threads
	wg.Wait()
}

func getFirstName() []string {
	var firstNames []string
	for _, booking := range bookings {
		firstNames = append(firstNames, booking.firstName)
	}
	return firstNames
}

func getUserInput() (string, string, string, uint) {
	var firstName string
	var lastName string
	var email string
	var userTickets uint

	fmt.Println("Enter your first name: ")
	_, _ = fmt.Scan(&firstName)

	fmt.Println("Enter your last name: ")
	_, _ = fmt.Scan(&lastName)

	fmt.Println("Enter your email address: ")
	_, _ = fmt.Scan(&email)

	fmt.Println("Enter number of tickets: ")
	_, _ = fmt.Scan(&userTickets)

	return firstName, lastName, email, userTickets
}

func bookTicket(userTickets uint, firstName, lastName, email string) {
	RemainingTickets = RemainingTickets - userTickets
	var userData = UserData{
		firstName:       firstName,
		lastName:        lastName,
		email:           email,
		numberOfTickets: userTickets,
	}
	bookings = append(bookings, userData)

	fmt.Printf("Thank you %v %v for booking %v tickets. You will recive a cofirmation email at %v\n", firstName, lastName, userTickets, email)
	fmt.Printf("%v tickets remaining for %v\n", RemainingTickets, conferenceName)
}

func sendTicket(userTickets uint, firstName, lastName, email string) {
	time.Sleep(10 * time.Second)
	var ticket = fmt.Sprintf("%v tickets for %v %v", userTickets, firstName, lastName)
	fmt.Println("############")
	fmt.Printf("Sending ticket:\n %v\n to email address%v\n", ticket, email)
	fmt.Println("############")
	// after send the email we can say the threads work is finish
	wg.Done()
}
