package config

import (
	"fmt"
	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/mysql"
)

var db *gorm.DB

func Connect() {
	d, err := gorm.Open("mysql", "mgh:m2711gH9985/Go-DB?charset=utf8&parseTime=True&loc=Local")
	if err != nil {
		fmt.Println("the error for the db")
		panic(err)
	}
	db = d
}

func GetDB() *gorm.DB {
	return db
}
