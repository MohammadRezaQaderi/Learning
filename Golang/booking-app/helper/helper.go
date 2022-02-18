package helper

import (
	"strings"
)

func ValidateUserInput(firstName, lastName, email string, userTickets, RemainingTickets uint) (bool, bool, bool) {
	isValidName := len(firstName) >= 2 && len(lastName) >= 2
	isValidEmail := strings.Contains(email, "@")
	isValidTicketNumber := userTickets > 0 && userTickets <= RemainingTickets
	return isValidName, isValidEmail, isValidTicketNumber
}
