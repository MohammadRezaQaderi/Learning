//package store
//
//import (
//	"github.com/MohammadRezaQaderi/Learning/Golang/db/model"
//	"gorm.io/gorm"
//)
//
//type Student interface {
//	// save the model of the student
//	Save(model.Student) error
//	// get the id and return the student
//	Load(int) (model.Student, error)
//}
//
//type SQLStudent struct {
//	db *gorm.DB
//}
//
//func NewSQLStudent(db *gorm.DB) Student {
//	return &SQLStudent{
//		db: db,
//	}
//}
