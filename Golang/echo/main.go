package main

import (
	"github.com/MohammadRezaQaderi/Learning/Golang/echo/handler"
	"github.com/labstack/echo/v4"
	"log"
)

func main() {
	e := echo.New()

	h := handler.Hello{
		From: "DORDOR",
	}

	e.GET("/hello", h.Get)

	e.POST("/hello", h.Post)

	e.GET("/hello/:username", h.User)

	if err := e.Start("127.0.0.1:1378"); err != nil {
		log.Fatal(err)
	}
}
