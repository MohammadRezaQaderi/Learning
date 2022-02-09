package main

import (
	"github.com/labstack/echo/v4"
	"log"
	"net/http"
)

func main() {
	e := echo.New()

	e.GET("/hello", func(c echo.Context) error {
		return c.JSON(http.StatusOK, "hello")
	})
	if err := e.Start("127.0.0.1:1378"); err != nil {
		log.Fatalf("cannot start the server %s", err)
	}
}
