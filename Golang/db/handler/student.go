package handler

type Student struct {
	store
}
type request struct {
	FirstName string `json:"first_name"`
	LastName  string `json:"last_name"`
	ID        uint64 `json:"id"`
}

func NewStudent() {

}
